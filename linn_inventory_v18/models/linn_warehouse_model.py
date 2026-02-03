from odoo import models, fields, api

class WarehouseSync(models.Model):
    _inherit = "stock.warehouse"

    # 🆕 Custom fields for Linn API sync
    linnexternal_id = fields.Char(string="Linn External ID", index=True)
    linn_is_fulfillment = fields.Boolean(string="Linn Is Fulfillment Center")
    linn_available = fields.Boolean(string="Linn Available")