from odoo import models, fields, api,_
from odoo.exceptions import ValidationError
import requests
import base64
import json
import re

import logging
_logger = logging.getLogger(__name__)

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    xero_purchase_id = fields.Char(string="Xero PO Id",copy=False)
    tax_state = fields.Selection([('inclusive', 'Tax Inclusive'), ('exclusive', 'Tax Exclusive'), ('no_tax', 'No Tax')],
                                 string='Tax Status')
    inclusive = fields.Boolean('Inclusive')

    @api.model
    def create(self, vals):
        order = super().create(vals)
        order._auto_set_tax_state()
        return order

    def write(self, vals):
        res = super().write(vals)
        self._auto_set_tax_state()
        return res

    def _auto_set_tax_state(self):
        for order in self:
            tax_states = set()
            for line in order.order_line:
                for tax in line.tax_ids:
                    # Ignore 0% taxes (tax-exempt)
                    if tax.amount == 0.0:
                        continue
                    _logger.info("Tax Found: %s | Type: %s", tax.name, tax.price_include_override)
                    if tax.price_include_override == 'tax_included':
                        tax_states.add('inclusive')
                    elif tax.price_include_override == 'tax_excluded':
                        tax_states.add('exclusive')

            # Determine tax state
            new_tax_state = 'exclusive'
            if 'inclusive' in tax_states and 'exclusive' in tax_states:
                new_tax_state = 'exclusive'  # fallback for mixed
            elif 'inclusive' in tax_states:
                new_tax_state = 'inclusive'
            elif not tax_states:
                new_tax_state = 'no_tax'

            if order.tax_state != new_tax_state:
                order.tax_state = new_tax_state
                order.inclusive = (new_tax_state == 'inclusive')

    @api.onchange('tax_state')
    def update_inclusive_flag(self):
        self.inclusive = (self.tax_state == 'inclusive')
        for line in self.order_line:
            line.inclusive = self.inclusive

    # @api.model
    # def create(self, vals):
    #     _logger.info("🛠️ Creating Purchase Order with vals: %s", vals)
    #     order = super().create(vals)
    #     order._auto_set_tax_state()
    #     return order
    #
    # def write(self, vals):
    #     _logger.info("Writing Purchase Order with vals: %s", vals)
    #     res = super().write(vals)
    #     self._auto_set_tax_state()
    #     return res
    #
    # @api.depends('order_line.taxes_id')
    # def _auto_set_tax_state(self):
    #     for order in self:
    #         tax_states = set()
    #         _logger.info(f"🔍 Checking tax state for PO: {order.name}")
    #         for line in order.order_line:
    #             for tax in line.taxes_id:
    #                 _logger.info(
    #                     f"   → Line {line.name}, Tax: {tax.name}, price_include_override = {tax.price_include_override}")
    #                 if tax.price_include_override == 'tax_included':
    #                     tax_states.add('inclusive')
    #                 elif tax.price_include_override == 'tax_excluded':
    #                     tax_states.add('exclusive')
    #
    #         new_tax_state = 'exclusive'
    #         if 'inclusive' in tax_states and 'exclusive' in tax_states:
    #             new_tax_state = 'exclusive'  # mixed fallback
    #         elif 'inclusive' in tax_states:
    #             new_tax_state = 'inclusive'
    #         elif not tax_states:
    #             new_tax_state = 'no_tax'
    #
    #         _logger.info(f"Final Tax State Decision: {new_tax_state}")
    #         if order.tax_state != new_tax_state:
    #             _logger.info(f"Updating tax_state from {order.tax_state} to {new_tax_state}")
    #             order.tax_state = new_tax_state
    #
    #         # Set line.inclusive based on new tax state
    #         for line in order.order_line:
    #             if new_tax_state == 'inclusive':
    #                 line.inclusive = True
    #             elif new_tax_state == 'exclusive':
    #                 line.inclusive = False
    #             else:
    #                 line.inclusive = False  # safe default for no_tax
    #
    # @api.onchange('tax_state', 'inclusive')
    # def update_inclusive_flag(self):
    #     for line in self.order_line:
    #         if self.tax_state == 'inclusive':
    #             line.inclusive = True
    #         elif self.tax_state == 'exclusive':
    #             line.inclusive = False
    #         elif self.tax_state == 'no_tax':
    #             line.inclusive = False

    # @api.model
    # @api.onchange('tax_state')
    # def onchange_tax_status(self):
    #     for line_id in self.order_line:
    #         if (self.tax_state == 'inclusive'):
    #             line_id.inclusive = True
    #         elif (self.tax_state == 'exclusive'):
    #             line_id.inclusive = False

    @api.model
    def prepare_purchaseorder_export_line_dict(self, line):
        #         line = self
        company = self.company_id
        if company:
            company = self.env['res.users'].search([('id', '=', self.env.uid)], limit=1).company_id
        line_vals = {}

        if self.partner_id:
            if line.tax_ids:
                line_tax = self.env['account.tax'].search([('id', '=', line.tax_ids.id),('company_id','=',company.id)])
                if line_tax:
                    tax = line_tax.xero_tax_type_id
                    if not tax:
                        self.env['account.tax'].get_xero_tax_ref(line_tax)
                        line_tax = self.env['account.tax'].search([('id', '=', line.tax_ids.id),('company_id','=',company.id)])
                        tax = line_tax.xero_tax_type_id

                    line_vals = {
                                'Description': line.name,
                                'UnitAmount': line.price_unit,
                                'ItemCode': line.product_id.default_code,
                                'Quantity': line.product_qty,
                                'TaxType': tax,
                                "DiscountRate": line.discount,
                                }
            else:
                if line.product_id:
                    line_vals = {
                        'Description': line.name,
                        'UnitAmount': line.price_unit,
                        'ItemCode': line.product_id.default_code,
                        'Quantity': line.product_qty,
                        "DiscountRate": line.discount,
                    }
                else:
                    line_vals = {
                        'Description': line.name,
                        "DiscountRate": line.discount
                        # 'UnitAmount': line.price_unit,
                        # 'ItemCode': line.product_id.default_code,
                        # 'Quantity': line.product_qty,
                    }

        return line_vals

    @api.model
    def prepare_purchaseorder_export_dict(self):
        company = self.company_id
        if not company:
            company = self.env['res.users'].search([('id', '=', self.env.uid)], limit=1).company_id

        if self.partner_id:
            cust_id = self.env['res.partner'].get_xero_partner_ref(self.partner_id)

        vals = {}
        lst_line = []
        if self.tax_state:
            if self.tax_state == 'inclusive':
                tax_state = 'Inclusive'
            elif self.tax_state == 'exclusive':
                tax_state = 'Exclusive'
            elif self.tax_state == 'no_tax':
                tax_state = 'NoTax'

        if self.state:
            if self.state == 'draft' or self.state == 'sent':
                status = 'DRAFT'
            elif self.state == 'purchase':
                status = 'AUTHORISED'
            else:
                status = 'DRAFT'

        if self.partner_ref:
            partner_ref = self.partner_ref
        else:
            partner_ref = ''

        def remove_tags(text):
            """
            Removes html test from string
            :param text:
            :return: new string
            """
            TAG_RE = re.compile(r'<[^>]+>')
            return TAG_RE.sub('', text)

        if self.note:
            notes = remove_tags(self.note)
        else:
            notes = ''


        if len(self.order_line) == 1:
            single_line = self.order_line

            if single_line.product_id.xero_product_id:
                _logger.info(_("PRODUCT DEFAULT CODE AVAILABLE"))
            elif not single_line.product_id.xero_product_id:
                self.env['product.product'].get_xero_product_ref(single_line.product_id)
            if single_line.tax_ids:
                line_tax = self.env['account.tax'].search([('id', '=', single_line.tax_ids.id),('company_id','=',company.id)])
                if line_tax:
                    tax = line_tax.xero_tax_type_id
                    # product = self.env['product.template'].get_xero_product_ref(single_line.product_id)
                    if not tax:
                        self.env['account.tax'].get_xero_tax_ref(line_tax)
                        line_tax = self.env['account.tax'].search([('id', '=', single_line.tax_ids.id),('company_id','=',company.id)])
                        tax = line_tax.xero_tax_type_id

                    vals.update({
                        "Contact": {"ContactID": cust_id},
                        "Date": str(self.date_order),
                        "PurchaseOrderNumber": self.name,
                        "DeliveryDate": str(self.date_planned) if self.date_planned else '',
                        "DeliveryInstructions":notes,
                        "Reference": partner_ref,
                        # "DeliveryAddress":address5,
                        "LineAmountTypes": tax_state,
                        "LineItems": [
                            {
                                "ItemCode":single_line.product_id.default_code,
                                "Description": single_line.name,
                                "Quantity": single_line.product_qty,
                                "UnitAmount": single_line.price_unit,
                                "TaxType":tax,
                                "DiscountRate": single_line.discount,
                            }
                        ],
                        "Status": status,
                    })
            else:
                vals.update({
                    "Contact": {"ContactID": cust_id},
                    "Date": str(self.date_order),
                    "PurchaseOrderNumber": self.name,
                    "DeliveryDate": str(self.date_planned) if self.date_planned else '',
                    # "DeliveryAddress": address5,
                    "DeliveryInstructions": notes,
                    "Reference": partner_ref,
                    "LineAmountTypes": tax_state,
                    "LineItems": [
                        {
                            "ItemCode": single_line.product_id.default_code,
                            "Description": single_line.name,
                            "Quantity": single_line.product_qty,
                            "UnitAmount": single_line.price_unit,
                            "DiscountRate": single_line.discount,
                        }
                    ],
                    "Status": status,
                })

        else:
            for line in self.order_line:

                if line.product_id.xero_product_id:
                    _logger.info(_("PRODUCT DEFAULT CODE AVAILABLE"))
                elif not line.product_id.xero_product_id:
                    self.env['product.product'].get_xero_product_ref(line.product_id)

                line_vals = self.prepare_purchaseorder_export_line_dict(line)
                lst_line.append(line_vals)
            vals.update({
                        "Contact": {"ContactID": cust_id},
                        "Date": str(self.date_order),
                        "PurchaseOrderNumber":self.name,
                        # "DeliveryAddress": address5,
                        "DeliveryDate": str(self.date_planned) if self.date_planned else '',
                        "Reference": partner_ref ,
                        "DeliveryInstructions": notes,
                        "LineAmountTypes": tax_state,
                        "LineItems": lst_line,
                        "Status": status
                    })
        currency = self.currency_id if self.currency_id else False
        if currency:
            vals.update({"CurrencyCode": currency.name})
        return vals

    def get_head(self):
        if self.env.context.get('cron'):
            xero_config = self.company_id
        else:
            xero_config = self.company_id
            if not xero_config:
                xero_config = self.env['res.users'].search([('id', '=', self.env.uid)], limit=1).company_id
        client_id = xero_config.xero_client_id
        client_secret = xero_config.xero_client_secret


        data = client_id + ":" + client_secret
        encodedBytes = base64.b64encode(data.encode("utf-8"))
        encodedStr = str(encodedBytes, "utf-8")
        headers = {
            'Authorization': "Bearer " + str(xero_config.xero_oauth_token),
            'Xero-tenant-id': xero_config.xero_tenant_id,
            'Accept': 'application/json'

        }
        return headers

    @api.model
    def exportPurchaseOrder(self):
        """export purchase order to QBO"""
        xero_config = self.company_id
        if not xero_config:
            xero_config = self.env['res.users'].search([('id', '=', self.env.uid)], limit=1).company_id
        if self.env.context.get('active_ids'):
            purchase = self.browse(self.env.context.get('active_ids'))
        else:
            purchase = self
        if purchase and self.env.context.get('not_cron'):
            xero_config = purchase[0].company_id
        for t in purchase:
            if not t.xero_purchase_id:
                vals = t.prepare_purchaseorder_export_dict()
                parsed_dict = json.dumps(vals)
                if xero_config.xero_oauth_token:
                    token = xero_config.xero_oauth_token
                headers = self.get_head()
                if token:
                    protected_url = 'https://api.xero.com/api.xro/2.0/PurchaseOrders'
                    data = requests.request('POST', url=protected_url, data=parsed_dict, headers=headers)
                    if data.status_code == 200:
                        response_data = json.loads(data.text)
                        if response_data.get('PurchaseOrders'):
                                t.xero_purchase_id = response_data.get('PurchaseOrders')[0].get('PurchaseOrderID')
                                self.env.cr.commit()
                        _logger.info(_("Exported successfully to XERO"))
                    elif data.status_code == 400:
                        logs = self.env['xero.error.log'].create({
                            'transaction': 'Purchase Order Export',
                            'xero_error_response': data.text,
                            'error_date': fields.Datetime.now(),
                            'record_id': t,
                        })
                        self.env.cr.commit()
                        response_data = json.loads(data.text)
                        if response_data:
                            if response_data.get('Elements'):
                                for element in response_data.get('Elements'):
                                    if element.get('ValidationErrors'):
                                        for err in element.get('ValidationErrors'):
                                            if err.get('Message'):
                                                raise ValidationError('(Purchase Order) Xero Exception : ' + err.get('Message'))
                            elif response_data.get('Message'):
                                raise ValidationError(
                                    '(Purchase Order) Xero Exception : ' + response_data.get('Message'))
                            else:
                                raise ValidationError(
                                    '(Purchase Order) Xero Exception : please check xero logs in odoo for more details')
                    elif data.status_code == 401:
                        raise ValidationError("Time Out.\nPlease Check Your Connection or error in application or refresh token..!!")
            else:
                vals = t.prepare_purchaseorder_export_dict()
                parsed_dict = json.dumps(vals)
                if xero_config.xero_oauth_token:
                    token = xero_config.xero_oauth_token
                headers=self.get_head()
                if token:
                    protected_url = 'https://api.xero.com/api.xro/2.0/PurchaseOrders/'+t.xero_purchase_id
                    data = requests.request('POST', url=protected_url, headers=headers, data=parsed_dict)
                    if data.status_code == 200:
                            _logger.info(_("Exported successfully to XERO"))
                    elif data.status_code == 400:
                        logs = self.env['xero.error.log'].create({
                            'transaction': 'Purchase Order Export',
                            'xero_error_response': data.text,
                            'error_date': fields.Datetime.now(),
                            'record_id': t,
                        })
                        self.env.cr.commit()
                        response_data = json.loads(data.text)
                        if response_data:
                            if response_data.get('Elements'):
                                for element in response_data.get('Elements'):
                                    if element.get('ValidationErrors'):
                                        for err in element.get('ValidationErrors'):
                                            if err.get('Message'):
                                                raise ValidationError('(Purchase Order) Xero Exception : ' + err.get('Message'))
                            elif response_data.get('Message'):
                                raise ValidationError(
                                    '(Purchase Order) Xero Exception : ' + response_data.get('Message'))
                            else:
                                raise ValidationError(
                                    '(Purchase Order) Xero Exception : please check xero logs in odoo for more details')
                    elif data.status_code == 401:
                        raise ValidationError("Time Out.\nPlease Check Your Connection or error in application or refresh token..!!")
        success_form = self.env.ref('rishvi_xero_odoo_connector.export_success_view', False)
        return {
            'name': _('Notification'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'res.company.message',
            'views': [(success_form.id, 'form')],
            'view_id': success_form.id,
            'target': 'new',
        }

    @api.model
    def exportPurchaseOrder_cron(self):
        # xero_config = self.env['res.users'].search([('id', '=', self.env.uid)], limit=1).company_id
        companys = self.env['res.company'].search([])
        # self.env.context['cron'] = 1
        self = self.with_context(cron=1)
        for xero_config in companys:
            if xero_config.xero_client_id and xero_config.xero_client_secret:
                xero_config.refresh_token()
                purchase_id = self.env['purchase.order'].search([('date_approve', '>', xero_config.export_record_after),('company_id', '=', xero_config.id),('state', '=', 'purchase'),('xero_purchase_id', '=', False)])
                for purchase in purchase_id:
                    purchase.exportPurchaseOrder()
            else:
                continue



class PurchaseOderLine(models.Model):
    _inherit = 'purchase.order.line'

    xero_purchase_line_id = fields.Char(string="Xero Id",copy=False)
    inclusive = fields.Boolean('Inclusive', default=False,copy=False)

# from odoo import models, fields, api,_
# from odoo.exceptions import ValidationError
# import requests
# import base64
# import json
# import re

# import logging
# _logger = logging.getLogger(__name__)

# class XeroPurchaseOrder(models.Model):
#     _inherit = 'purchase.order'

#     xero_purchase_id = fields.Char(string="Xero PO Id",copy=False)
#     tax_state = fields.Selection([('inclusive', 'Tax Inclusive'), ('exclusive', 'Tax Exclusive'), ('no_tax', 'No Tax')],
#                                  string='Tax Status')
#     inclusive = fields.Boolean('Inclusive')

#     @api.model
#     def create(self, vals):
#         order = super().create(vals)
#         order._auto_set_tax_state()
#         return order

#     def write(self, vals):
#         res = super().write(vals)
#         self._auto_set_tax_state()
#         return res

#     def _auto_set_tax_state(self):
#         for order in self:
#             tax_states = set()
#             for line in order.order_line:
#                 for tax in line.tax_ids:
#                     # Ignore 0% taxes (tax-exempt)
#                     if tax.amount == 0.0:
#                         continue
#                     _logger.info("Tax Found: %s | Type: %s", tax.name, tax.price_include_override)
#                     if tax.price_include_override == 'tax_included':
#                         tax_states.add('inclusive')
#                     elif tax.price_include_override == 'tax_excluded':
#                         tax_states.add('exclusive')

#             # Determine tax state
#             new_tax_state = 'exclusive'
#             if 'inclusive' in tax_states and 'exclusive' in tax_states:
#                 new_tax_state = 'exclusive'  # fallback for mixed
#             elif 'inclusive' in tax_states:
#                 new_tax_state = 'inclusive'
#             elif not tax_states:
#                 new_tax_state = 'no_tax'

#             if order.tax_state != new_tax_state:
#                 order.tax_state = new_tax_state
#                 order.inclusive = (new_tax_state == 'inclusive')

#     @api.onchange('tax_state')
#     def update_inclusive_flag(self):
#         self.inclusive = (self.tax_state == 'inclusive')
#         for line in self.order_line:
#             line.inclusive = self.inclusive

#     # @api.model
#     # def create(self, vals):
#     #     _logger.info("🛠️ Creating Purchase Order with vals: %s", vals)
#     #     order = super().create(vals)
#     #     order._auto_set_tax_state()
#     #     return order
#     #
#     # def write(self, vals):
#     #     _logger.info("Writing Purchase Order with vals: %s", vals)
#     #     res = super().write(vals)
#     #     self._auto_set_tax_state()
#     #     return res
#     #
#     # @api.depends('order_line.taxes_id')
#     # def _auto_set_tax_state(self):
#     #     for order in self:
#     #         tax_states = set()
#     #         _logger.info(f"🔍 Checking tax state for PO: {order.name}")
#     #         for line in order.order_line:
#     #             for tax in line.taxes_id:
#     #                 _logger.info(
#     #                     f"   → Line {line.name}, Tax: {tax.name}, price_include_override = {tax.price_include_override}")
#     #                 if tax.price_include_override == 'tax_included':
#     #                     tax_states.add('inclusive')
#     #                 elif tax.price_include_override == 'tax_excluded':
#     #                     tax_states.add('exclusive')
#     #
#     #         new_tax_state = 'exclusive'
#     #         if 'inclusive' in tax_states and 'exclusive' in tax_states:
#     #             new_tax_state = 'exclusive'  # mixed fallback
#     #         elif 'inclusive' in tax_states:
#     #             new_tax_state = 'inclusive'
#     #         elif not tax_states:
#     #             new_tax_state = 'no_tax'
#     #
#     #         _logger.info(f"Final Tax State Decision: {new_tax_state}")
#     #         if order.tax_state != new_tax_state:
#     #             _logger.info(f"Updating tax_state from {order.tax_state} to {new_tax_state}")
#     #             order.tax_state = new_tax_state
#     #
#     #         # Set line.inclusive based on new tax state
#     #         for line in order.order_line:
#     #             if new_tax_state == 'inclusive':
#     #                 line.inclusive = True
#     #             elif new_tax_state == 'exclusive':
#     #                 line.inclusive = False
#     #             else:
#     #                 line.inclusive = False  # safe default for no_tax
#     #
#     # @api.onchange('tax_state', 'inclusive')
#     # def update_inclusive_flag(self):
#     #     for line in self.order_line:
#     #         if self.tax_state == 'inclusive':
#     #             line.inclusive = True
#     #         elif self.tax_state == 'exclusive':
#     #             line.inclusive = False
#     #         elif self.tax_state == 'no_tax':
#     #             line.inclusive = False

#     # @api.model
#     # @api.onchange('tax_state')
#     # def onchange_tax_status(self):
#     #     for line_id in self.order_line:
#     #         if (self.tax_state == 'inclusive'):
#     #             line_id.inclusive = True
#     #         elif (self.tax_state == 'exclusive'):
#     #             line_id.inclusive = False

#     @api.model
#     def prepare_purchaseorder_export_line_dict(self, line):
#         #         line = self
#         company = self.company_id
#         if company:
#             company = self.env['res.users'].search([('id', '=', self.env.uid)], limit=1).company_id
#         line_vals = {}

#         if self.partner_id:
#             if line.tax_ids:
#                 line_tax = self.env['account.tax'].search([('id', '=', line.tax_ids.id),('company_id','=',company.id)])
#                 if line_tax:
#                     tax = line_tax.xero_tax_type_id
#                     if not tax:
#                         self.env['account.tax'].get_xero_tax_ref(line_tax)
#                         line_tax = self.env['account.tax'].search([('id', '=', line.tax_ids.id),('company_id','=',company.id)])
#                         tax = line_tax.xero_tax_type_id

#                     line_vals = {
#                                 'Description': line.name,
#                                 'UnitAmount': line.price_unit,
#                                 'ItemCode': line.product_id.default_code,
#                                 'Quantity': line.product_qty,
#                                 'TaxType': tax,
#                                 "DiscountRate": line.discount,
#                                 }
#             else:
#                 if line.product_id:
#                     line_vals = {
#                         'Description': line.name,
#                         'UnitAmount': line.price_unit,
#                         'ItemCode': line.product_id.default_code,
#                         'Quantity': line.product_qty,
#                         "DiscountRate": line.discount,
#                     }
#                 else:
#                     line_vals = {
#                         'Description': line.name,
#                         "DiscountRate": line.discount
#                         # 'UnitAmount': line.price_unit,
#                         # 'ItemCode': line.product_id.default_code,
#                         # 'Quantity': line.product_qty,
#                     }

#         return line_vals

#     @api.model
#     def prepare_purchaseorder_export_dict(self):
#         company = self.company_id
#         if not company:
#             company = self.env['res.users'].search([('id', '=', self.env.uid)], limit=1).company_id

#         if self.partner_id:
#             cust_id = self.env['res.partner'].get_xero_partner_ref(self.partner_id)

#         vals = {}
#         lst_line = []
#         tax_state = 'Exclusive'
#         if self.tax_state:
#             if self.tax_state == 'inclusive':
#                 tax_state = 'Inclusive'
#             elif self.tax_state == 'exclusive':
#                 tax_state = 'Exclusive'
#             elif self.tax_state == 'no_tax':
#                 tax_state = 'NoTax'

#         if self.state:
#             if self.state == 'draft' or self.state == 'sent':
#                 status = 'DRAFT'
#             elif self.state == 'purchase':
#                 status = 'AUTHORISED'
#             else:
#                 status = 'DRAFT'

#         if self.partner_ref:
#             partner_ref = self.partner_ref
#         else:
#             partner_ref = ''

#         def remove_tags(text):
#             """
#             Removes html test from string
#             :param text:
#             :return: new string
#             """
#             TAG_RE = re.compile(r'<[^>]+>')
#             return TAG_RE.sub('', text)

#         # if self.note:
#         #     notes = remove_tags(self.note)
#         # else:
#         #     notes = ''


#         if len(self.order_line) == 1:
#             single_line = self.order_line

#             if single_line.product_id.xero_product_id:
#                 _logger.info(_("PRODUCT DEFAULT CODE AVAILABLE"))
#             elif not single_line.product_id.xero_product_id:
#                 self.env['product.product'].get_xero_product_ref(single_line.product_id)
#             if single_line.tax_ids:
#                 line_tax = self.env['account.tax'].search([('id', '=', single_line.tax_ids.id),('company_id','=',company.id)])
#                 if line_tax:
#                     tax = line_tax.xero_tax_type_id
#                     # product = self.env['product.template'].get_xero_product_ref(single_line.product_id)
#                     if not tax:
#                         self.env['account.tax'].get_xero_tax_ref(line_tax)
#                         line_tax = self.env['account.tax'].search([('id', '=', single_line.tax_ids.id),('company_id','=',company.id)])
#                         tax = line_tax.xero_tax_type_id

#                     vals.update({
#                         "Contact": {"ContactID": cust_id},
#                         "Date": str(self.date_order),
#                         "PurchaseOrderNumber": self.name,
#                         "DeliveryDate": str(self.date_planned) if self.date_planned else '',
#                         # "DeliveryInstructions":notes,
#                         "Reference": partner_ref,
#                         # "DeliveryAddress":address5,
#                         "LineAmountTypes": tax_state,
#                         "LineItems": [
#                             {
#                                 "ItemCode":single_line.product_id.default_code,
#                                 "Description": single_line.name,
#                                 "Quantity": single_line.product_qty,
#                                 "UnitAmount": single_line.price_unit,
#                                 "TaxType":tax,
#                                 "DiscountRate": single_line.discount,
#                             }
#                         ],
#                         "Status": status,
#                     })
#             else:
#                 vals.update({
#                     "Contact": {"ContactID": cust_id},
#                     "Date": str(self.date_order),
#                     "PurchaseOrderNumber": self.name,
#                     "DeliveryDate": str(self.date_planned) if self.date_planned else '',
#                     # "DeliveryAddress": address5,
#                     # "DeliveryInstructions": notes,
#                     "Reference": partner_ref,
#                     "LineAmountTypes": tax_state,
#                     "LineItems": [
#                         {
#                             "ItemCode": single_line.product_id.default_code,
#                             "Description": single_line.name,
#                             "Quantity": single_line.product_qty,
#                             "UnitAmount": single_line.price_unit,
#                             "DiscountRate": single_line.discount,
#                         }
#                     ],
#                     "Status": status,
#                 })

#         else:
#             for line in self.order_line:

#                 if line.product_id.xero_product_id:
#                     _logger.info(_("PRODUCT DEFAULT CODE AVAILABLE"))
#                 elif not line.product_id.xero_product_id:
#                     self.env['product.product'].get_xero_product_ref(line.product_id)

#                 line_vals = self.prepare_purchaseorder_export_line_dict(line)
#                 lst_line.append(line_vals)
#             vals.update({
#                         "Contact": {"ContactID": cust_id},
#                         "Date": str(self.date_order),
#                         "PurchaseOrderNumber":self.name,
#                         # "DeliveryAddress": address5,
#                         "DeliveryDate": str(self.date_planned) if self.date_planned else '',
#                         "Reference": partner_ref ,
#                         # "DeliveryInstructions": notes,
#                         "LineAmountTypes": tax_state,
#                         "LineItems": lst_line,
#                         "Status": status
#                     })
#         currency = self.currency_id if self.currency_id else False
#         if currency:
#             vals.update({"CurrencyCode": currency.name})
#         return vals

#     def fetchHead(self):
#         if self.env.context.get('cron'):
#             xero_config = self.company_id
#         else:
#             xero_config = self.company_id
#             if not xero_config:
#                 xero_config = self.env['res.users'].search([('id', '=', self.env.uid)], limit=1).company_id
#         client_id = xero_config.xero_client_id
#         client_secret = xero_config.xero_client_secret


#         data = client_id + ":" + client_secret
#         encodedBytes = base64.b64encode(data.encode("utf-8"))
#         encodedStr = str(encodedBytes, "utf-8")
#         headers = {
#             'Authorization': "Bearer " + str(xero_config.xero_oauth_token),
#             'Xero-tenant-id': xero_config.xero_tenant_id,
#             'Accept': 'application/json'

#         }
#         return headers

#     @api.model
#     def exportPurchaseOrder(self):
#         """export purchase order to QBO"""
#         xero_config = self.company_id
#         if not xero_config:
#             xero_config = self.env['res.users'].search([('id', '=', self.env.uid)], limit=1).company_id
#         if self.env.context.get('active_ids'):
#             purchase = self.browse(self.env.context.get('active_ids'))
#         else:
#             purchase = self
#         if purchase and self.env.context.get('not_cron'):
#             xero_config = purchase[0].company_id
#         for t in purchase:
#             if not t.xero_purchase_id:
#                 vals = t.prepare_purchaseorder_export_dict()
#                 parsed_dict = json.dumps(vals)
#                 if xero_config.xero_oauth_token:
#                     token = xero_config.xero_oauth_token
#                 headers = self.fetchHead()
#                 if token:
#                     protected_url = 'https://api.xero.com/api.xro/2.0/PurchaseOrders'
#                     data = requests.request('POST', url=protected_url, data=parsed_dict, headers=headers)
#                     if data.status_code == 200:
#                         response_data = json.loads(data.text)
#                         if response_data.get('PurchaseOrders'):
#                                 t.xero_purchase_id = response_data.get('PurchaseOrders')[0].get('PurchaseOrderID')
#                                 self.env.cr.commit()
#                         _logger.info(_("Exported successfully to XERO"))
#                     elif data.status_code == 400:
#                         logs = self.env['xero.error.log'].create({
#                             'transaction': 'Purchase Order Export',
#                             'xero_error_response': data.text,
#                             'error_date': fields.Datetime.now(),
#                             'record_id': t,
#                         })
#                         self.env.cr.commit()
#                         response_data = json.loads(data.text)
#                         if response_data:
#                             if response_data.get('Elements'):
#                                 for element in response_data.get('Elements'):
#                                     if element.get('ValidationErrors'):
#                                         for err in element.get('ValidationErrors'):
#                                             if err.get('Message'):
#                                                 raise ValidationError('(Purchase Order) Xero Exception : ' + err.get('Message'))
#                             elif response_data.get('Message'):
#                                 raise ValidationError(
#                                     '(Purchase Order) Xero Exception : ' + response_data.get('Message'))
#                             else:
#                                 raise ValidationError(
#                                     '(Purchase Order) Xero Exception : please check xero logs in odoo for more details')
#                     elif data.status_code == 401:
#                         raise ValidationError("Time Out.\nPlease Check Your Connection or error in application or refresh token..!!")
#             else:
#                 vals = t.prepare_purchaseorder_export_dict()
#                 parsed_dict = json.dumps(vals)
#                 if xero_config.xero_oauth_token:
#                     token = xero_config.xero_oauth_token
#                 headers=self.fetchHead()
#                 if token:
#                     protected_url = 'https://api.xero.com/api.xro/2.0/PurchaseOrders/'+t.xero_purchase_id
#                     data = requests.request('POST', url=protected_url, headers=headers, data=parsed_dict)
#                     if data.status_code == 200:
#                             _logger.info(_("Exported successfully to XERO"))
#                     elif data.status_code == 400:
#                         logs = self.env['xero.error.log'].create({
#                             'transaction': 'Purchase Order Export',
#                             'xero_error_response': data.text,
#                             'error_date': fields.Datetime.now(),
#                             'record_id': t,
#                         })
#                         self.env.cr.commit()
#                         response_data = json.loads(data.text)
#                         if response_data:
#                             if response_data.get('Elements'):
#                                 for element in response_data.get('Elements'):
#                                     if element.get('ValidationErrors'):
#                                         for err in element.get('ValidationErrors'):
#                                             if err.get('Message'):
#                                                 raise ValidationError('(Purchase Order) Xero Exception : ' + err.get('Message'))
#                             elif response_data.get('Message'):
#                                 raise ValidationError(
#                                     '(Purchase Order) Xero Exception : ' + response_data.get('Message'))
#                             else:
#                                 raise ValidationError(
#                                     '(Purchase Order) Xero Exception : please check xero logs in odoo for more details')
#                     elif data.status_code == 401:
#                         raise ValidationError("Time Out.\nPlease Check Your Connection or error in application or refresh token..!!")
#         success_form = self.env.ref('rishvi_xero_odoo_connector.export_success_view', False)
#         return {
#             'name': _('Notification'),
#             'type': 'ir.actions.act_window',
#             'view_type': 'form',
#             'view_mode': 'form',
#             'res_model': 'res.company.message',
#             'views': [(success_form.id, 'form')],
#             'view_id': success_form.id,
#             'target': 'new',
#         }

#     @api.model
#     def exportPurchaseOrder_cron(self):
#         # xero_config = self.env['res.users'].search([('id', '=', self.env.uid)], limit=1).company_id
#         _logger.info("Cron for Exporting Purchase Orders to XERO is triggered.")
#         _logger.info("111111111111111111111111111111111111111111111111111111111111111111111111")
#         companys = self.env['res.company'].search([])
#         # self.env.context['cron'] = 1
#         self = self.with_context(cron=1)
#         for xero_config in companys:
#             if xero_config.xero_client_id and xero_config.xero_client_secret:
#                 xero_config.refresh_token()
#                 _logger.info("22222222222222222222222222222222222222222222222222222222222222222222222222222222222")
#                 purchase_id = self.env['purchase.order'].search([('company_id', '=', xero_config.id),('state', '=', 'purchase'),('xero_purchase_id', '=', False)])
#                 for purchase in purchase_id:
#                     _logger.info("333333333333333333333333333333333333333333333333333333333333333")
#                     purchase.exportPurchaseOrder()
#             else:
#                 continue



# class PurchaseOderLine(models.Model):
#     _inherit = 'purchase.order.line'

#     xero_purchase_line_id = fields.Char(string="Xero Id",copy=False)
#     inclusive = fields.Boolean('Inclusive', default=False,copy=False)
