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
from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError


class RoomBookingLine(models.Model):
    _name = "room.booking.line"
    _description = "Hotel Folio Line"
    _rec_name = 'room_id'

    @tools.ormcache()
    def _set_default_uom_id(self):
        return self.env.ref('uom.product_uom_day')

    booking_id = fields.Many2one("room.booking", string="Booking",
                                 help="Indicates the Room",
                                 ondelete="cascade")
    checkin_date = fields.Datetime(string="Check In",
                                   help="You can choose the date,"
                                        " Otherwise sets to current Date",
                                   required=True)
    checkout_date = fields.Datetime(string="Check Out",
                                    help="You can choose the date,"
                                         " Otherwise sets to current Date",
                                    required=True)
    room_id = fields.Many2one('hotel.room', string="Room",
                              domain=[('status', '=', 'available')],
                              help="Indicates the Room",
                              required=True)
    uom_qty = fields.Float(string="Duration",
                           help="The quantity converted into the UoM used by "
                                "the product", readonly=True)
    uom_id = fields.Many2one('uom.uom',
                             default=_set_default_uom_id,
                             string="Unit of Measure",
                             help="This will set the unit of measure used",
                             readonly=True)
    price_unit = fields.Float(related='room_id.list_price', string='Rent',
                              digits='Product Price',
                              help="The rent price of the selected room.")
    tax_ids = fields.Many2many('account.tax',
                               'hotel_room_order_line_taxes_rel',
                               'room_id', 'tax_id',
                               related='room_id.taxes_ids',
                               string='Taxes',
                               help="Default taxes used when selling the room.",
                               domain=[('type_tax_use', '=', 'sale')])
    currency_id = fields.Many2one(string='Currency',
                                  related='booking_id.pricelist_id.currency_id',
                                  help='The currency used')
    price_subtotal = fields.Float(
        string="Subtotal",
        compute='_compute_price_subtotal', help="Total Price excluding Tax",
        store=True)
    price_tax = fields.Float(
        string="Total Tax",
        compute='_compute_price_subtotal', help="Tax Amount",
        store=True)
    price_total = fields.Float(
        string="Total",
        compute='_compute_price_subtotal', help="Total Price including Tax",
        store=True)
    state = fields.Selection(
        related='booking_id.state',
        string="Order Status", help=" Status of the Order",
        copy=False, precompute=True)
    booking_line_visible = fields.Boolean(default=False,
                                          string="Booking Line Visible",
                                          help="If True, then Booking Line will"
                                               " be visible")

    @api.onchange("checkin_date", "checkout_date")
    def _onchange_checkin_date(self):

        if self.checkout_date < self.checkin_date:
            raise ValidationError(
                _("Checkout must be greater or equal checkin date"))
        if self.checkin_date and self.checkout_date:
            diffdate = self.checkout_date - self.checkin_date
            qty = diffdate.days
            if diffdate.total_seconds() > 0:
                qty = qty + 1
            self.uom_qty = qty

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

    @api.onchange('room_id')
    def domain_check(self):

        if self.booking_id.room_type == 'single':
            return {'domain': {'room_id': [('status', '=', 'available'),
                                           ('room_type', '=', 'single')]}}
        elif self.booking_id.room_type == 'double':
            return {'domain': {'room_id': [('status', '=', 'available'),
                                           ('room_type', '=', 'double')]}}
        elif self.booking_id.room_type == 'dormitory':
            return {'domain': {'room_id': [('status', '=', 'available'),
                                           ('room_type', '=', 'dormitory')]}}
        else:
            return {'domain': {'room_id': [('status', '=', 'available')]}}