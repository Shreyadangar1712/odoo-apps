# -*- coding: utf-8 -*-
########################################################################
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

{
    'name': 'Employee Shift & Attendance Management (HRMS)',
    'version': '19.0.1',
    'category': 'Human Resources',
    'summary': 'Shift based attendance with day and night support',
    'description': """
    HRMS Shift Attendance is a module that provides shift based attendance with day and night support.,
    It includes features like shift management, attendance tracking, leave management, expense management, and more.
    With Birthday and Absent Reminder and Eraly Leaving Reminder Email Notification also Attendance Manager Monthly Report.
    """,
    'author':'Rishvi Ltd',
    'company': 'Rishvi Ltd',
    'maintainer': 'Rishvi Ltd',
    'website': 'https://www.rishvi.co.uk/',
    'license': 'LGPL-3',
    'depends': ['base', 'hr', 'hr_attendance', 'hr_expense', 'hr_holidays'],
    'data': [
        'data/attendance_cron.xml',
        'data/hr_reason_data.xml',
        'data/hr_shift_data.xml',
        'security/hrms_settings_security.xml',
        'security/ir.model.access.csv',
        'data/birthday_template_data.xml',
        'data/absent_reminder_template.xml',
        'data/attendance_alert_templates.xml',
        'views/hrms_settings_views.xml',
        'views/shift_view.xml',
        'views/reason_view.xml',
        'views/hr_expense_views.xml',
        'views/attendance_view.xml',
        'views/attendance_manager_monthly_report_views.xml',
        'views/hr_timeinfo.xml',
        'views/employee_form.xml',
        'report/attendance_manager_monthly_report.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'rishvi_hrms_module_v19/static/src/scss/attendance_manager_monthly_report.scss',
        ],
    },
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': True,
    "price": 100.0,
    "currency": "EUR",
}
