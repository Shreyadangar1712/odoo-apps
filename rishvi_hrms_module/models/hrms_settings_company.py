# -*- coding: utf-8 -*-
########################################################################
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
########################################################################
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    attendance_alert_recipient_selection = [
        ('hr', 'HR'),
        ('manager', 'Manager'),
        ('both', 'HR and Manager'),
    ]

    birthday_spotlight_photo = fields.Binary(string="Snapshot Photo")
    birthday_spotlight_text = fields.Text(
        string="Spotlight Message",
        default="Wishing you a very Happy Birthday! Hope you have a wonderful day and a great year ahead.",
    )
    birthday_spotlight_role = fields.Char(string="Spotlight Role", default="Best Employee")
    birthday_header_icon = fields.Binary(string="Birthday Header Icon")
    birthday_send_to_all_today = fields.Boolean(
        string="Send To All Employee Birthday Mail",
        default=False,
    )
    absent_reminder_send_to_all = fields.Boolean(
        string="Send To All Employee Absent Reminder Mail",
        default=False,
    )
    late_coming_notification_enabled = fields.Boolean(
        string="Enable Late Coming Notification",
        default=False,
    )
    late_coming_send_to_all = fields.Boolean(
        string="Send Late Coming Alert To All Employees",
        default=True,
    )
    late_coming_employee_ids = fields.Many2many(
        'hr.employee',
        'res_company_late_coming_employee_rel',
        'company_id',
        'employee_id',
        string="Late Coming Employees",
    )
    late_coming_recipient = fields.Selection(
        attendance_alert_recipient_selection,
        string="Late Coming Send To",
        default='hr',
    )
    early_going_notification_enabled = fields.Boolean(
        string="Enable Early Going Notification",
        default=False,
    )
    early_going_send_to_all = fields.Boolean(
        string="Send Early Going Alert To All Employees",
        default=True,
    )
    early_going_employee_ids = fields.Many2many(
        'hr.employee',
        'res_company_early_going_employee_rel',
        'company_id',
        'employee_id',
        string="Early Going Employees",
    )
    early_going_recipient = fields.Selection(
        attendance_alert_recipient_selection,
        string="Early Going Send To",
        default='hr',
    )
