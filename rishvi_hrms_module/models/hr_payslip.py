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
from datetime import datetime, timedelta

from odoo import api, fields, models
from odoo.tools import float_round

try:
    import pytz
except ImportError:
    pytz = None


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    attendance_worked_hours = fields.Float(
        string='Attendance Worked Hours',
        compute='_compute_attendance_worked_hours',
        store=True,
        help='Total worked hours from attendance (check-in/check-out) in the payslip period.'
    )
    attendance_extra_hours = fields.Float(
        string='Attendance Extra Hours',
        compute='_compute_attendance_worked_hours',
        store=True,
        help='Extra hours beyond 8h per attendance in the payslip period.'
    )

    @api.depends('employee_id', 'date_from', 'date_to')
    def _compute_attendance_worked_hours(self):
        icp = self.env['ir.config_parameter'].sudo()
        global_is_enabled = str(
            icp.get_param('rishvi_hrms_module_v19.hr_attendance_detention_time', 'False')
        ).lower() in ['true', '1']
        global_deduction_minutes = int(
            icp.get_param('rishvi_hrms_module_v19.hr_attendance_detention_minute s', 0) or 0
        )

        for slip in self:
            if not slip.employee_id or not slip.date_from or not slip.date_to:
                slip.attendance_worked_hours = 0.0
                slip.attendance_extra_hours = 0.0
                continue
            # Apply per-attendance payroll deduction configured on employee.
            date_from_dt = fields.Datetime.start_of(slip.date_from, 'day')
            date_to_dt = fields.Datetime.end_of(slip.date_to, 'day')
            attendances = self.env['hr.attendance'].search([
                ('employee_id', '=', slip.employee_id.id),
                ('check_in', '>=', date_from_dt),
                ('check_in', '<=', date_to_dt),
                ('check_out', '!=', False),
            ])
            # Sum up pre-calculated hours from attendance (which now only handle 8h capping)
            total_custom = sum(attendances.mapped('custom_worked_hours'))
            extra = sum(attendances.mapped('custom_extra_hours'))
            
            # Fetch global deduction from company settings, with legacy config fallback.
            company = slip.company_id or slip.employee_id.company_id or self.env.company
            is_enabled = company.hr_attendance_detention_time
            deduction_minutes = company.hr_attendance_detention_minutes
            if not is_enabled and not deduction_minutes:
                is_enabled = global_is_enabled
                deduction_minutes = global_deduction_minutes
            
            deduction_hours = 0.0
            if is_enabled:
                deduction_hours = deduction_minutes / 60.0
            
            # Apply deduction ONCE to the total working hours
            slip.attendance_worked_hours = max(0.0, total_custom - deduction_hours)

            # Use strict after-work OT logic (excludes morning OT) if available
            after_work_ot = slip._get_after_work_overtime_hours()
            if after_work_ot is not None:
                # Never exceed extra computed after employee-level logic.
                slip.attendance_extra_hours = min(after_work_ot, extra)
            else:
                slip.attendance_extra_hours = extra

    def _get_worked_day_lines_values(self, domain=None):
        """Override to use actual attendance hours for normal work (WORK100).
        - When allow_overtime=True : paid hours = normal + extra (OT included)
        - When allow_overtime=False: paid hours = normal hours only (capped at 8/shift)
        Remaining unworked hours are injected as OUT-OF-CONTRACT so Odoo's
        salary denominator equals full calendar month hours (correct proration).
        """
        self.ensure_one()
        res = super()._get_worked_day_lines_values(domain=domain)
        if self.attendance_worked_hours <= 0:
            return res

        work100 = self.env['hr.work.entry.type'].search([('code', '=', 'WORK100')], limit=1)
        if not work100:
            return res

        hours_per_day = self._get_worked_day_lines_hours_per_day()

        # --- Full scheduled hours from Odoo's work entries for this period ---
        original_work100_hours = 0.0
        for line in res:
            if line.get('work_entry_type_id') == work100.id:
                original_work100_hours = line['number_of_hours']
                break

        # --- How many hours to actually pay for WORK100 ---
        allow_ot = self.employee_id.allow_overtime if self.employee_id else False
        if allow_ot:
            # Include OT hours in the paid amount
            paid_hours = self.attendance_worked_hours + self.attendance_extra_hours
        else:
            # Only pay for capped (normal) attendance hours
            paid_hours = self.attendance_worked_hours

        # --- Replace WORK100 hours with actual paid hours ---
        for line in res:
            if line.get('work_entry_type_id') == work100.id:
                line['number_of_hours'] = paid_hours
                line['number_of_days'] = (
                    float_round(paid_hours / hours_per_day, precision_rounding=0.01)
                    if hours_per_day else 0
                )
                break

        # --- Inject unworked hours as OUT-of-contract so the denominator stays correct ---
        # denominator = paid_hours + unworked_hours = original_work100_hours (full month schedule)
        unworked_hours = original_work100_hours - paid_hours
        if unworked_hours > 0.01:
            out_type = self.env.ref(
                'hr_work_entry.hr_work_entry_type_out_of_contract', raise_if_not_found=False
            )
            if out_type:
                out_exists = False
                for line in res:
                    if line.get('work_entry_type_id') == out_type.id:
                        line['number_of_hours'] += unworked_hours
                        line['number_of_days'] = (
                            float_round(line['number_of_hours'] / hours_per_day, precision_rounding=0.01)
                            if hours_per_day else 0
                        )
                        out_exists = True
                        break
                if not out_exists:
                    res.append({
                        'sequence': out_type.sequence,
                        'work_entry_type_id': out_type.id,
                        'number_of_hours': unworked_hours,
                        'number_of_days': (
                            float_round(unworked_hours / hours_per_day, precision_rounding=0.01)
                            if hours_per_day else 0
                        ),
                    })

        return res


    def _get_work_end_per_day(self, calendar, from_date, to_date):
        """Return dict date -> work end datetime (UTC) for each work day in range."""
        if not calendar or not calendar.attendance_ids:
            return {}
        # Build per (dayofweek, week_type) the max hour_to (work end in hours, e.g. 17.0)
        work_attendances = calendar._get_global_attendances()
        end_by_day = {}  # (dayofweek, week_type) -> hour_to
        for att in work_attendances:
            if att.display_type:
                continue
            key = (att.dayofweek, att.week_type or '0')
            end_by_day[key] = max(end_by_day.get(key, 0), att.hour_to)
        tz = pytz.timezone(calendar.tz or 'UTC') if pytz else None
        result = {}
        d = from_date
        while d <= to_date:
            weekday = str(d.weekday())  # 0=Monday
            # week_type: 0 = first week, 1 = second week (for 2-week calendars)
            week_type = '0'
            if calendar.two_weeks_calendar:
                iso_week = d.isocalendar()[1]
                week_type = '1' if iso_week % 2 == 0 else '0'
            key = (weekday, week_type)
            if key not in end_by_day:
                key = (weekday, '0')
            hour_to = end_by_day.get(key)
            if hour_to is not None:
                hour_int = int(hour_to)
                min_int = int(round((hour_to % 1) * 60))
                if min_int >= 60:
                    hour_int += 1
                    min_int = 0
                work_end_naive = datetime(d.year, d.month, d.day, hour_int, min_int, 0)
                if tz:
                    work_end_utc = tz.localize(work_end_naive).astimezone(pytz.UTC).replace(tzinfo=None)
                else:
                    work_end_utc = work_end_naive
                result[d] = work_end_utc
            d += timedelta(days=1)
        return result

    def _get_after_work_overtime_hours(self):
        """
        Overtime hours that fall *after* official work end time (office/country schedule).
        Early morning (before work start) OT is not counted for salary.
        Returns None if not computable (no calendar/overtime model); then full OT is kept.
        """
        self.ensure_one()
        if not self.employee_id or not self.version_id or not self.version_id.resource_calendar_id:
            return None
        OvertimeLine = self.env.get('hr.attendance.overtime.line')
        if not OvertimeLine:
            return None
        date_from_dt = fields.Datetime.start_of(self.date_from, 'day')
        date_to_dt = fields.Datetime.end_of(self.date_to, 'day')
        calendar = self.version_id.resource_calendar_id
        work_end_by_date = self._get_work_end_per_day(calendar, self.date_from, self.date_to)
        if not work_end_by_date:
            return None
        overtimes = OvertimeLine.search([
            ('employee_id', '=', self.employee_id.id),
            ('time_start', '<', date_to_dt),
            ('time_stop', '>', date_from_dt),
            ('duration', '>', 0),  # only positive OT (after work); negative = early/undertime
        ])
        if getattr(self.env.company, 'attendance_overtime_validation', None) == 'by_manager':
            overtimes = overtimes.filtered(lambda o: o.status == 'approved')
        total_after_work = 0.0
        for ot in overtimes:
            t_start = ot.time_start
            t_stop = ot.time_stop
            if t_stop <= t_start:
                continue
            day_cur = max(self.date_from, t_start.date() if hasattr(t_start, 'date') else t_start)
            day_last = min(self.date_to, t_stop.date() if hasattr(t_stop, 'date') else t_stop)
            while day_cur <= day_last:
                day_start = fields.Datetime.start_of(day_cur, 'day')
                day_end = fields.Datetime.end_of(day_cur, 'day')
                work_end_utc = work_end_by_date.get(day_cur)
                if work_end_utc is not None:
                    # Work day: only count hours after office end time
                    after_start = max(t_start, work_end_utc)
                    after_end = min(t_stop, day_end)
                else:
                    # Non-work day (e.g. weekend): count full OT on that day
                    after_start = max(t_start, day_start)
                    after_end = min(t_stop, day_end)
                if after_start < after_end:
                    total_after_work += (after_end - after_start).total_seconds() / 3600.0
                day_cur += timedelta(days=1)
        return float_round(total_after_work, precision_digits=2)
