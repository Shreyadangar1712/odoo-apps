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
from odoo import fields, models


class CleaningTeam(models.Model):
    _name = "cleaning.team"
    _description = "Cleaning Team"

    name = fields.Char(string="Team Name", help="Name of the Team")
    team_head_id = fields.Many2one('res.users', string="Team Head",
                                   help="Choose the Team Head",
                                   domain=lambda self: [
                                       ('groups_id', 'in', self.env.ref(
                                           'rishvi_hotel_management_system.'
                                           'cleaning_team_group_head').id)])
    member_ids = fields.Many2many('res.users', string="Member",
                                  domain=lambda self: [
                                      ('groups_id', 'in', self.env.ref(
                                          'rishvi_hotel_management_system.'
                                          'cleaning_team_group_user').id)],
                                  help="Team Members")
