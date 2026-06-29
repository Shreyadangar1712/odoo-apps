from odoo import models, fields,api


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"
     

    stream_weight = fields.Float(
        string="Weight",
        store=True
    )

   

    stream_stock_location_id = fields.Many2one(
        "stream.depot",
        string="Stock Location"
    )

    stream_on_hand = fields.Float(
        string="On Hand"
    )

    stream_status = fields.Selection([
        ("draft", "Draft"),
        ("done", "Done")
    ], string="Status")


    stream_cube = fields.Float(
        string="Cube",
        compute="_compute_stream_cube",
        store=True,
    )

    @api.depends('product_id')
    def _compute_stream_cube(self):
        for line in self:
            line.stream_cube = line.product_id.product_tmpl_id.volume or 0.0