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
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class CleaningRequest(models.Model):
    _name = "cleaning.request"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "sequence"
    _description = "Cleaning Request"

    sequence = fields.Char(string="Sequence", readonly=True, default='New',
                           copy=False, tracking=True,
                           help="Sequence for identifying the request")
    state = fields.Selection([('draft', 'Draft'),
                              ('assign', 'Assigned'),
                              ('ongoing', 'Cleaning'),
                              ('support', 'Waiting For Support'),
                              ('done', 'Completed')],
                             string="State",
                             default='draft', help="State of cleaning request")
    cleaning_type = fields.Selection(selection=[('room', 'Room'),
                                                ('hotel', 'Hotel'),
                                                ('vehicle', 'Vehicle')],
                                     required=True, tracking=True,
                                     string="Cleaning Type",
                                     help="Choose what is to be cleaned")
    room_id = fields.Many2one('hotel.room', string="Room",
                              help="Choose the room")
    hotel = fields.Char(string="Hotel", help="cleaning request space in hotel")
    vehicle_id = fields.Many2one('fleet.vehicle.model',
                                 string="Vehicle",
                                 help="Cleaning request from vehicle")
    support_team_ids = fields.Many2many('res.users',
                                        string="Support Team",
                                        help="Support team members")
    support_reason = fields.Char(string='Support', help="Support Reason")
    description = fields.Char(string="Description",
                              help="Description about the cleaning")
    team_id = fields.Many2one('cleaning.team', string="Team",
                              required=True,
                              tracking=True,
                              help="Choose the team")
    head_id = fields.Many2one('res.users', string="Head",
                              related='team_id.team_head_id',
                              help="Head of cleaning team")
    assigned_id = fields.Many2one('res.users', string="Assigned To",
                                  help="The team member to whom the request is "
                                       "Assigned To")
    domain_partner_ids = fields.Many2many('res.partner',
                                          string="Domain Partner",
                                          help="Choose the Domain Partner")

    @api.model
    def create(self, vals_list):
        if vals_list.get('sequence', 'New') == 'New':
            vals_list['sequence'] = self.env['ir.sequence'].next_by_code(
                'cleaning.request')
        return super().create(vals_list)

    @api.onchange('team_id')
    def _onchange_team_id(self):
        self.update(
            {'domain_partner_ids': self.team_id.member_ids.ids})

    def action_assign_cleaning(self):
        self.update({'state': 'assign'})

    def action_start_cleaning(self):
        self.write({'state': 'ongoing'})

    def action_done_cleaning(self):
        self.write({'state': 'done'})

    def action_assign_support(self):
        if self.support_reason:
            self.write({'state': 'support'})
        else:
            raise ValidationError(_('Please enter the reason'))

    def action_assign_assign_support(self):
        if self.support_team_ids:
            self.write({'state': 'ongoing'})
        else:
            raise ValidationError(_('Please choose a support'))

    def action_maintain_request(self):
        self.env['maintenance.request'].sudo().create({
            'date': fields.Date.today(),
            'state': 'draft',
            'type': self.cleaning_type,
            'vehicle_maintenance_id': self.vehicle_id.id
        })
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success',
                'message': "Maintenance Request Sent Successfully",
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }
