from odoo import models, fields, api, exceptions ,_

class PriceLists(models.Model):
    _inherit = 'product.pricelist'