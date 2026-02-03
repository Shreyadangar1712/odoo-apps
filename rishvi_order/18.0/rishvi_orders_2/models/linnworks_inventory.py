from odoo import models, fields, api, _
from odoo.exceptions import UserError
import requests
import logging
from datetime import datetime

_logger = logging.getLogger(__name__)


class LinnworksAppDetails(models.Model):
    _inherit = 'linn.app.detail'

    def parse_linnworks_datetime(self, date_str):
        if not date_str:
            return False
        try:
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%fZ")
            except ValueError:
                dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
            return dt
        except Exception as e:
            _logger.warning("Failed to parse date %s: %s", date_str, e)
            return False

    def import_orders(self):
        self.ensure_one()
        token = self._get_auth_token()
        if not token:
            raise UserError(_("Failed to authenticate with Linnworks API"))

        url = "https://eu-ext.linnworks.net/api/Orders/GetOpenOrders"
        headers = {
            "Authorization": self.auth_token,
            "accept": "application/jsonrpc",
            "content-type": "application/jsonrpc",
        }
        payload = {
            "entriesPerPage": 2147483647,
            "pageNumber": 1,
            "filters": None,
            "sorting": None,
            "fulfilmentCenter": "",
            "additionalFilter": ""
        }

        response = requests.post(url, json=payload, headers=headers)
        if response.status_code != 200:
            raise UserError(_("Failed to fetch orders from Linnworks: %s") % response.text)

        data = response.json()
        _logger.info("Linnworks response keys: %s", data.keys() if isinstance(data, dict) else "Not a dict")

        if isinstance(data, dict):
            orders = data.get('Data') or data.get('Orders') or []
            if not orders and 'OrderId' in data:
                orders = [data]
        elif isinstance(data, list):
            orders = data
        else:
            raise UserError(_("Unexpected Linnworks API response format."))

        _logger.info("Importing %d orders from Linnworks", len(orders))

        sale_order_obj = self.env['sale.order']
        product_obj = self.env['product.product']

        for order_data in orders:

            linnworks_order_id = order_data.get('OrderId')
            linn_order_number = order_data.get('NumOrderId')

            if not linnworks_order_id:
                _logger.warning("Skipping order with missing OrderId: %s", order_data)
                continue

            partner_vals = order_data.get('CustomerInfo', {}).get('Address', {})
            partner = self._get_or_create_partner(partner_vals)

            currency_code = order_data.get('TotalsInfo', {}).get('Currency', '').upper()
            Currency = self.env['res.currency']
            Pricelist = self.env['product.pricelist']

            currency = Currency.search([('name', '=', currency_code)], limit=1)
            if not currency:
                _logger.warning("Currency %s not found in Odoo. Falling back to company currency.", currency_code)
                currency = self.env.company.currency_id

            pricelist = Pricelist.search([('currency_id', '=', currency.id)], limit=1)
            if not pricelist:
                pricelist_vals = {
                    'name': f"{currency.name} Pricelist (Auto)",
                    'currency_id': currency.id,
                    'item_ids': [],
                }
                pricelist = Pricelist.create(pricelist_vals)
                _logger.info("Created new pricelist %s for currency %s", pricelist.name, currency.name)

            existing_order = sale_order_obj.search([('linnworks_order_id', '=', linnworks_order_id)], limit=1)

            order_line_vals_list = []
            total_amount = 0.0
            total_tax = 0.0

            # Process items first
            for item in order_data.get('Items', []):
                sku = item.get('SKU') or item.get('ChannelSKU')
                title = item.get('Title') or item.get('ChannelTitle')
                quantity = item.get('Quantity', 1)

                product = product_obj.search([('default_code', '=', sku)], limit=1)
                if not product and title:
                    product = product_obj.search([('name', '=', title)], limit=1)

                if not product:
                    _logger.warning(f"Product with SKU {sku} and title {title} not found, creating new product")
                    product_vals = {
                        'name': title or f"Unknown Product ({sku})",
                        'default_code': sku,
                        'type': 'consu',
                        'list_price': item.get('PricePerUnit', 0.0),
                        'linnworks_item_id': item.get('ItemId')
                    }
                    product = product_obj.create(product_vals)
                    _logger.info(f"Created new product {product.name} with SKU {sku}")

                line_total = item.get('PricePerUnit', 0.0) * quantity
                line_tax = item.get('Tax', 0.0)
                unit_price = item.get('Cost', 0.0)
                tax_rate = item.get('TaxRate', 0.0)
                tax = self._get_tax_by_rate(tax_rate)

                order_line_vals_list.append({
                    'product_id': product.id,
                    'name': product.name,
                    'product_uom_qty': quantity,
                    'price_unit': unit_price,
                    'tax_ids': [(6, 0, [tax.id])] if tax else [],
                })

                total_amount += line_total
                total_tax += line_tax
                _logger.debug(f"Added line for product {product.name} (SKU: {sku})")

            # Process shipping cost separately (after items)
            postage_cost = order_data.get('ShippingInfo', {}).get('PostageCost', 0.0)
            postage_cost_ex_tax = order_data.get('ShippingInfo', {}).get('PostageCostExTax', 0.0)

            if postage_cost > 0:
                # Calculate tax rate for postage
                if postage_cost_ex_tax > 0:
                    postage_tax = postage_cost - postage_cost_ex_tax
                    postage_tax_rate = (postage_tax / postage_cost_ex_tax * 100) if postage_cost_ex_tax else 0.0
                else:
                    postage_tax_rate = 0.0

                # Find or create a shipping product
                shipping_product = product_obj.search([('default_code', '=', 'LWSHIPPING')], limit=1)
                if not shipping_product:
                    shipping_product = product_obj.create({
                        'name': 'Shipping Fee (Linnworks)',
                        'default_code': 'LWSHIPPING',
                        'type': 'service',
                        'list_price': postage_cost,
                    })
                    _logger.info("Created shipping product for Linnworks")

                tax = self._get_tax_by_rate(postage_tax_rate)

                order_line_vals_list.append({
                    'product_id': shipping_product.id,
                    'name': shipping_product.name,
                    'product_uom_qty': 1,
                    'price_unit': postage_cost_ex_tax if postage_cost_ex_tax > 0 else postage_cost,
                    'tax_ids': [(6, 0, [tax.id])] if tax else [],
                })

                total_amount += postage_cost_ex_tax if postage_cost_ex_tax > 0 else postage_cost
                total_tax += postage_cost - postage_cost_ex_tax if postage_cost_ex_tax > 0 else 0.0

            if not order_line_vals_list:
                _logger.warning("Order %s has no valid products, skipping", linnworks_order_id)
                continue

            totals_info = order_data.get('TotalsInfo', {})
            subtotal = totals_info.get('Subtotal', total_amount)
            tax = totals_info.get('Tax', total_tax)
            total_charge = totals_info.get('TotalCharge', subtotal + tax)

            other_charges = round(total_charge - (subtotal + tax), 2)
            if other_charges < 0:
                _logger.warning("Negative other charges for order %s: %s", linnworks_order_id, other_charges)
                other_charges = 0.0

            total_amount = subtotal
            total_tax = tax
            total_amount_inc_tax = total_charge

            if existing_order:
                existing_order.order_line.unlink()
                existing_order.write({
                    'order_line': [(0, 0, vals) for vals in order_line_vals_list],
                    'partner_id': partner.id,
                    'date_order': self.parse_linnworks_datetime(order_data.get('GeneralInfo', {}).get('ReceivedDate')),
                    'client_order_ref': order_data.get('GeneralInfo', {}).get('ReferenceNum'),
                    'linn_order_number': linn_order_number,
                    'pricelist_id': pricelist.id,
                    'currency_id': currency.id,
                    'amount_untaxed': total_amount,
                    'amount_tax': total_tax,
                    'amount_total': total_amount_inc_tax,
                    'linnworks_other_charges': other_charges,
                    'linnworks_sync': True,
                })
                _logger.info("Updated sale order %s for Linnworks order %s", existing_order.name, linnworks_order_id)
            else:
                order_vals = {
                    'partner_id': partner.id,
                    'linnworks_order_id': linnworks_order_id,
                    'linn_order_number': linn_order_number,
                    'date_order': self.parse_linnworks_datetime(order_data.get('GeneralInfo', {}).get('ReceivedDate')),
                    'client_order_ref': order_data.get('GeneralInfo', {}).get('ReferenceNum'),
                    'order_line': [(0, 0, vals) for vals in order_line_vals_list],
                    'pricelist_id': pricelist.id,
                    'currency_id': currency.id,
                    'amount_untaxed': total_amount,
                    'amount_tax': total_tax,
                    'amount_total': total_amount_inc_tax,
                    'linnworks_other_charges': other_charges,
                    'linnworks_sync': True,
                }
                sale_order = sale_order_obj.create(order_vals)
                _logger.info("Created sale order %s for Linnworks order %s", sale_order.name)
                _logger.info("Created  %s for Linnworks numbers %s", sale_order.linn_order_number)

    def _get_or_create_partner(self, partner_data):
        Partner = self.env['res.partner']

        name = partner_data.get('FullName')
        phone = partner_data.get('PhoneNumber')

        address_parts = [
            partner_data.get('Address1'),
            partner_data.get('Address2'),
            partner_data.get('Town'),
            partner_data.get('Region'),
            partner_data.get('PostCode'),
            partner_data.get('Country')
        ]

        # Filter out empty parts and join with commas
        full_address = ', '.join(part for part in address_parts if part)

        email = partner_data.get('EmailAddress')

        # Prepare values
        vals = {
            'name': name or 'Unknown',
            'email': email,
            'phone': phone,
            'street': partner_data.get('Address1'),
            'street2': partner_data.get('Address2'),
            'city': partner_data.get('Town', ''),
            'zip': partner_data.get('PostCode', ''),
            'state_id': self.env['res.country.state'].search(
                [('name', '=', partner_data.get('Region', ''))],
                limit=1
            ).id,
            'country_id': self.env['res.country'].search(
                [('name', '=', partner_data.get('Country', ''))],
                limit=1
            ).id,
            'linnworks_customer_uid': email,
        }

        # Search for existing partner by each field
        # Case 1: Y Y Y Y → Existing user → No child
        case1_partner = Partner.search([
            ('name', '=', name),
            ('phone', '=', phone),
            ('street', '=', partner_data.get('Address1')),
            ('street', '=', partner_data.get('Address2')),
            ('email', '=', email)
        ], limit=1)

        # Case 2: N Y Y N → Existing → Make Child with new val
        case2_partner = Partner.search([
            ('phone', '=', phone),
            ('street', '=', partner_data.get('Address1')),
            ('street', '=', partner_data.get('Address2'))
        ], limit=1)

        # Case 3: N N N Y → Existing → Make Child with new val
        case3_partner = Partner.search([
            ('email', '=', email)
        ], limit=1)

        # Case 5: N N N N → New → New Contact
        # NOT OF Case 1: N N N N → New → New Contact

        _logger.info("11111111111111111111111111111111111111111111134567")
        _logger.info(case1_partner)
        _logger.info(case2_partner)
        _logger.info(case3_partner)
        if case1_partner:
            return case1_partner
        elif case2_partner:
            return Partner.create({**vals, 'parent_id': case2_partner.id})
        elif case3_partner:
            return Partner.create({**vals, 'parent_id': case3_partner.id})
        else:
            return Partner.create(vals)

    def _get_tax_by_rate(self, tax_rate, currency_code='GBP'):
        account_tax_obj = self.env['account.tax']
        tax_rate = float(tax_rate)

        # Search for a tax with the same rate and type sale
        tax = account_tax_obj.search([
            ('amount', '=', tax_rate),
            ('type_tax_use', '=', 'sale'),
            ('name', 'ilike', f'{tax_rate}%')
        ], limit=1)

        if not tax:
            # Create a new tax if not found
            tax_vals = {
                'name': f'{tax_rate}% Tax (Auto)',
                'amount': tax_rate,
                'type_tax_use': 'sale',
                'amount_type': 'percent',
                'price_include': False,  # adjust if tax included in price
            }
            tax = account_tax_obj.create(tax_vals)
            _logger.info("Created new tax %s for rate %s%%", tax.name, tax_rate)
        return tax


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    linnworks_order_id = fields.Char('Linnworks Order ID', copy=False, index=True)
    linn_order_number = fields.Char('Linnworks Order Number', copy=False, index=True)
    linnworks_other_charges = fields.Monetary('Linnworks Other Charges', currency_field='currency_id',
                                              help="Difference between expected and actual total from Linnworks.")


class ResPartner(models.Model):
    _inherit = 'res.partner'

    linnworks_customer_uid = fields.Char("Linnworks Customer ID", copy=False, index=True)