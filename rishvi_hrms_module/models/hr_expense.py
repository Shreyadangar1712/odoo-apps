# -*- coding: utf-8 -*-
##########################################################################
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
from odoo.exceptions import ValidationError


class HrExpense(models.Model):
    _inherit = 'hr.expense'

    travel_date_to = fields.Date(string="Expense End Date", required=True, tracking=True)
    travel_mode = fields.Selection(
        [
            ('air', 'By Air'),
            ('road', 'By Road'),
        ],
        string="Mode",
        required=True,
        tracking=True,
    )
    fixed_kilometer_distance = fields.Float(
        string="Fixed Kilometer Distance",
        required=True,
        tracking=True,
    )
    maximum_amount = fields.Monetary(
        string="Maximum Amount",
        currency_field='company_currency_id',
        required=True,
        tracking=True,
    )

    @api.constrains('date', 'travel_date_to')
    def _check_travel_dates(self):
        for expense in self:
            if expense.date and expense.travel_date_to and expense.date > expense.travel_date_to:
                raise ValidationError("To Date must be greater than or equal to From Date.")

    @api.constrains('fixed_kilometer_distance', 'maximum_amount')
    def _check_expense_travel_values(self):
        for expense in self:
            if expense.fixed_kilometer_distance < 0:
                raise ValidationError("Fixed Kilometer Distance must be zero or greater.")
            if expense.maximum_amount < 0:
                raise ValidationError("Maximum Amount must be zero or greater.")
