# -*- coding: utf-8 -*-
import logging
import odoo
import time
from odoo import http, _
from odoo.http import request
from odoo.tools import float_round
from odoo import models, api, exceptions, fields

import requests

_logger = logging.getLogger(__name__)


class LinnOrderImportController(http.Controller):


    

    @http.route('/order/status_counts', type='jsonrpc', auth='user', methods=['GET', 'POST'])
    def get_order_number_counts(self):
        """
        Fetch order status counts from external AWS Lambda API
        and return data as JSON.
        """
        try:
            icp = request.env["ir.config_parameter"].sudo()
            lw_token = icp.get_param("lw_token")
            rishvi_base_api_url = icp.get_param("rishvi_base_api_url")
            rishvi_app = icp.get_param("rishvi_app")
            params = {"appName": rishvi_app, "appToken": lw_token}
            headers = {"accept": "*/*"}
            url = f"{rishvi_base_api_url}/Order/order-status-counts"

            
            response = requests.get(url, params=params, headers=headers, timeout=15)

            response.raise_for_status()
            datas = response.json()
            total_order_count = 0
            for data in datas:
                total_order_count = total_order_count + data['count']

            return {
                "success": True,
                "data": total_order_count
            }
        except requests.exceptions.RequestException as e:
            _logger.error("Error fetching order status counts: %s", e)
            return {
                "success": False,
                "error": str(e)
            }

    @http.route('/linnworks/Order/get-countries', type='jsonrpc', auth='user', csrf=False)
    def fetch_countries(self, **kwargs):
        """
        Fetch countries data from external API and store it in 'linn.country' model.
        Also create/update corresponding taxes in 'account.tax' model.
        """
        _logger.info("Inside Import Countries")

        try:
            # Step 1: Get config from system parameters
            ir_config = request.env["ir.config_parameter"].sudo()
            lw_token = ir_config.get_param("lw_token")
            rishvi_base_api_url = ir_config.get_param("rishvi_base_api_url")
            rishvi_app = ir_config.get_param("rishvi_app")

            if not lw_token or not rishvi_base_api_url:
                return {"success": False, "message": "Token or Base URL not configured in System Parameters."}

            # Step 2: Build full URL
            url = f"{rishvi_base_api_url}/Order/get-countries"

            # Step 3: Headers & params
            headers = {"accept": "*/*"}
            params = {
                "appName": rishvi_app,
                "appToken": lw_token
            }

            # Step 4: Make GET request to external API
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            countries_data = response.json()

            # Step 5: Store countries and taxes
            for item in countries_data:
                country_code = item.get('countryCode')
                tax_rate = item.get('taxRate')
                country_name = item.get('countryName')

                #  Update or create in linn.country
                existing_country = request.env['linn.country'].sudo().search([
                    ('country_code', '=', country_code)
                ], limit=1)

                vals = {
                    'country_ids': item.get('countryId'),
                    'country_name': country_name,
                    'country_code': country_code,
                    'continent': item.get('continent'),
                    'currency_ids': item.get('currency'),
                    'customs_required': item.get('customsRequired'),
                    'tax_rate': tax_rate,
                    'address_format': item.get('addressFormat'),
                    'regions_count': item.get('regionsCount'),
                }

                if existing_country:
                    existing_country.write(vals)
                else:
                    request.env['linn.country'].sudo().create(vals)

                #  Also create/update tax in account.tax
                if tax_rate:
                    tax_name = f"{tax_rate}%"
                    Tax = request.env['account.tax'].sudo()

                    # Step 1: Try to find a tax with this amount or name
                    existing_tax = Tax.search([
                        '|',
                        ('name', '=', tax_name),
                        ('amount', '=', float(tax_rate))
                    ], limit=1)

                    tax_vals = {
                        'name': tax_name,
                        'amount': float(tax_rate),
                        'amount_type': 'percent',
                    }

                    # Step 2: Update if exists, else create
                    if existing_tax:
                        existing_tax.write(tax_vals)
                    else:
                        existing_tax = Tax.create(tax_vals)

                    # Step 3: Link country only if not already linked
                    if existing_country.id not in existing_tax.same_tax_country_ids.ids:
                        existing_tax.write({
                            'same_tax_country_ids': [(4, existing_country.id)]
                        })

            return {"success": True, "message": "Countries  imported successfully!"}

        except Exception as e:
            _logger.error("Error fetching countries: %s", str(e))
            return {"success": False, "message": str(e)}

    @http.route('/my/api/order/sync_orders_by_page', type='jsonrpc', auth='user', methods=['GET', 'POST'])
    def sync_all_the_order(self, **kwargs):
        """
        Fetch order:
          - Rishvi orders → counted directly from Odoo sale orders
          - Linnworks orders → fetched from external AWS Lambda API
        """
        try:
            page_number = kwargs.get('page_number', 1)
            start_time = time.time()

            # Automation toggles (stored as strings "true"/"false")
            ir_config = request.env['ir.config_parameter'].sudo()
            auto_post_invoice = ir_config.get_param("auto_post_invoice", "false").lower() == "true"
            auto_validate_delivery = ir_config.get_param("auto_validate_delivery", "false").lower() == "true"
            auto_cancel_orders = ir_config.get_param("auto_cancel_orders", "false").lower() == "true"

            

            
            icp = request.env["ir.config_parameter"].sudo()
            lw_token = icp.get_param("lw_token")
            rishvi_base_api_url = icp.get_param("rishvi_base_api_url")
            rishvi_app = icp.get_param("rishvi_app")
            params = {"appName": rishvi_app, "appToken": lw_token, "page": page_number, "limit": 30}
            headers = {"accept": "*/*"}
            url= f"{rishvi_base_api_url}/Order/orders"


            if not all([lw_token, rishvi_base_api_url, rishvi_app]):
                return {'status': 'error', 'message': 'System parameters missing'}
            response = requests.get(url, params=params, headers=headers, timeout=15)

            response.raise_for_status()
            data = response.json()

            orders = []
            if isinstance(data, dict):
                orders = data.get('orders') or data.get('data') or []
            elif isinstance(data, list):
                orders = data

            created_count = updated_count = error_count = invoiced_count = delivered_count = cancelled_count = 0

            for idx, order_data in enumerate(orders, start=1):
                try:
                    with request.env.cr.savepoint():
                        result = self._process_order_with_workflow(
                            order_data,
                            auto_post_invoice,
                            auto_validate_delivery,
                            auto_cancel_orders
                        )
                        

                        if result.get('action') == 'created':
                            created_count += 1
                        elif result.get('action') == 'updated':
                            updated_count += 1

                        if result.get('invoiced'):
                            invoiced_count += 1
                        if result.get('delivered'):
                            delivered_count += 1
                        if result.get('cancelled'):
                            cancelled_count += 1

                        _logger.info(
                            f"✅ [{idx}] {result.get('action', '').upper()} - Invoice:{result.get('invoiced')}, Delivery:{result.get('delivered')}, Cancelled:{result.get('cancelled')}"
                        )

                except Exception as e:
                    error_count += 1
                    _logger.exception(f"❌ [{idx}] Error processing order")
                    continue
            requests.get("https://httpbin.org/delay/2", timeout=15)
            total_time = round(time.time() - start_time, 2)
            _logger.info(f"✅ PAGE {page_number} COMPLETE")
            _logger.info(f"📊 Created:{created_count}, Updated:{updated_count}, Errors:{error_count}")
            _logger.info(f"📊 Invoiced:{invoiced_count}, Delivered:{delivered_count}, Cancelled:{cancelled_count}")

            return {
                'status': 'ok',
                'created': created_count,
                'updated': updated_count,
                'errors': error_count,
                'invoiced': invoiced_count,
                'delivered': delivered_count,
                'cancelled': cancelled_count,
                'total_processed': len(orders),
                'time': total_time
            }

        except Exception as e:
            _logger.exception(f"❌ Fatal error syncing page {page_number}")
            return {'status': 'error', 'message': str(e)}

    # ============================================
    # HELPER: Process Order with Workflow
    # ============================================
    def _process_order_with_workflow(self, order_data, auto_post_invoice,
                                     auto_validate_delivery, auto_cancel_orders):
        """
        Workflow:
        1) If holdOrCancel and auto_cancel_orders -> cancel order
        2) Create/Update sale.order with lines
        3) Confirm order (action_confirm)
        4) If status == 1 and auto_post_invoice -> create & post invoice
        5) If partShipped == True and auto_validate_delivery -> validate pickings
        """
        linnworks_order_id = order_data.get('orderId')
        if not linnworks_order_id:
            return {'action': 'skipped', 'reason': 'No order ID'}
    

        items = order_data.get('orderItems', []) or []
        source_name = order_data.get("generalInfo", {}).get("source")
        if source_name == "RISHVI_POS":
            return {'action': 'error', 'reason': 'failed_to_create_order'}

        # Workflow flags
        lw_status = order_data.get("paymentStatus")

        part_shipped = order_data.get('partShipped', False)
        hold_or_cancel = order_data.get('holdOrCancel', False)

        # ===== PARTNER =====
        addr = order_data.get('deliveryAddress', {}) or {}
        billing_address = order_data.get('billingAddress', {}) or {}

        partner = None
        try:
            Partner = request.env['res.partner'].sudo()
            country = request.env['res.country'].sudo().search(
                [('name', 'ilike', addr.get("country") or "United Kingdom")], limit=1)
            if not country:
                country = request.env['res.country'].sudo().search([('code', '=', 'GB')], limit=1)
            Partner = request.env['res.partner'].sudo()

            partner_vals = {
                'name': addr.get("fullName") or "Guest",
                'email': addr.get("emailAddress") if addr.get("emailAddress") != "False" else False,
                'phone': addr.get("phoneNumber") or False,
                'street': addr.get("address1") or "",
                'street2': addr.get("address2") or "",
                'city': addr.get("town") or "",
                'zip': addr.get("postCode") or "",
                'country_id': country.id if country else False,
                'company_name': addr.get("company") or "",
            }
            
            billing_vals = {
                'name': billing_address.get("fullName") or "Guest",
                'email': billing_address.get("emailAddress") if billing_address.get(
                    "emailAddress") != "False" else False,
                'phone': billing_address.get("phoneNumber") or False,
                'street': billing_address.get("address1") or "",
                'street2': billing_address.get("address2") or "",
                'city': billing_address.get("town") or "",
                'zip': billing_address.get("postCode") or "",
                'country_id': country.id if country else False,
            }
            
            billing_partner=None
            partner=None
            if billing_address.get("fullName") == False or billing_address.get("fullName") == "":
                billing_partner = request.env['res.partner'].search([('name', '=', 'Guest'),], limit=1)
            else:
                billing_partner = request.env['res.partner'].search([('name', '=', billing_vals.get('name')),('email', '=', billing_vals.get('email')),('phone', '=', billing_vals.get('phone')),], limit=1)
            if addr.get("fullName") == False or addr.get("fullName") == "":
                partner = request.env['res.partner'].search([('name', '=', 'Guest'),], limit=1)
            else:
                partner = Partner.search([('name', '=', partner_vals.get("name")),('phone', '=', partner_vals.get("phone")),('email', '=', partner_vals.get("email"))], limit=1)
            
            if not partner:
                # Search for existing partner by each field
                # Case 1: Y Y Y Y → Existing user → No child
                case1_partner = Partner.search([
                    ('name', '=', addr.get("fullName")),
                    ('phone', '=', addr.get("phoneNumber")),
                    ('street', '=', addr.get("address1")),
                    ('email', '=', addr.get("emailAddress"))
                ], limit=1)
            
                # Case 2: N Y Y N → Existing → Make Child with new val
                case2_partner = Partner.search([
                    ('phone', '=', addr.get("phoneNumber")),
                    ('street', '=', addr.get("address1"))
                ], limit=1)
            
                # Case 3: N N N Y → Existing → Make Child with new val
                case3_partner = Partner.search([
                    ('email', '=', addr.get("emailAddress"))
                ], limit=1)
            
                # Case 5: N N N N → New → New Contact
                # NOT OF Case 1: N N N N → New → New Contact
            
                if case1_partner:
                    partner = case1_partner
                elif case2_partner:
                    partner = Partner.create({**partner_vals, 'parent_id': case2_partner.id})
                elif case3_partner:
                    partner = Partner.create({**partner_vals, 'parent_id': case3_partner.id})
                else:
                    partner = Partner.create(partner_vals)
            if not billing_partner:
                # Search for existing partner by each field
                # Case 1: Y Y Y Y → Existing user → No child
                case1_partner = Partner.search([
                    ('name', '=', billing_address.get("fullName")),
                    ('phone', '=', billing_address.get("phoneNumber")),
                    ('street', '=', billing_address.get("address1")),
                    ('email', '=', billing_address.get("emailAddress"))
                ], limit=1)
            
                # Case 2: N Y Y N → Existing → Make Child with new val
                case2_partner = Partner.search([
                    ('phone', '=', billing_address.get("phoneNumber")),
                    ('street', '=', billing_address.get("address1")),
                ], limit=1)
            
                # Case 3: N N N Y → Existing → Make Child with new val
                case3_partner = Partner.search([
                    ('email', '=', billing_address.get("emailAddress"))
                ], limit=1)
            
                # Case 5: N N N N → New → New Contact
                # NOT OF Case 1: N N N N → New → New Contact
                if case1_partner:
                    billing_partner = case1_partner
                elif case2_partner:
                    billing_partner = Partner.create({**billing_vals, 'parent_id': case2_partner.id})
                elif case3_partner:
                    billing_partner = Partner.create({**billing_vals, 'parent_id': case3_partner.id})
                else:
                    billing_vals['parent_id'] = partner.id
                    billing_partner = Partner.create(billing_vals)
                



        except Exception as e:
            _logger.exception("❌ Partner creation/search failed")
            # continue but partner might be None, which will fail later

        # {'orderId': '2fcfb580-b2ee-40ea-90a5-9fa1152bff43', 'source': 'DIRECT', 'subSource': '', 'referenceNumber': 'DRAFT', 'postalServiceId': '00000000-0000-0000-0000-000000000000', 'postalServiceName': 'Default', 'savePostalServiceIfNotExist': False, 'receivedDate': '2025-10-14T17:54:46.99Z', 'dispatchBy': '2025-10-14T17:54:46.99Z', 'currency': 'GBP', 'paymentStatus': 'UNPAID', 'channelBuyerName': '', 'postalServiceCost': 0, 'postalServiceTaxRate': 0, 'useChannelTax': False, 'postageCost': 0, 'status': 0, 'holdOrCancel': False, 'isParked': False, 'partShipped': False, 'billingAddress': {'fullName': 'justin crm inv', 'address1': 'billing add Flat 1Singh mount', 'address2': '', 'address3': '', 'town': 'Reedshire', 'region': '', 'postCode': 'BB97 1TT', 'country': 'United Kingdom', 'emailAddress': '', 'company': '', 'phoneNumber': ''}, 'deliveryAddress': {'fullName': 'Justin Smith', 'address1': 'Flat 1\nSingh mount', 'address2': '', 'address3': '', 'town': 'Reedshire', 'region': '', 'postCode': 'BB97 1TT', 'country': 'UNKNOWN', 'emailAddress': 'dianekaur@example.org', 'company': '', 'phoneNumber': '(0191)4960744'}, 'orderItems': [{'sku': 'MC-GEN-LG-WHT-97', 'itemNumber': 'MC-GEN-LG-WHT-97', 'itemTitle': '', 'pricePerUnit': 0, 'qty': 1, 'taxRate': 15, 'taxCostInclusive': False, 'discount': 0}], 'notes': []}

        # ===== CURRENCY & PRICELIST =====
        currency_code = (order_data.get('currency') or 'GBP').strip()
        currency = request.env['res.currency'].sudo().search([('name', '=', currency_code)], limit=1)
        if not currency:
            currency = request.env.company.currency_id

        pricelist = request.env['product.pricelist'].sudo().search([('currency_id', '=', currency.id)], limit=1)
        if not pricelist:
            pricelist = request.env['product.pricelist'].sudo().create({
                'name': f"{currency.name} Pricelist",
                'currency_id': currency.id,
            })

       
 

        # ===== ORDER LINES =====
        order_line_vals = []
        for item in items:
            item_id = item.get("itemId")
            sku = item.get('sku')
            if not sku:
                # skip items without SKU
                continue


            productCategory = request.env['product.category']

            category_name = item.get("categoryName")

            if category_name:
                    category = productCategory.search([
                        ('name', '=', category_name)
                    ], limit=1)

                    if not category:
                        category = productCategory.create({
                            'name': category_name
                        })
            else:
                    category = productCategory.search([('name', '=', 'Default')], limit=1)
                    if not category:
                        category = productCategory.create({'name': 'Default'})


            product = request.env['product.product'].sudo().search([('default_code', '=', sku)], limit=1)
            if not product:
                product = request.env['product.product'].sudo().create({
                    'name': item.get('itemTitle', sku) or sku,
                    'default_code': sku,
                    'type': 'consu',
                    'is_storable': True,
                    'available_in_pos': True,
                    'list_price': item.get('pricePerUnit', 0.0),
                    'linnworks_item_id': item_id,
                    'categ_id': category.id
                })
                _logger.info(f"🆕 Created product for SKU {sku} -> {product.name} ({product.id})")

            qty = item.get('quantity', 1) or 1
            price_unit = item.get('pricePerUnit', 0.0) or 0.0

            tax_obj = request.env['account.tax']

            # Look for an existing tax with 15% rate
            tax = tax_obj.search([('amount', '=', item.get("taxRate"))], limit=1)

            if not tax:
                # Create tax if not found
                tax = tax_obj.create({
                    'name': f'{float(item.get("taxRate"))}%',
                    'amount': float(item.get("taxRate")),
                    'amount_type': 'percent',
                    'type_tax_use': 'sale',  # or 'purchase' or 'both'
                })

            order_line_vals.append({
                'product_id': product.id,
                'name': product.name,
                'product_uom_qty': qty,
                'price_unit': price_unit,
                'discount': float(item.get("discount")) or 0.0,
                'tax_ids': [(6, 0, tax.ids)]  # Add taxes here
            })

        if not order_line_vals:
            # No lines — skip creating order
            _logger.info("ℹ️ Order skipped: no order lines")
            return {'action': 'skipped', 'reason': 'No order lines'}

        # ===== CREATE / UPDATE SALE.ORDER =====
        existing_order = request.env['sale.order'].sudo().search([
            ('linnworks_order_id', '=', str(linnworks_order_id))
        ], limit=1)
        if existing_order:
            status = lw_status
            sale_order = existing_order
            invoice_posted = False
            if status == "PAID" or status == 1: # Post invoice for PAID orders
                for invoice in sale_order.invoice_ids.filtered(lambda inv: inv.state == 'draft'):
                    try:
                        _logger.info("Attempting to auto-post PAID order invoice: %s", invoice.name)

                        if not invoice.invoice_line_ids:
                            _logger.info(" Invoice has no lines, keeping as draft: %s", invoice.name)  # Changed to info
                            continue

                        if not invoice.invoice_date_due:
                            invoice.invoice_date_due = fields.Date.today()

                        invoice.action_post()
                        invoice_posted = True
                        _logger.info(" Invoice auto-posted successfully for PAID order: %s", invoice.name)

                    except Exception as invoice_error:
                        _logger.warning("Could not auto-post invoice %s (keeping as draft): %s", invoice.name,
                                        invoice_error)  # Changed to warning

            delivery_validated = False
            if part_shipped:
                for picking in sale_order.picking_ids:
                    if picking.state == 'assigned':
                        try:
                            _logger.info("Attempting to auto-validate delivery: %s", picking.name)
                            picking.button_validate()
                            delivery_validated = True
                            _logger.info("Delivery auto-validated successfully: %s", picking.name)
                        except Exception as delivery_error:
                            _logger.warning("Could not auto-validate delivery %s: %s", picking.name,
                                            delivery_error)  # Changed to warning
            else:
                _logger.info(" Delivery kept as assigned - partShipped is False")
            action = 'updated'
        else:
            _logger.info("🆕 Creating new order in Odoo")

            notes_list = order_data.get('notes') or []
            first_note = notes_list[0].get('note') if len(notes_list) > 0 else ""
        
            order_vals = {
                'partner_id': partner.id if partner else False,
                'partner_invoice_id': billing_partner.id,
                'partner_shipping_id': partner.id,
                'linnworks_order_id': str(linnworks_order_id),
                'linn_order_number': order_data.get('numOrderId') or False,
                'order_line': [(0, 0, vals) for vals in order_line_vals],
                'pricelist_id': pricelist.id,
                'linnworks_sync': True,
                'notes': first_note,

                'currency_id': currency.id}
            try:
                order = request.env['sale.order'].sudo().create(order_vals)
                svc = request.env['sale.shipping.services'].sudo().search(
                    [('service_id', '=', order_data.get('postalServiceId'))], limit=1)
                if not svc:
                    svc = request.env['sale.shipping.services'].sudo().create({
                        'postal_service_name': item.get('postalServiceName') or "Unnamed Service",
                        'service_id': item.get('serviceId') or 0,
                        'vendor_id': False,
                        'amount': item.get('postalServiceCost'),
                        'active': True
                    })
                order.shipping_service_id = svc.id

                # Mapping Other Details:
                source = request.env['source.details'].sudo().search([('name', '=', order_data.get('source'))], limit=1)
                if not source:
                    source = request.env['source.details'].sudo().create({
                        'name': order_data.get('source')})
                order.linn_order_source = source.id

                sub_source = request.env['sub.source.details'].sudo().search(
                    [('name', '=', order_data.get('subSource'))], limit=1)
                if not sub_source:
                    sub_source = request.env['sub.source.details'].sudo().create({
                        'name': order_data.get('subSource')})
                order.linn_order_sub_source = sub_source.id

              

                order.action_confirm()
                status = lw_status
                sale_order = order

                # --- Post Invoice if status == 1 (PAID) ---
                invoice = sale_order._create_invoices()
                invoice_posted = False
                _logger.info(f'{status}')

                if status == "PAID" or status == 1:  # Post invoice for PAID orders

                    for invoice in sale_order.invoice_ids.filtered(lambda inv: inv.state == 'draft'):
                        try:
                            _logger.info("Attempting to auto-post PAID order invoice: %s", invoice.name)

                            if not invoice.invoice_line_ids:
                                _logger.info(" Invoice has no lines, keeping as draft: %s",
                                             invoice.name)  # Changed to info
                                continue

                            if not invoice.invoice_date_due:
                                invoice.invoice_date_due = fields.Date.today()

                            invoice.action_post()
                            invoice_posted = True
                            _logger.info(" Invoice auto-posted successfully for PAID order: %s", invoice.name)

                        except Exception as invoice_error:
                            _logger.warning("Could not auto-post invoice %s (keeping as draft): %s", invoice.name,
                                            invoice_error)  # Changed to warning

                # --- Validate delivery if partShipped is True ---
                delivery_validated = False
                if part_shipped:
                    for picking in sale_order.picking_ids:
                        if picking.state == 'assigned':
                            try:
                                _logger.info("Attempting to auto-validate delivery: %s", picking.name)
                                picking.button_validate()
                                delivery_validated = True
                                _logger.info("Delivery auto-validated successfully: %s", picking.name)
                            except Exception as delivery_error:
                                _logger.warning("Could not auto-validate delivery %s: %s", picking.name,
                                                delivery_error)  # Changed to warning

                else:
                    _logger.info(" Delivery kept as assigned - partShipped is False")  # Info instead of error
                hold_or_cancel = order_data.get('holdOrCancel', False)
                if hold_or_cancel and auto_cancel_orders:
                    sale_order.action_cancel()
            except Exception as e:
                _logger.exception(f"❌ Failed creating sale.order {e}")
                return {'action': 'error', 'reason': 'failed_to_create_order'}
            action = 'created'

        # ===== EXECUTE WORKFLOW =====
        workflow_result = {'invoiced': False, 'delivered': False, 'cancelled': False, 'action': action}

        workflow_result['action'] = action
        return workflow_result

    @http.route('/order/status_counts_status', type='jsonrpc', auth='user')
    def get_order_status_counts(self, **kwargs):
        """
        Fetch order:
          - Rishvi orders → Fetch directly from Odoo sale orders
          - Linnworks orders → fetched from external AWS Lambda API
        """
       
        page_number = kwargs.get('page_number', 1)
        start_time = time.time()

        # --- RISHVI COUNTS FROM ODOO DATABASE ---
        count_rishvi_order_draft = request.env['sale.order'].sudo().search_count([('state', '=', 'draft')])
        count_rishvi_order_sale = request.env['sale.order'].sudo().search_count([('state', '=', 'sale')])
        count_rishvi_order_cancel = request.env['sale.order'].sudo().search_count([('state', '=', 'cancel')])
        count_rishvi_order_synced = request.env['sale.order'].sudo().search_count([('linnworks_sync', '=', True)])

        rishvi_counts = {
            "draft": count_rishvi_order_draft,
            "confirmed": count_rishvi_order_sale,
            "cancelled": count_rishvi_order_cancel,
            "synced": count_rishvi_order_synced,
        }

        # ---  LINNWORKS COUNTS (FROM EXTERNAL API) ---
        lineworks_counts = {"pending": 0, "processed": 0, "dispatched": 0, "returned": 0}

        try:
            icp = request.env["ir.config_parameter"].sudo()
            lw_token = icp.get_param("lw_token")
            rishvi_base_api_url = icp.get_param("rishvi_base_api_url")
            rishvi_app = icp.get_param("rishvi_app")    
            params = {"appName": rishvi_app, "appToken": lw_token}
            headers = {"accept": "*/*"}
            url= f"{rishvi_base_api_url}/Order/order-status-counts"
            response = requests.get(url, params=params, headers=headers, timeout=15)
            response.raise_for_status()
            data = response.json()

            for item in data:
                status = (item.get("status") or "").upper()
                count = int(item.get("count", 0))

                if status in ["PENDING", "UNPAID"]:
                    lineworks_counts["pending"] += count
                elif status == "PAID":
                    lineworks_counts["processed"] += count
                elif status == "RESEND":
                    lineworks_counts["dispatched"] += count
                elif status == "RETURN":
                    lineworks_counts["returned"] += count

        except requests.exceptions.RequestException as e:
            _logger.error("Error fetching Linnworks order status counts: %s", e)

        _logger.info("🔍 Rishvi Counts: %s", rishvi_counts)
        _logger.info("🔍 Linnworks Counts: %s", lineworks_counts)

        # ---  FINAL RESPONSE ---
        return {
            "success": True,
            "data": {
                "rishvi_orders": rishvi_counts,
                "lineworks_orders": lineworks_counts,
            },
        }


