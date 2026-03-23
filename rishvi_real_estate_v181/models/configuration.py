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

class real_estate_setings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    reservation_hours= fields.Integer(string='Hours to release units reservation',
                                              config_parameter='rishvi_real_estate.reservation_hours')

    penalty_percent= fields.Integer('Penalty Percentage')
    penalty_account= fields.Many2one('account.account',
                                             'Late Payments Penalty Account',
                                             config_parameter='rishvi_real_estate.penalty_account')
    discount_account= fields.Many2one('account.account',
                                              'Discount Account',
                                              config_parameter='rishvi_real_estate.discount_account')
    income_account= fields.Many2one('account.account',
                                            'Income Account',
                                            config_parameter='rishvi_real_estate.income_account')
    me_account= fields.Many2one('account.account',
                                        'Managerial Expenses Account',
                                        config_parameter='rishvi_real_estate.me_account')
    analytic_account= fields.Many2one('account.analytic.account',
                                              'Analytic Account',
                                              config_parameter='rishvi_real_estate.analytic_account')
    security_deposit_account= fields.Many2one('account.account',
                                                      'Security Deposit Account',
                                                      config_parameter='rishvi_real_estate.security_deposit_account')

    revenue_account= fields.Many2one('account.account',
                                                      'Revenue Account',
                                                      config_parameter='rishvi_real_estate.revenue_account')

class Config(models.TransientModel):
    _name = 'gmap.config'

    @api.model
    def get_key_api(self):
        return self.env['ir.config_parameter'].sudo().get_param('google_maps_api_key')