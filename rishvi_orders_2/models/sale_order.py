from odoo import models, fields, api, exceptions ,_
import logging
from odoo.http import request
import requests
from odoo.tools import float_round
import json



from odoo.exceptions import ValidationError
from datetime import datetime, timedelta, timezone

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    linnworks_sync = fields.Boolean(copy=False)
    linn_order_source = fields.Many2one(
        'source.details',
        string='Source',
        default=lambda self: self._safe_default_source()
    )
    linn_order_sub_source = fields.Many2one('sub.source.details',string='Sub Source')
    #
    # linn_order_sub_source =  fields.Selection([
    #     ('B2B', 'Business to Business'),
    #     ('B2C', 'Business to Consumer'),
    #     ('C2C', 'Consumer to Consumer'),
    #     ('C2B', 'Consumer to Business'),
    #     ('B2G', 'Business to Government'),
    #     ('G2B', 'Government to Business'),
    #     ('B2B2C', 'Business to Business to Consumer'),
    #     ('D2C', 'Direct to Consumer'),
    #     ('B2E', 'Business to Employee'),
    #
    # ], string="Sub Source", default='B2B')
    
    status = fields.Selection([
    ('0', 'Unpaid'),
    ('1', 'Paid'),
    ('2', 'Return'),
    ('3', 'Pending'),
    ('4', 'Resend'),
    ], string="Order Status", default='0', copy=False)
    notes = fields.Text(string="Note", copy=False)
    is_parked = fields.Boolean(string="Is Parked(Tick for Yes)", default=False, copy=False)
    #quicksale merge
    quick_sale = fields.Boolean(string="Quick Sale",
                                states={
                                    'draft': [('readonly', False)],
                                    'sent': [('readonly', False)],
                                    'sale': [('readonly', True)],
                                    'done': [('readonly', True)],
                                    'cancel': [('readonly', True)],
                                }, )

    shipping_service_id = fields.Many2one(
        'sale.shipping.services',
        string="Shipping Service",
        default=lambda self: self._safe_default_shipping_service(),
    )

    def _safe_default_shipping_service(self):
        # Avoid running default during module installation or upgrades
        if self.env.context.get('install_mode') or self.env.context.get('module'):
            return False

        return self._get_default_shipping_service()

    def _get_default_shipping_service(self):
        # Search by postal_service_name field
        service_names = [
            'Default',
        ]

        for name in service_names:
            service = self.env['sale.shipping.services'].search([
                ('postal_service_name', '=', name)
            ], limit=1)
            if service:
                return service.id
            
    def _safe_default_source(self):
        # Avoid running default during module installation or upgrades
        if self.env.context.get('install_mode') or self.env.context.get('module'):
            return False

        return self._get_default_source()


    def _get_default_source(self):
        Source = self.env['source.details']
        # Try to find existing "Rishvi"
        source = Source.search([('name', '=', 'Rishvi')], limit=1)

        # If not found → create it
        if not source:
            source = Source.create({
                'name': 'Rishvi',
            })

        return source.id

    shipping_service_amount = fields.Monetary(
        string="Shipping Cost",
        currency_field='currency_id',
        compute='_compute_shipping_service_amount',
        store=True,
    )
    service_id = fields.Char(related='shipping_service_id.service_id', string="Service ID", readonly=True)
    postal_service_name = fields.Char(related='shipping_service_id.postal_service_name', string="Postal Service",
                                      readonly=True)
    vendor_id = fields.Many2one(related='shipping_service_id.vendor_id', string="Vendor", readonly=True)
    amount = fields.Monetary(related='shipping_service_id.amount', string="Shipping Cost", readonly=True,
                             currency_field='currency_id')
    order_tracking = fields.Char(string="Order Tracking number")
    service_country = fields.Many2one(related='shipping_service_id.service_country', string="Service Country",
                                      readonly=True)


    @api.depends('shipping_service_id', 'currency_id', 'company_id', 'date_order')
    def _compute_shipping_service_amount(self):
        """Compute shipping amount in order currency (for UI preview)."""
        for order in self:
            svc = order.shipping_service_id
            if not svc:
                order.shipping_service_amount = 0.0
                continue
            amt = svc.amount or 0.0
            svc_currency = svc.currency_id or order.company_id.currency_id
            if svc_currency and order.currency_id and svc_currency != order.currency_id:
                date = (order.date_order and fields.Datetime.to_datetime(order.date_order).date()
                        or fields.Date.context_today(order))
                amt = svc_currency._convert(amt, order.currency_id, order.company_id, date)
            order.shipping_service_amount = float_round(
                amt, precision_rounding=(order.currency_id or order.company_id.currency_id).rounding
            )

    def _sync_shipping_line(self):
        """Server-side: ensure exactly one shipping order line exists, updated to current service/amount.

        - If no shipping service or zero amount: remove any shipping lines.
        - Otherwise update first shipping line or create one if missing.
        - Remove any duplicate shipping lines if present.
        """
        Product = self.env['product.product']
        SaleLine = self.env['sale.order.line']

        for order in self:
            ship_lines = order.order_line.filtered(lambda l: l.is_shipping_line)
            svc = order.shipping_service_id
            amount = float(order.shipping_service_amount or 0.0)

            # Currency rounding
            rounding = (order.currency_id or order.company_id.currency_id).rounding
            amount = float_round(amount, precision_rounding=rounding)

            # If no service or amount <= 0: remove shipping lines
            if not svc or amount <= 0.0:
                if ship_lines:
                    ship_lines.sudo().unlink()
                continue

            # Determine product: prefer svc.product_id; else find or create generic
            product = getattr(svc, 'product_id', False)
            if not product:
                product = Product.search([('default_code', '=', 'DELIVERY_GENERIC')], limit=1)
                if not product:
                    product_vals = {
                        'name': 'Shipping - Generic',
                        'type': 'service',
                        'default_code': 'DELIVERY_GENERIC',
                        'sale_ok': True,
                        'purchase_ok': False,
                    }
                    product = Product.create(product_vals)

            # Keep one shipping line, remove extras
            main_ship = ship_lines[:1] if ship_lines else None
            if len(ship_lines) > 1:
                (ship_lines - main_ship).sudo().unlink()

            # Prepare values for the shipping line
            # NOTE: tax_id set to empty list so shipping has NO tax. Adjust if you want taxes.
            line_vals = {
                'order_id': order.id,
                'product_id': product.id,
                'name': svc.postal_service_name or product.display_name or 'Shipping',
                'product_uom_qty': 1.0,
                'price_unit': amount,
                'is_shipping_line': True,
                'tax_ids': [(6, 0, [])],  # no tax on shipping line by default
                'sequence': 99999,
            }

            if main_ship and main_ship.id:
                # Update persisted shipping line
                main_ship.sudo().write(line_vals)
            else:
                # Create shipping line (persist)
                SaleLine.sudo().create(line_vals)


    # Ensure server-side create/write call the sync method (idempotent)
    @api.model_create_multi
    def create(self, vals_list):
        orders = super(SaleOrder, self).create(vals_list)
        # Run sync for all created orders
        orders._sync_shipping_line()
        return orders

    def write(self, vals):
        res = super(SaleOrder, self).write(vals)
        # Sync shipping lines for affected records; idempotent so safe to always call
        self._sync_shipping_line()
        return res

    def _ensure_shipping_line(self, order):
        """Create or update the shipping order line for `order` based on order.shipping_service_id.
        Returns the shipping line (recordset of one) or empty recordset if none.
        """
        self.ensure_one()
        order = order  # local alias
        svc = order.shipping_service_id
        if not svc:
            # if service removed, delete existing shipping line(s)
            existing = order.order_line.filtered(lambda l: l.is_shipping_line)
            if existing:
                existing.unlink()
            return self.env['sale.order.line']

        # choose product: prefer svc.product_id if exists, else try generic delivery product code
        product = False
        if hasattr(svc, 'product_id') and svc.product_id:
            product = svc.product_id
        else:
            product = self.env['product.product'].search([('default_code', '=', 'DELIVERY_GENERIC')], limit=1)
            if not product:
                product = self.env['product.product'].create({
                    'name': 'Shipping - Generic',
                    'type': 'service',
                    'default_code': 'DELIVERY_GENERIC',
                    'sale_ok': True,
                    'purchase_ok': False,
                })

        # compute price in order currency (convert if necessary)
        service_amount = svc.amount or 0.0
        service_currency = getattr(svc, 'currency_id', False) or order.company_id.currency_id
        if service_currency and order.currency_id and service_currency != order.currency_id:
            date = (order.date_order and fields.Datetime.to_datetime(order.date_order).date()
                    or fields.Date.context_today(order))
            service_amount = service_currency._convert(service_amount, order.currency_id, order.company_id, date)
        rounding = (order.currency_id or order.company_id.currency_id).rounding
        final_price = float_round(service_amount, precision_rounding=rounding)

        # find existing shipping line (we mark shipping lines with is_shipping_line)
        ship_line = order.order_line.filtered(lambda l: l.is_shipping_line)[:1]
        vals = {
            'product_id': product.id,
            'name': svc.postal_service_name or product.display_name or 'Shipping',
            'product_uom_qty': 1.0,
            'price_unit': final_price,
            'is_shipping_line': True,
            # taxes: use product taxes by default (if you want no taxes use [] here)
            'tax_ids': [(6, 0, product.taxes_id.ids)] if product and product.taxes_id else False,
        }

        if ship_line:
            # Update existing (use sudo to avoid access problems)
            try:
                ship_line.sudo().write(vals)
            except Exception:
                # fallback to write without sudo
                ship_line.write(vals)
            return ship_line
        else:
            # create new shipping line record
            vals.update({
                'order_id': order.id,
            })
            new_line = self.env['sale.order.line'].sudo().create(vals)
            return new_line

 #quick sale
    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for order in self:
            if order.quick_sale:
                invoice = order._create_invoices()
                if invoice:
                    invoice.action_post()

                for picking in order.picking_ids:
                    if picking.state not in ['done', 'cancel']:
                        picking.action_confirm()
                        # Set all move lines' done quantity equal to the demanded quantity
                        for move in picking.move_ids_without_package:
                            move.quantity = move.product_uom_qty
                        picking.action_assign()
                        picking.button_validate()

        return res

    def action_sync_linnworks_order(self):
        """ Button action to create Linnworks order """
        for order in self:
            # Log action
            _logger.info(f"Creating Linnworks Order for Sale Order: {order}")
            _logger.info(f"Creating Linnworks Order for Sale Order ID: {order.id}")
            
            if not order.order_line:
                return {
                    "type": "ir.actions.client",
                    "tag": "display_notification",
                    "params": {
                        "title": "Missing Order Lines",
                        "message": f"Please add at least one product to the order {order.name} before syncing to Linnworks.",
                        "type": "warning",  # 'success', 'warning', 'info', 'danger'
                        "sticky": True
                    }
                }

                # Check if shipping service is set
            if not order.shipping_service_id:
                return {
                    "type": "ir.actions.client",
                    "tag": "display_notification",
                    "params": {
                        "title": "Shipping Service Missing",
                        "message": f"Please select a Shipping Service for {order.name} before syncing.",
                        "type": "warning",
                        "sticky": True,
                    },
                }

            icp = request.env["ir.config_parameter"].sudo()
            lw_token = icp.get_param("lw_token").strip()
            rishvi_base_api_url = icp.get_param("rishvi_base_api_url").strip()
            rishvi_app = icp.get_param("rishvi_app").strip()
            
            raw_time = str(order.date_order)
            try:
                # Try parsing normally first
                dt = datetime.strptime(raw_time[:19], "%Y-%m-%d %H:%M:%S")
            except ValueError:
                # Fallback if seconds part is broken
                parts = raw_time.split()
                date_part = parts[0]
                time_part = parts[1].split(":")[:3]
                fixed_time = ":".join(time_part)
                dt = datetime.strptime(f"{date_part} {fixed_time}", "%Y-%m-%d %H:%M:%S")

            # Convert to UTC and ISO 8601 with milliseconds
            iso_time_recieved_order = dt.replace(tzinfo=timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
            linn_order_invoiced_status=0
            linn_order_shipping_status=False
            linn_order_parked_status=False
            linn_order_Cancel_OnHold_status=False
            payment_status="UNPAID"
            
            if order.invoice_ids and order.invoice_ids[0].state=="posted":
                linn_order_invoiced_status=1
                payment_status="PAID"
                
            if order.delivery_status=="full":
                linn_order_shipping_status=True
            if order.state=="cancel":
                linn_order_Cancel_OnHold_status=True
            
            url = f"{rishvi_base_api_url}/Order/create-order"
            data = {
                    "source": str(order.linn_order_source.name or ""),
                    "subSource": str(order.linn_order_sub_source.name or ""),
                    "referenceNumber": str(order.name),
                    "postalServiceId": str(order.service_id),
                    "postalServiceName": str(order.postal_service_name),
                    "savePostalServiceIfNotExist": True,
                    "receivedDate": str(iso_time_recieved_order),
                    "dispatchBy": str(iso_time_recieved_order),
                    "currency": str(order.pricelist_id.currency_id.name),
                    "paymentStatus": str('UNPAID'),
                    "channelBuyerName": str(order.partner_invoice_id.name),
                    "postalServiceCost": float(order.shipping_service_id.amount or 0.0),
                    "postalServiceTaxRate": 0,
                    "status": int(linn_order_invoiced_status),
                    "holdOrCancel": linn_order_Cancel_OnHold_status,
                    "isParked": linn_order_parked_status,
                    "partShipped": linn_order_shipping_status,
                    "useChannelTax": True,
                    "postageCost":  float(order.shipping_service_id.amount or 0.0),

                   "billingAddress": {
                    "fullName": str(order.partner_invoice_id.name or ""),
                    "address1": str(order.partner_invoice_id.street or ""),
                    "town": str(order.partner_invoice_id.city or ""),
                    "postCode": str(order.partner_invoice_id.zip or ""),
                    "country": str(order.partner_invoice_id.country_id.name or ""),
                    "emailAddress": str(order.partner_invoice_id.email or ""),
                    "company": str(order.partner_invoice_id.company_name or ""),
                    "phoneNumber": str(order.partner_invoice_id.phone or "")
                    },
                    "deliveryAddress": {
                        "fullName": str(order.partner_invoice_id.name or ""),
                        "address1": str(order.partner_shipping_id.street or ""),
                        "town": str(order.partner_shipping_id.city or ""),
                        "postCode": str(order.partner_shipping_id.zip or ""),
                        "country": str(order.partner_shipping_id.country_id.name or ""),
                        "emailAddress": str(order.partner_shipping_id.email or ""),
                        "company": str(order.partner_shipping_id.company_id.name or ""),
                        "phoneNumber": str(order.partner_shipping_id.phone or "")
                    },
                    "orderItems": [
                        {
                            "sku": str(line.product_id.default_code),
                            "itemNumber": str(line.product_id.linnworks_item_id),
                            "itemTitle": str(line.product_id.name),
                            "pricePerUnit": line.price_unit,
                            "qty": int(line.product_uom_qty),
                            "taxRate": sum(t.amount for t in line.tax_ids) if line.tax_ids else 0.0,
                            "taxCostInclusive": False,
                            "discount": float(line.discount or 0.0),
                        }
                        for line in order.order_line
                        if not getattr(line, "is_shipping_line", False)

                    ],
                    "notes": [
                        {
                            "note": order.notes if order.notes else "",
                            "createdBy": "RISHVI",
                            "internal": True
                        }
                    ]
                }
            
            if order.linnworks_sync==True:
                url = f"{rishvi_base_api_url}/Order/update-order"               

                data = {'orderId': str(order.linnworks_order_id),
                        "source": str(order.linn_order_source.name),
                        "subSource": str(order.linn_order_sub_source.name or ""),
                        "referenceNumber": str(order.name),
                        "postalServiceId": str(order.service_id),
                        "postalServiceName": str(order.postal_service_name),
                        "savePostalServiceIfNotExist": True,
                        "receivedDate": str(iso_time_recieved_order),
                        "dispatchBy": str(iso_time_recieved_order),
                        "currency": str(order.pricelist_id.currency_id.name),
                        "paymentStatus": payment_status,
                        "channelBuyerName": str(order.partner_invoice_id.name),
                        "postalServiceCost": order.shipping_service_amount,
                        "postalServiceTaxRate": 0,
                        "status": int(linn_order_invoiced_status),
                        "holdOrCancel": linn_order_Cancel_OnHold_status,
                        "isParked": linn_order_parked_status,
                        "partShipped": linn_order_shipping_status,
                        "useChannelTax": True,
                        "postageCost": order.shipping_service_amount,
                        "billingAddress": {
                            "fullName": str(order.partner_invoice_id.name or ""),
                            "address1": str(order.partner_invoice_id.street or ""),
                            "town": str(order.partner_invoice_id.city or ""),
                            "postCode": str(order.partner_invoice_id.zip or ""),
                            "country": str(order.partner_invoice_id.country_id.name or ""),
                            "emailAddress": str(order.partner_invoice_id.email or ""),
                            "company": str(order.partner_invoice_id.company_name or ""),
                            "phoneNumber": str(order.partner_invoice_id.phone or "")
                        },
                        "deliveryAddress": {
                            "fullName": str(order.partner_invoice_id.name or ""),
                            "address1": str(order.partner_shipping_id.street or ""),
                            "town": str(order.partner_shipping_id.city or ""),
                            "postCode": str(order.partner_shipping_id.zip or ""),
                            "country": str(order.partner_shipping_id.country_id.name or ""),
                            "emailAddress": str(order.partner_shipping_id.email or ""),
                            "company": str(order.partner_shipping_id.company_id.name or ""),
                            "phoneNumber": str(order.partner_shipping_id.phone or "")
                        },
                        "orderItems": [
                            {
                                "sku": str(line.product_id.default_code),
                                "itemNumber": str(line.product_id.linnworks_item_id),
                                "itemTitle": str(line.product_id.name),
                                "pricePerUnit": line.price_unit,
                                "qty": int(line.product_uom_qty),
                                "taxRate": sum(t.amount for t in line.tax_ids) if line.tax_ids  else 0.0,
                                "taxCostInclusive": False,
                                "discount": float(line.discount or 0.0),
                            }
                            for line in order.order_line
                            if not getattr(line, "is_shipping_line", False)

                        ],
                        "notes": [
                                {
                                    "note": order.notes or "",
                                    "createdBy": "RISHVI",
                                    "internal": True,
                                }
                            ],
                    }             
            
            params = {"appName": rishvi_app, "appToken": lw_token}
            headers = {"accept": "*/*", "Content-Type": "application/json"}

            
            # _logger.info(data)
            try:
                response = requests.post(url, params=params, headers=headers, data=json.dumps(data), timeout=15)
                response.raise_for_status()
                data = response.json()
                if response.status_code == 200:
                    if order.linnworks_sync==True:
                        return {
                            "type": "ir.actions.client",
                            "tag": "display_notification",
                            "params": {
                                "title": "Success",
                                "message": data['message'],
                                "type": "success",
                                "sticky": True,  # Disappears after a few seconds
                            }
                        }
                    order.write({
                        'linnworks_order_id': data['orderId'],
                        'linn_order_number':data['numOrderId'],
                        'linnworks_sync': True,
                    })
                    return {
                        "type": "ir.actions.client",
                        "tag": "display_notification",
                        "params": {
                            "title": "Success",
                            "message": f"Your {order.name} Orders successfully synced!",
                            "type": "success",
                            "sticky": True,  # Disappears after a few seconds
                             "next": {
                                "type": "ir.actions.client",
                                "tag": "reload"  # reloads the current view
                            }
                        }
                    }
            except requests.exceptions.RequestException as e:
                _logger.error("Error fetching order status counts: %s", e)
                return {
                    "type": "ir.actions.client",
                    "tag": "display_notification",
                    "params": {
                        "title": "Error",
                        "message": f"Error fetching order status counts: {str(e)}",
                        "type": "danger",   # 'success', 'warning', 'info', or 'danger'
                        "sticky": True       # Makes the toast stay until manually closed
                    }
                }

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    linn_product_Available_quantity=fields.Float(string="Linnworks Available" ,copy=False)
    linnworks_unit_cost = fields.Float(
        string="Linn Unit Retail",
        compute="_compute_linnworks_unit_cost",
        store=True,  # store=True if you want it searchable and visible in tree views
        copy=False
    )
    #shipping sale service
    is_shipping_line = fields.Boolean(string="Is Shipping Line", default=False)
    real_on_hand_qty = fields.Float(
        string="On Hand Qty",
        compute="_compute_real_on_hand_qty",
        digits="Product Unit of Measure",
        store=False,  # no need to store, always computed live
    )

    @api.depends("product_id")
    def _compute_real_on_hand_qty(self):
        """Compute the current available stock quantity of the product."""
        for line in self:
            if not line.product_id or line.product_id.type not in ('product', 'consu'):
                line.real_on_hand_qty = 0.0
                continue
            # Fetch live available quantity
            qty = line.product_id.qty_available
            line.real_on_hand_qty = qty


    @api.depends('price_unit')  # or 'product_id.lst_price' depending on your requirement
    def _compute_linnworks_unit_cost(self):
        for line in self:
            # Take value from the unit price
            line.linnworks_unit_cost = line.price_unit
    
    def check_for_linnwork_quantiy(self):
        _logger.info("Product %s with Linworks Id %s",self.product_id.id,self.product_id.linnworks_item_id)
        if self.product_id and self.product_id.linnworks_item_id:
            if self.product_id.linnworks_item_id== False:
                self.linn_product_Available_quantity=0.0
                return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': _('Warning'),
                             'message': _("Product is not Present in linnworks"),
                            'type': 'warning',
                            'sticky': False,
                        }
                    }  
            # Construct full URL
            icp = self.env["ir.config_parameter"].sudo()
            lw_token = icp.get_param("lw_token").strip()
            rishvi_base_api_url = icp.get_param("rishvi_base_api_url").strip()
            rishvi_app = icp.get_param("rishvi_app").strip()
            
            url = f"{rishvi_base_api_url}/Inventory/inventory-item/{self.product_id.linnworks_item_id}"
            params = {'appName':rishvi_app,
                      'appToken':lw_token}
            headers = {
                "accept": "application/json",
                "content-type": "application/json"
            }
            try:
                response = requests.get(
                    url,
                    params=params,
                    headers=headers,
                    timeout=10
                )
                response.raise_for_status  # Raise HTTP errors
                if response and response.json():
                    response = response.json()
                    stockLevel= response.get('stockLevels')
                    
                    request=self
                    for level in stockLevel:
                        warehouse = request.env['stock.warehouse'].search([
                            "|",
                            ("linnexternal_id", "=", level['locationId']),
                            ("name", "=",level['warehouseName'])
                        ], limit=1)
                        
                        location = warehouse.lot_stock_id
                        if warehouse:
                            _logger.info(warehouse)
                            quant = request.env['stock.quant'].search([('product_id', '=', self.product_id),('location_id', '=', location.id)], limit=1)
                            if quant:
                                quant.sudo().write({'quantity': level['quantity']})
                            
                            else:
                                quant=request.env['stock.quant'].sudo().create({
                                'product_id': self.product_id,
                                'location_id': location.id,
                                'quantity': level['quantity'],
                                'company_id': request.env.company.id,
                                })                   
                        else:                      
                            vals = {
                                "name": level['warehouseName'],
                                "code": level['warehouseName'][:5].upper().replace(" ", ""),  # short code
                                "linnexternal_id": level['locationId'],
                            }
                            warehouse=request.env['stock.warehouse'].create(vals)
                            location = warehouse.lot_stock_id
                            request.env['stock.quant'].sudo().create({
                                'product_id': self.product_id,
                                'location_id': location.id,
                                'quantity': level['quantity'],
                                'company_id': request.env.company.id,
                                })

                    if stockLevel:
                        stock_lines = [
                            "%s: %s units" % (s.get("warehouseName", "Unknown"), s.get("quantity", 0))
                            for s in stockLevel
                        ]
                        stock_summary = ", ".join(stock_lines)
                        message = _("Available stock for %s → %s") % (self.product_id.display_name, stock_summary)
                    else:
                        message = _("No stock information available for %s") % self.product_id.display_name

                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': _('Info'),
                            'message': message,
                            'type': 'success',
                            'sticky': True
                        }
                    }

                return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': _('Warning'),
                             'message': _("Somthing Wents Wrong"),
                            'type': 'warning',
                            'sticky': False,
                        }
                    }  

            except requests.exceptions.RequestException as e:
                _logger.error("Error calling Linnworks controller: %s", e)
                return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': _("Error"),
                            'message': _("Could not fetch stock from Linnworks."),
                            'type': 'warning',
                            'sticky': False,
                        }
                    }

