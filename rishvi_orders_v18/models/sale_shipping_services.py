# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools.misc import get_lang


class PosShippingServices(models.Model):
    _name = 'sale.shipping.services'
    _description = 'Sale Shipping Services'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = "postal_service_name"


    service_id = fields.Char(string='Service ID', required=True)
    postal_service_name = fields.Char(string='Postal Service Name', required=True)
    service_country = fields.Many2one('res.country', string='Service Country')
    vendor_id = fields.Many2one('res.partner', string='Vendor')
    amount = fields.Monetary(string='Amount', currency_field='currency_id', readonly=False, store=True)
    currency_id = fields.Many2one('res.currency', string='Currency', related='vendor_id.currency_id', readonly=True)
    active = fields.Boolean(string='Active', default=True)

