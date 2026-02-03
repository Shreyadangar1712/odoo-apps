from odoo import models, fields

class ProductProperty(models.Model):
    _name = 'product.property'
    _description = 'Product Extended Property'

    key = fields.Char(string='Property Key', required=True)
    value = fields.Char(string='Property Value', required=True)
    product_id = fields.Many2one('product.template', string='Product', required=True)

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    extended_properties = fields.One2many(
        'product.property',
        'product_id',         # Reverse relationship field
        string='Extended Properties',
    )

 