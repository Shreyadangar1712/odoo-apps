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

from odoo import fields, models
from odoo.exceptions import ValidationError

class HrShift(models.Model):
    _name = 'hr.shift'
    _description = 'Employee Shift'

    _rec_name = 'name'

    # shift_id = fields.Many2one('hr.employee', string="Employee")
    name = fields.Selection([
        ('Morning', 'Morning'),
        ('Afternoon', 'Afternoon'),
        ('Night', 'Night')
    ], string="Shift", required=True)
    start = fields.Float(string="Start Time", required=True)
    end = fields.Float(string="End Time", required=True)
    start_time_display = fields.Char(
        string="Start Time",
        compute="_compute_time_display",
        inverse="_inverse_start_time_display",
    )
    end_time_display = fields.Char(
        string="End Time",
        compute="_compute_time_display",
        inverse="_inverse_end_time_display",
    )
    grace_time = fields.Integer(string="Grace Time (Minutes)")
    is_night_shift = fields.Boolean(string="Night Shift")

    def _compute_time_display(self):
        for rec in self:
            rec.start_time_display = rec._format_time_12h(rec.start)
            rec.end_time_display = rec._format_time_12h(rec.end)

    def _inverse_start_time_display(self):
        for rec in self:
            rec.start = rec._parse_time_value(rec.start_time_display, rec.start)

    def _inverse_end_time_display(self):
        for rec in self:
            rec.end = rec._parse_time_value(rec.end_time_display, rec.end)

    def _format_time_12h(self, value):
        if value is False and value != 0:
            return False
        total_minutes = int(round((value or 0.0) * 60))
        total_minutes %= 24 * 60
        hours, minutes = divmod(total_minutes, 60)
        suffix = 'AM' if hours < 12 else 'PM'
        display_hours = hours % 12 or 12
        return f'{display_hours:02d}:{minutes:02d} {suffix}'

    def _parse_time_value(self, value, fallback):
        if not value:
            return fallback
        cleaned = value.strip().upper()
        twelve_hour_match = re.fullmatch(r'(\d{1,2})(?::(\d{2}))?\s*(AM|PM)', cleaned)
        if twelve_hour_match:
            hours = int(twelve_hour_match.group(1))
            minutes = int(twelve_hour_match.group(2) or 0)
            suffix = twelve_hour_match.group(3)
            if hours < 1 or hours > 12 or minutes > 59:
                raise ValidationError("Please enter time like 09:00 AM or 05:00 PM.")
            hours = hours % 12
            if suffix == 'PM':
                hours += 12
            return hours + (minutes / 60.0)

        twenty_four_match = re.fullmatch(r'(\d{1,2})(?::(\d{2}))?', cleaned)
        if twenty_four_match:
            hours = int(twenty_four_match.group(1))
            minutes = int(twenty_four_match.group(2) or 0)
            if hours > 23 or minutes > 59:
                raise ValidationError("Please enter valid time.")
            return hours + (minutes / 60.0)

        raise ValidationError("Please enter time like 09:00 AM or 05:00 PM.")
