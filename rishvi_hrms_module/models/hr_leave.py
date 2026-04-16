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
import logging

from odoo import fields, models


_logger = logging.getLogger(__name__)


class HrLeave(models.Model):
    _inherit = 'hr.leave'

    def action_approve(self, check_state=True):
        result = super().action_approve(check_state=check_state)

        approved_leaves = self.filtered(lambda leave: leave.state in ('validate', 'validate1') and leave.employee_id.work_email)
        if not approved_leaves:
            return result

        today = fields.Date.context_today(self)
        settings_model = self.env['res.config.settings']
        date_start, date_end = settings_model._get_month_range(today.year, today.month)
        month_name = settings_model._get_month_label(today.month)

        for employee in approved_leaves.mapped('employee_id'):
            settings_model._send_absent_reminder_emails(
                employee,
                date_start,
                date_end,
                month_name,
                today.year,
                require_leave=False,
                log_prefix="LEAVE APPROVAL: ",
            )
            _logger.info("LEAVE APPROVAL: Triggered current-month absence reminder for %s", employee.name)

        return result
