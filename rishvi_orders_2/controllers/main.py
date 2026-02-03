# -*- coding: utf-8 -*-
import logging
import odoo
from odoo import http, _
from odoo.http import request
from odoo import models, api, exceptions, fields

import requests

_logger = logging.getLogger(__name__)


class LinnOrderController(http.Controller):

    @http.route('/linnworks/get-order-by-numid', type='jsonrpc', auth='user', methods=['POST'])
    def import_order_by_number(self, numOrderId=None, **kwargs):
        _logger = logging.getLogger(__name__)
        try:
            if not numOrderId:
                return {'success': False, 'message': "No Order Number provided."}
            existing_order = request.env['sale.order'].search([
                ('linn_order_number', '=', numOrderId)
            ], limit=1)

            if existing_order:
                return {'success': False, 'message': f"Order {numOrderId} number already exists."}

            SaleOrder = request.env['sale.order'].sudo()
            Product = request.env['product.template'].sudo()
            Partner = request.env['res.partner'].sudo()
            Carrier = request.env['sale.shipping.services'].sudo()
            company = request.env.company
            StockQuant = request.env['stock.quant']

            icp = request.env["ir.config_parameter"].sudo()
            lw_token = (icp.get_param("lw_token") or "").strip()
            base_url = (icp.get_param("rishvi_base_api_url") or "").strip()
            app_name = (icp.get_param("rishvi_app") or "").strip()

            if not lw_token or not base_url or not app_name:
                return {'success': False, 'message': "Missing API credentials."}

            url = f"{base_url}/Order/get-order-by-numid"
            params = {"appName": app_name, "appToken": lw_token, "numOrderId": numOrderId}
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()

            if not response:
                return {'success': False, 'message': "Missing response data. Cannot proceed."}

            order_data = response.json()

            items = order_data.get("items", [])
            source_name = order_data.get("generalInfo", {}).get("source")
            if source_name == "RISHVI_POS":
                return {'success': False, 'message': "POS Orders are not imported via this method."}

            if not items:
                return {'success': False, 'message': "No order lines found"}  # or return False / some ID as needed

            if not order_data:
                return {'success': False, 'message': f"No order found with number {numOrderId}"}

            # --- Partner ---
            addr = order_data.get("customerInfo", {}).get("address") or {}
            billing_address = order_data.get("customerInfo", {}).get("billingAddress") or {}

            partner = None
            try:
                Partner = request.env['res.partner'].sudo()
                country = request.env['res.country'].sudo().search(
                    [('name', 'ilike', addr.get("country") or "United Kingdom")], limit=1)
                if not country:
                    country = request.env['res.country'].sudo().search([('code', '=', 'GB')], limit=1)
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
                    billing_partner = request.env['res.partner'].search([
                        ('name', '=', 'Guest'),], limit=1)
                else:
                    billing_partner = request.env['res.partner'].search([
                        ('name', '=', billing_vals.get('name')),
                        ('email', '=', billing_vals.get('email')),
                        ('phone', '=', billing_vals.get('phone')),
                    ], limit=1)
                if addr.get("fullName") == False or addr.get("fullName") == "":
                    partner = request.env['res.partner'].search([
                        ('name', '=', 'Guest'),], limit=1)
                else:
                    partner = Partner.search([
                        ('name', '=', partner_vals.get("name")),
                        ('phone', '=', partner_vals.get("phone")),
                        ('email', '=', partner_vals.get("email"))
                    ], limit=1)
                

                if not partner:
                    # Search for existing partner by each field
                    # Case 1: Y Y Y Y → Existing user → No child
                    case1_partner = Partner.search([('name', '=', addr.get("fullName")),('phone', '=', addr.get("phoneNumber")),('street', '=', addr.get("address1")),('email', '=', addr.get("emailAddress"))], limit=1)

                    # Case 2: N Y Y N → Existing → Make Child with new val
                    case2_partner = Partner.search([('phone', '=', addr.get("phoneNumber")),('street', '=', addr.get("address1")),], limit=1)

                    # Case 3: N N N Y → Existing → Make Child with new val
                    case3_partner = Partner.search([('email', '=', addr.get("emailAddress"))], limit=1)

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
                        ('street', '=', billing_address.get('Address2'))
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

            order_lines = []

            for item in order_data.get("items", []):
                name= item.get("title") or "Linnworks Product"
                sku = item.get("sku") or item.get("itemNumber")
                item_id = item.get("itemId")
                product = Product.search([('default_code', '=', sku)], limit=1)
                price_unit = item.get('pricePerUnit', 0.0) or 0.0

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
                
                # pos_category = request.env['pos.category'].sudo()
                # pos_category_obj = pos_category.search([('name', '=', category_name)], limit=1)
                # if not pos_category_obj:
                #     pos_category_obj = pos_category.create({'name': category_name})


             
                product = request.env['product.product'].sudo().search([('default_code', '=', sku)], limit=1)
                if not product:
                    product = request.env['product.product'].sudo().create({
                        'name': item.get('title', sku) or sku,
                        'default_code': sku,
                        'type': 'consu',
                        'is_storable': True,
                        'available_in_pos': True,
                        'list_price': item.get('pricePerUnit', 0.0),
                        'linnworks_item_id': item_id,
                        'categ_id': category.id if category else False,
                        # 'pos_categ_ids': [(4, pos_category_obj.id)]
                    })
                    _logger.info(f"🆕 Created product for SKU {sku} -> {product.name} ({product.id})")

                qty = item.get('quantity', 1) or 1
                unit_price = round(float(item.get("pricePerUnit")), 2)
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
                order_lines.append((0, 0, {
                    'product_id': product.id,
                    'name': item.get("title") or product.name,
                    'product_uom_qty': qty,
                    'price_unit': unit_price or 0.0,
                    'company_id': company.id,
                    # 'product_uom': product.uom_id.id,
                    'discount': item.get('discount') or 0.0,
                    'tax_ids': [(6, 0, tax.ids)]  # Add taxes here

                }))

            # --- Carrier ---
            shipping = order_data.get("shippingInfo") or {}
            carrier = Carrier.search([('postal_service_name', '=', shipping.get("postalServiceName") or "Default")],
                                     limit=1)

            # --- Currency ---
            totals = order_data.get("totalsInfo") or {}
            currency = request.env['res.currency'].sudo().search([('name', '=', totals.get("currency") or "GBP")],limit=1)

            # --- Payment Term ---
            payment_term_name = order_data.get("paymentInfo", {}).get("paymentTerm")
            payment_term = request.env['account.payment.term'].sudo().search([('name', '=', payment_term_name)],
                                                                             limit=1)

            # --- Create or Update Sale Order ---
            existing_order = SaleOrder.search([('name', '=', numOrderId)], limit=1)
            # Get or create the source record
            source_name = order_data.get("generalInfo", {}).get("source")
            source_record = False

            SOURCE_MODEL = 'source.details'  # ⬅️ CHANGE THIS to your actual model

            sub_source_name = order_data.get("generalInfo", {}).get("subSource")
            sub_source_record = False

            SUB_SOURCE_MODEL = 'sub.source.details'  # ⬅️ CHANGE THIS to your actual model

            if source_name and source_name not in ["None", "False", "null", ""]:
                try:
                    # Search for existing source
                    source_record = request.env[SOURCE_MODEL].sudo().search([
                        ('name', '=', source_name)
                    ], limit=1)

                    # Create if doesn't exist
                    if not source_record:
                        source_record = request.env[SOURCE_MODEL].sudo().create({
                            'name': source_name
                        })
                        _logger.info(" Created new source: %s (ID: %s)", source_name, source_record.id)
                    else:
                        _logger.info(" Found existing source: %s (ID: %s)", source_name, source_record.id)

                except Exception as e:
                    _logger.warning(" Could not process source '%s': %s", source_name, e)
                    source_record = False

            if sub_source_name and sub_source_name not in ["None", "False", "null", ""]:
                try:
                    # Search for existing source
                    sub_source_record = request.env[SUB_SOURCE_MODEL].sudo().search([
                        ('name', '=', sub_source_name)
                    ], limit=1)

                    # Create if doesn't exist
                    if not sub_source_record:
                        sub_source_record = request.env[SUB_SOURCE_MODEL].sudo().create({
                            'name': sub_source_name
                        })
                        _logger.info(" Created new source: %s (ID: %s)", sub_source_name, sub_source_record.id)
                    else:
                        _logger.info(" Found existing source: %s (ID: %s)", sub_source_name, sub_source_record.id)

                except Exception as e:
                    _logger.warning(" Could not process source '%s': %s", sub_source_name, e)
                    sub_source_record = False

            notes_list = order_data.get('notes') or []
            first_note = notes_list[0].get('note') if len(notes_list) > 0 else ""

            order_vals = {
                'partner_id': partner.id if partner else False,
                'partner_invoice_id': billing_partner.id,
                'partner_shipping_id': partner.id,
                'order_line': order_lines,
                'currency_id': currency.id,
                'company_id': company.id,
                'linnworks_order_id': str(order_data.get("orderId")),
                'linn_order_number': str(order_data.get("numOrderId")),
                'payment_term_id': payment_term.id if payment_term else False,
                'is_parked': bool(order_data.get("generalInfo", {}).get("isParked")),
                'linn_order_source': source_record.id if source_record else False,
                # 'linn_order_sub_source': str(order_data.get("generalInfo", {}).get("subSource")),
                'linn_order_sub_source': sub_source_record.id if sub_source_record else False,
                'linnworks_sync': True,
                'status': str(order_data.get("generalInfo", {}).get("status")),
                'notes': first_note,
                'vendor_id': shipping.get("vendor") or "",
                'shipping_service_id': carrier.id,
                'order_tracking': shipping.get("trackingNumber") or ""
            }

            if existing_order:
                existing_order.write(order_vals)
                sale_order = existing_order
            else:
                sale_order = SaleOrder.create(order_vals)

            # --- Confirm Sale Order & Create Draft Invoice ---
            sale_order.action_confirm()

            invoice = sale_order._create_invoices()  # Draft invoice only

            # --- Process Delivery ---
            for picking in sale_order.picking_ids:
                if picking.state not in ['done', 'cancel']:
                    picking.action_confirm()
                    for move in picking.move_ids:
                        move.quantity = move.product_uom_qty
                    picking.action_assign()
                    picking.button_validate()

            status =  order_data.get("generalInfo", {}).get("status")
            part_shipped = shipping.get("partShipped") or False

            _logger.info("Auto-processing check - Status: %s (1=Paid, 0=Unpaid), PartShipped: %s", status,
                         part_shipped)

            # --- Post Invoice if status == 1 (PAID) ---
            invoice_posted = False
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

            # --- Prepare response message ---
            message = f"Order {numOrderId} imported successfully!"
            if (status == 1 and  invoice_posted) or status == 'PAID':
                message += " (Invoice auto-posted for PAID order)"
            elif status == 0 or status == 'UNPAID' :
                message += " (Invoice kept as draft - order UNPAID)"
            elif status == 1 and not invoice_posted:
                message += " (PAID order - invoice processing completed)"

            if part_shipped and delivery_validated:
                message += " (Delivery auto-validated)"
            elif part_shipped and not delivery_validated:
                message += " (Part-shipped order - delivery processing completed)"
            else:
                message += " (Delivery kept as assigned)"

            _logger.info("🎊 %s", message)

            return {
                'success': True,
                'message': message,
                'invoice_posted': invoice_posted,
                'delivery_validated': delivery_validated,
                'order_status': 'posted' if invoice_posted else 'draft'
            }
        except Exception as e:
            request.env.cr.rollback()
            _logger.error("❌ Linnworks Import Error: %s", e, exc_info=True)
            return {'success': False, 'message': f"Error importing order: {str(e)}"}


