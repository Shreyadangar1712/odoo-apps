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
from odoo import fields, models


class HrEmployeePublic(models.Model):
    _inherit = "hr.employee.public"

    barcode = fields.Char(compute="_compute_attendance_public_fields", readonly=True, store=False)
    attendance_policy = fields.Selection(
        [
            ("none", "No Punch Required"),
            ("single", "Single Punch"),
            ("double", "Double Punch"),
        ],
        compute="_compute_attendance_public_fields",
        readonly=True,
        store=False,
    )
    attendance_shift = fields.Selection(
        [
            ("Morning", "Morning"),
            ("Afternoon", "Afternoon"),
            ("Night", "Night"),
        ],
        compute="_compute_attendance_public_fields",
        readonly=True,
        store=False,
    )
    allow_overtime = fields.Boolean(compute="_compute_attendance_public_fields", readonly=True, store=False)
    reason_required = fields.Boolean(compute="_compute_attendance_public_fields", readonly=True, store=False)
   

    def _compute_attendance_public_fields(self):
        self._compute_from_employee([
            "barcode",
            "attendance_policy",
            "attendance_shift",
            "allow_overtime",
            "reason_required",
        ])
