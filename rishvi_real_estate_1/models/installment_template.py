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

class installment_template(models.Model):
    _name = "installment.template"
    _description = "Installment Template"
    _inherit = ['mail.thread']

    name= fields.Char('Name', size=64, required=True)
    duration_month= fields.Integer('Month')        
    duration_year= fields.Integer('Year')        
    annual_raise= fields.Integer('Annual Raise %')        
    repetition_rate= fields.Integer('Repetition Rate (month)', default=1)        
    adv_payment_rate= fields.Integer('Advance Payment %')        
    deduct= fields.Boolean('Deducted from amount?')
    note= fields.Html('Note')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
