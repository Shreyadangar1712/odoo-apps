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
from odoo import api, fields, models

class account_voucher(models.Model):
    _inherit = "account.payment"

    reservation_id=  fields.Many2one('unit.reservation','Reservation')
    real_estate_ref= fields.Char('Real Estate Ref.')
    ownership_line_id= fields.Many2one('loan.line.rs.own','Ownership Installment')
    rental_line_id= fields.Many2one('loan.line.rs.rent','Rental Contract Installment')

class account_move(models.Model):
    _inherit = "account.move"

    real_estate_ref = fields.Char('Real Estate Ref.')
    ownership_line_id = fields.Many2one('loan.line.rs.own', 'Ownership Installment')
    rental_line_id = fields.Many2one('loan.line.rs.rent', 'Rental Contract Installment')
    property_owner_id = fields.Many2one('res.partner', string="Owner")

class account_move_line(models.Model):
    _inherit = "account.move.line"
    commissioned= fields.Boolean('Commissioned')