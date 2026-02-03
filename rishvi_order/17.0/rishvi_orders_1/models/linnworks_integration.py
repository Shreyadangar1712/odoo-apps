from odoo import models, fields, api, _
from odoo.exceptions import UserError
import requests
import logging
from datetime import datetime

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    linnworks_order_id = fields.Char('Linnworks Order ID', copy=False, index=True)
    linn_order_number = fields.Char('Linnworks Order Number', copy=False, index=True)
    linnworks_other_charges = fields.Monetary('Linnworks Other Charges', currency_field='currency_id', help="Difference between expected and actual total from Linnworks.")


class ResPartner(models.Model):
    _inherit = 'res.partner'

    linnworks_customer_uid = fields.Char("Linnworks Customer ID", copy=False, index=True)
