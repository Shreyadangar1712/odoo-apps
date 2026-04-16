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
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class HrTimeinfo(models.Model):
    _inherit = 'hr.leave'

    reason = fields.Selection(selection="_get_reason_selection", string="Reason")
    remark = fields.Text(string="Remark")

    @api.model
    def _get_reason_selection(self):
        return self.env['hr.reason'].get_selection()

    @api.constrains('reason', 'employee_id')
    def _check_remark(self):
        for rec in self:
            if rec.employee_id.reason_required and not rec.reason:
                raise UserError(_("A reason is required for this employee's time off request."))
