from odoo import fields,models

class DeliveryNote(models.Model):
    _name = 'delivery.note'

    sale_id = fields.Many2one(
        'sale.order',
        string='Sale Order'
    )

    carrier_id = fields.Many2one(
        'delivery.carrier',
        string='Carrier',
        related='sale_id.carrier_id',
        store=True,
        readonly=False,
    )