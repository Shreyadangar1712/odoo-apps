# -*- coding: utf-8 -*-
#############################################################################
#
#    Rishvi Pvt Ltd
#
#    Copyright (C) 2025-TODAY Rishvi Pvt Ltd (<https://www.rishvi.com>)
#    Author: Rishvi Development Team (<https://www.rishvi.com>)
#
#    This software is proprietary and confidential.
#
#    Unauthorized copying, modification, distribution, or use of this
#    software, via any medium, is strictly prohibited without the prior
#    written permission of Rishvi Pvt Ltd.
#
#    This software is licensed, not sold. A valid commercial license
#    from Rishvi Pvt Ltd is required to use this software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
#    OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
#    NON-INFRINGEMENT.
#
#    For licensing information, contact: support@rishvi.com
#
##########################################################################
from odoo import api, fields, models, tools


class FleetBookingLine(models.Model):
    _name = "fleet.booking.line"
    _description = "Hotel Fleet Line"
    _rec_name = 'fleet_id'

    @tools.ormcache()
    def _get_default_uom_id(self):
        return self.env.ref('uom.product_uom_km')

    booking_id = fields.Many2one("room.booking", string="Booking",
                                 ondelete="cascade",
                                 help="Shows the room Booking")
    fleet_id = fields.Many2one('fleet.vehicle.model',
                               string="Vehicle",
                               help='Indicates the Vehicle')
    description = fields.Char(string='Description',
                              related='fleet_id.display_name',
                              help="Description of Vehicle")
    uom_qty = fields.Float(string="Total KM", default=1,
                           help="The quantity converted into the UoM used by "
                                "the product")
    uom_id = fields.Many2one('uom.uom', readonly=True,
                             string="Unit of Measure",
                             default=_get_default_uom_id, help="This will set "
                                                               "the unit of"
                                                               " measure used")
    price_unit = fields.Float(string='Rent/KM', related='fleet_id.price_per_km',
                              digits='Product Price',
                              help="The rent/km of the selected fleet.")
    tax_ids = fields.Many2many('account.tax',
                               'hotel_fleet_order_line_taxes_rel',
                               'fleet_id',
                               'tax_id', string='Taxes',
                               help="Default taxes used when renting the fleet "
                                    "models.",
                               domain=[('type_tax_use', '=', 'sale')])
    currency_id = fields.Many2one(
        related='booking_id.pricelist_id.currency_id',
        string="Currency",
        help='The currency used')
    price_subtotal = fields.Float(
        string="Subtotal",
        compute='_compute_price_subtotal', help="Total price excluding tax",
        store=True)
    price_tax = fields.Float(
        string="Total Tax",
        compute='_compute_price_subtotal', help="Total tax amount",
        store=True)
    price_total = fields.Float(
        string="Total",
        compute='_compute_price_subtotal',
        help="Total Price Including Tax",
        store=True)
    state = fields.Selection(
        related='booking_id.state',
        string="Order Status",
        help=" Status of the Order",
        copy=False)

    @api.depends('uom_qty', 'price_unit', 'tax_ids')
    def _compute_price_subtotal(self):

        for line in self:
            tax_results = self.env['account.tax']._compute_taxes(
                [line._convert_to_tax_base_line_dict()])
            totals = list(tax_results['totals'].values())[0]
            amount_untaxed = totals['amount_untaxed']
            amount_tax = totals['amount_tax']
            line.update({
                'price_subtotal': amount_untaxed,
                'price_tax': amount_tax,
                'price_total': amount_untaxed + amount_tax,
            })
            if self.env.context.get('import_file',
                                    False) and not self.env.user. \
                    user_has_groups('account.group_account_manager'):
                line.tax_id.invalidate_recordset(
                    ['invoice_repartition_line_ids'])

    def _convert_to_tax_base_line_dict(self):
        self.ensure_one()
        return self.env['account.tax']._convert_to_tax_base_line_dict(
            self,
            partner=self.booking_id.partner_id,
            currency=self.currency_id,
            taxes=self.tax_ids,
            price_unit=self.price_unit,
            quantity=self.uom_qty,
            price_subtotal=self.price_subtotal,
        )

    def search_available_vehicle(self):
        return (self.env['fleet.vehicle.model'].search(
            [('id', 'in', self.search([]).mapped('fleet_id').ids)]).ids)
