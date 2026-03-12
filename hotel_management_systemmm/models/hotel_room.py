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


class HotelRoom(models.Model):
    _name = 'hotel.room'
    _description = 'Rooms'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    @tools.ormcache()
    def _get_default_uom_id(self):
        return self.env.ref('uom.product_uom_unit')

    name = fields.Char(string='Name', help="Name of the Room", index='trigram',
                       required=True, translate=True)
    status = fields.Selection([("available", "Available"),
                               ("reserved", "Reserved"),
                               ("occupied", "Occupied")],
                              default="available", string="Status",
                              help="Status of The Room",
                              tracking=True)
    is_room_avail = fields.Boolean(default=True, string="Available",
                                   help="Check if the room is available")
    list_price = fields.Float(string='Rent', digits='Product Price',
                              help="The rent of the room.")
    uom_id = fields.Many2one(
        'uom.uom', string='Unit of Measure',
        default=_get_default_uom_id, required=True,
        help="Default unit of measure used for all stock operations.")
    room_image = fields.Image(string="Room Image", max_width=1920,
                              max_height=1920, help='Image of the room')
    taxes_ids = fields.Many2many('account.tax',
                                 'hotel_room_taxes_rel',
                                 'room_id', 'tax_id',
                                 help="Default taxes used when selling the"
                                      " room.", string='Customer Taxes',
                                 domain=[('type_tax_use', '=', 'sale')],
                                 default=lambda self: self.env.company.
                                 account_sale_tax_id)
    room_amenities_ids = fields.Many2many("hotel.amenity",
                                          string="Room Amenities",
                                          help="List of room amenities.")
    floor_id = fields.Many2one('hotel.floor', string='Floor',
                               help="Automatically selects the Floor",
                               tracking=True)
    user_id = fields.Many2one('res.users', string="User",
                              related='floor_id.user_id',
                              help="Automatically selects the manager",
                              tracking=True)
    room_type = fields.Selection([('single', 'Single'),
                                  ('double', 'Double'),
                                  ('dormitory', 'Dormitory')],
                                 required=True, string="Room Type",
                                 help="Automatically selects the Room Type",
                                 tracking=True,
                                 default="single")
    num_person = fields.Integer(string='Number Of Persons',
                                required=True,
                                help="Automatically chooses the No. of Persons",
                                tracking=True)
    description = fields.Html(string='Description', help="Add description",
                              translate=True)

    @api.constrains("num_person")
    def _check_capacity(self):
        for room in self:
            if room.num_person <= 0:
                raise ValidationError(_("Room capacity must be more than 0"))

    @api.onchange("room_type")
    def _onchange_room_type(self):

        if self.room_type == "single":
            self.num_person = 1
        elif self.room_type == "double":
            self.num_person = 2
        else:
            self.num_person = 4
