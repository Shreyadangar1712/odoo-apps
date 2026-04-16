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
from odoo.exceptions import UserError, ValidationError
from datetime import timedelta
import pytz

class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    attendance_shift = fields.Selection([
        ('Morning', 'Morning'),
        ('Afternoon', 'Afternoon'),
        ('Night', 'Night'),
    ], string="Shift")

    change_shift = fields.Selection([
        ('Morning', 'Morning'),
        ('Afternoon', 'Afternoon'),
        ('Night', 'Night'),
    ], string="Change Shift" )
    form_date = fields.Date(string="Form Date")
    to_date = fields.Date(string="To Date")
    
    custom_worked_hours = fields.Float(string="Worked Hours ", compute="_compute_custom_hours", store=True)
    custom_extra_hours = fields.Float(string="Extra Hours ", compute="_compute_custom_hours", store=True)

    late_minutes = fields.Float(string="Late Minutes", compute="_compute_shift_data", store=True)
    early_minutes = fields.Float(string="Early Leave Minutes", compute="_compute_shift_data", store=True)
    attendance_status = fields.Selection([
        ('present', 'Present'),
        ('late', 'Late'),   
        ('early', 'Early Leave'),
    ], compute="_compute_shift_data", store=True)
    remark = fields.Text(string="Remark")
    reason = fields.Selection(selection="_get_reason_selection", string="Reason")
    
    employee_id_reason_required = fields.Boolean(related='employee_id.reason_required', string="Reason Required (Employee)")
    employee_allow_overtime = fields.Boolean(related='employee_id.allow_overtime', string="Allow Overtime (Employee)")

    @api.model
    def _get_reason_selection(self):
        return self.env['hr.reason'].get_selection()
    
    @api.depends('worked_hours')
    def _compute_custom_hours(self):
        for rec in self:
            # Only handle 8-hour capping here. 
            # Global deduction is applied once in the payslip as per user request.
            hours = rec.worked_hours or 0.0
            if hours > 8.0:
                rec.custom_worked_hours = 8.0
                rec.custom_extra_hours = hours - 8.0
            else:
                rec.custom_worked_hours = hours
                rec.custom_extra_hours = 0.0
                
    @api.depends('check_in', 'check_out', 'attendance_shift', 'employee_id.attendance_shift')
    def _compute_shift_data(self):
        # --- OPTIMIZATION: Pre-fetch shifts to avoid N+1 queries ---
        shift_names = set()
        for rec in self:
            s_name = rec.attendance_shift or rec.employee_id.attendance_shift
            if s_name:
                shift_names.add(s_name)
        
        shift_dict = {}
        if shift_names:
            shifts = self.env['hr.shift'].search([('name', 'in', list(shift_names))])
            shift_dict = {s.name: s for s in shifts}

        for rec in self:
            rec.late_minutes = 0
            rec.early_minutes = 0
            rec.attendance_status = 'present'

            # Fallback logic
            shift_name = rec.attendance_shift or rec.employee_id.attendance_shift
            if not shift_name or not rec.check_in:
                continue

            # Find the master shift record by name from prefetched dict
            shift = shift_dict.get(shift_name)
            if not shift:
                continue

            tz_name = rec.employee_id.tz or self.env.user.tz or 'UTC'
            try:
                tz = pytz.timezone(tz_name)
            except Exception:
                tz = pytz.UTC

            check_in_local = pytz.UTC.localize(rec.check_in).astimezone(tz)

            # Ensure shift.start and shift.end are floats as defined in hr_shift
            shift_start_local = check_in_local.replace(
                hour=int(shift.start),
                minute=int((shift.start % 1) * 60),
                second=0,
                microsecond=0
            )

            shift_end_local = check_in_local.replace(
                hour=int(shift.end),
                minute=int((shift.end % 1) * 60),
                second=0,
                microsecond=0
            )

            # Night shift adjustment
            if shift.end < shift.start:
                shift_end_local += timedelta(days=1)

            # Late Calculation
            grace = timedelta(minutes=shift.grace_time)
            if check_in_local > (shift_start_local + grace):
                late = (check_in_local - shift_start_local).total_seconds() / 60.0
                rec.late_minutes = late
                rec.attendance_status = 'late'

            # Early Leave
            if rec.check_out:
                check_out_local = pytz.UTC.localize(rec.check_out).astimezone(tz)
                if check_out_local < shift_end_local:
                    early = (shift_end_local - check_out_local).total_seconds() / 60.0
                    rec.early_minutes = early
                    if rec.attendance_status != 'late':
                        rec.attendance_status = 'early'


    @api.model
    def _create_or_update_attendance(self):
        employee = self.env.user.employee_id

        if not employee:
            raise UserError(_("Employee not linked with user."))

        policy = employee.attendance_policy

        # LEVEL 1 → No Punch
        if policy == 'none':
            raise UserError(_("Attendance not required for your level."))

        # LEVEL 2 → Single Punch (Auto Close Previous)
        if policy == 'single':
            open_attendance = self.search([
                ('employee_id', '=', employee.id),
                ('check_out', '=', False),
            ], limit=1)

            if open_attendance:
                open_attendance.check_out = fields.Datetime.now()

            return self.with_context(single_punch_bypass=True).create({
                'employee_id': employee.id,
                'check_in': fields.Datetime.now(),
            })

        # LEVEL 3 → Default (Double Punch)
        return super()._create_or_update_attendance()

    @api.constrains('check_in', 'check_out', 'employee_id')
    def _check_validity(self):
        # Bypass validation if the employee's attendance policy is 'single' or 'none'.
        # For 'double' policy, Odoo's default strict validation applies.
        for attendance in self:
            if attendance.employee_id.attendance_policy in ['single', 'none']:
                return # Bypass validation
        super()._check_validity() # Call original validation for other policies (i.e., 'double')

    @api.constrains('remark', 'employee_id', 'check_out', 'reason')
    def _check_remark(self):
        if self.env.context.get('skip_reason_validation'):
            return
        for rec in self:
            # Enforce reason only on check-out; check-in should not be blocked.
            if rec.check_out and rec.employee_id.reason_required and not rec.reason:
                raise UserError(_("A reason is required for this employee's attendance."))

    @api.constrains('check_in', 'check_out')
    def _check_maximum_work_duration(self):
        max_duration = timedelta(hours=48)
        for rec in self:
            if not rec.check_in or not rec.check_out:
                continue
            if rec.check_out - rec.check_in > max_duration:
                raise ValidationError(
                    _("Check-out cannot be more than 48 hours after check-in.")
                )

    @api.model
    def _cron_auto_check_out_single_punch(self):
        now = fields.Datetime.now()
        eight_hours_ago = now - timedelta(hours=8)

        # Close any open attendance that crossed 8 hours from check-in.
        attendances_to_auto_checkout = self.search([
            ('check_out', '=', False),
            ('check_in', '<=', eight_hours_ago),
        ])

        for attendance in attendances_to_auto_checkout:
            auto_checkout_time = attendance.check_in + timedelta(hours=8)
            vals = {'check_out': auto_checkout_time}
            if 'out_mode' in attendance._fields:
                vals['out_mode'] = 'auto_check_out'
            attendance.with_context(skip_reason_validation=True).write(vals)
            attendance.message_post(body=_("Automatically checked out after 8 hours from check-in."))

        return True

    @api.model
    def _cron_auto_check_out(self):
        """Keep Odoo's default behavior and also enforce strict 8-hour auto check-out."""
        result = super()._cron_auto_check_out()
        self._cron_auto_check_out_single_punch()
        return result

    def action_open_current_month_preview(self):
        return self.env['hr.attendance.manager.monthly.report'].action_open_filter_report()
