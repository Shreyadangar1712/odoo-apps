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
from odoo import models, fields

class HrEmployee(models.Model):
    _inherit = "hr.employee"

    attendance_policy = fields.Selection([
        ('none', 'No Punch Required'),
        ('single', 'Single Punch'),
        ('double', 'Double Punch'),
    ], default='double', string="Attendance Policy")

    attendance_shift = fields.Selection([
        ('Morning', 'Morning'),
        ('Afternoon', 'Afternoon'),
        ('Night', 'Night'),
    ], string="Shift")

    allow_overtime = fields.Boolean(
        string="Allow Overtime (OT)",
        default=False,
        help="If checked, extra hours (overtime) will be paid on the payslip. "
             "If unchecked, overtime hours are not paid (e.g. Group B policy)."
    )

    reason_required = fields.Boolean(
        string="Reason Required",
        default=False,
        help="If checked, the employee must provide a reason when checking out or taking leave."
    )

    