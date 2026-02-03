# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.osv import expression
from odoo.tools import float_compare, float_is_zero


class SaleOrderLine(models.Model):                                                                                                                                                                                                                                                                                                     
    _inherit = "sale.order.line"

    to_delivery_qty = fields.Integer(string="Qty To Deliver")
    to_dropship_qty = fields.Integer(string="Qty To Dropship")
    split_stock_purchase = fields.Boolean(
        related="warehouse_id.split_stock_purchase",
        store=True,
        readonly=True
    )

    @api.onchange('product_template_id','product_id','product_uom_qty')
    def _onchange_product_uom_qty(self):
        # Get the available stock of the product
        available_qty = self.product_id.qty_available or self.product_template_id.qty_available
        print("available_qty",available_qty)

        # If the requested quantity exceeds the available stock
        if self.product_uom_qty > available_qty:
            self.to_delivery_qty = available_qty  # Deliver only the available quantity
            self.to_dropship_qty = self.product_uom_qty - available_qty  # The rest goes to dropship
        else:
            self.to_delivery_qty = self.product_uom_qty  # Deliver the full quantity
            self.to_dropship_qty = 0  # No dropshipping required


