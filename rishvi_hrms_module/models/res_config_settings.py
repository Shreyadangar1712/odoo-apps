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

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # This will allow managing the detention time directly in Settings.
    # We can use a many2many with the hr.employee model to show a list of employees and their detention times.
    # However, since we want a "per-employee configurable deduction", a simpler way is to have a 
    # many2many or just a link to the employee list filtered by those who have a deduction.
    # But to make it truly "in settings", let's use a setting to enable/disable it globally if needed.
    
    hr_attendance_detention_time = fields.Boolean(
        string="Enable Detention Time",
        related='company_id.hr_attendance_detention_time',
        readonly=False,
        help="If enabled, detention time will be deducted from payroll."
    )

    hr_attendance_detention_minutes = fields.Integer(
        string="Detention Minutes",
        related='company_id.hr_attendance_detention_minutes',
        readonly=False,
        help="Global detention time in minutes to be deducted from total worked hours per attendance for all employees."
    )

    def _sync_detention_from_legacy_config(self):
        icp = self.env['ir.config_parameter'].sudo()
        company = self.env.company
        if not company.hr_attendance_detention_time and not company.hr_attendance_detention_minutes:
            company.write({
                'hr_attendance_detention_time': str(
                    icp.get_param('rishvi_hrms_module_v19.hr_attendance_detention_time', 'False')
                ).lower() in ['true', '1'],
                'hr_attendance_detention_minutes': int(
                    icp.get_param('rishvi_hrms_module_v19.hr_attendance_detention_minutes', 0) or 0
                ),
            })

    def action_open_hrms_general_settings(self):
        self._sync_detention_from_legacy_config()
        settings_fields = [
            'company_id',
            'hr_attendance_display_overtime',
            'attendance_overtime_validation',
            'hr_attendance_detention_time',
            'hr_attendance_detention_minutes',
        ]
        settings = self.create(self.default_get(settings_fields))
        form_view = self.env.ref('rishvi_hrms_module_v19.hrms_general_settings_view_form')
        return {
            'type': 'ir.actions.act_window',
            'name': 'Attendance Settings',
            'res_model': 'res.config.settings',
            'view_mode': 'form',
            'views': [(form_view.id, 'form')],
            'target': 'current',
            'res_id': settings.id,
            'context': {
                'module': 'hr_attendance',
                'bin_size': False,
            },
        }

    def set_values(self):
        res = super().set_values()
        icp = self.env['ir.config_parameter'].sudo()
        icp.set_param(
            'rishvi_hrms_module_v19.hr_attendance_detention_time',
            bool(self.hr_attendance_detention_time),
        )
        icp.set_param(
            'rishvi_hrms_module_v19.hr_attendance_detention_minutes',
            int(self.hr_attendance_detention_minutes or 0),
        )
        # Trigger recomputation for all attendance records to reflect NEW deduction settings immediately
        self.env['hr.attendance'].sudo().search([])._compute_custom_hours()
        return res
