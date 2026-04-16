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
import re

from odoo import api, fields, models


class HrReason(models.Model):
    _name = "hr.reason"
    _description = "Attendance/Leave Reason"
    _order = "name"

    code = fields.Char(string="Code", required=True, copy=False, index=True)
    name = fields.Char(string="Reason", required=True)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('hr_reason_code_uniq', 'unique(code)', 'Reason code must be unique.'),
    ]

    def _generate_code(self, name):
        base = re.sub(r'[^a-z0-9]+', '_', (name or '').strip().lower()).strip('_') or 'reason'
        code = base
        seq = 1
        while self.search_count([('code', '=', code)]):
            seq += 1
            code = f"{base}_{seq}"
        return code

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('code'):
                vals['code'] = self._generate_code(vals.get('name'))
        return super().create(vals_list)

    @api.model
    def get_selection(self):
        reasons = self.search([('active', '=', True)])
        return [(rec.code or f"reason_{rec.id}", rec.name) for rec in reasons]
