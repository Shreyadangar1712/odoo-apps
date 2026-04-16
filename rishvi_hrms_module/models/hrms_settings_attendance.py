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

import pytz

from odoo import api, fields, models
from odoo.osv.expression import AND, OR


_logger = logging.getLogger(__name__)


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    late_notification_sent = fields.Boolean(string="Late Notification Sent", default=False, copy=False)
    early_notification_sent = fields.Boolean(string="Early Notification Sent", default=False, copy=False)

    check_in_local = fields.Char(string="Check In (Local)", compute="_compute_display_times")
    check_out_local = fields.Char(string="Check Out (Local)", compute="_compute_display_times")
    late_duration = fields.Char(string="Late Duration", compute="_compute_display_times")
    early_duration = fields.Char(string="Early Duration", compute="_compute_display_times")

    def _supports_attendance_alert_metrics(self):
        return {
            'late_minutes': 'late_minutes' in self._fields,
            'early_minutes': 'early_minutes' in self._fields,
            'attendance_status': 'attendance_status' in self._fields,
        }

    @staticmethod
    def _format_minutes_as_hhmm(minutes):
        if not minutes:
            return "00:00"
        hours = int(minutes // 60)
        remaining_minutes = int(minutes % 60)
        return f"{hours:02d}:{remaining_minutes:02d}"

    def _compute_display_times(self):
        metrics = self._supports_attendance_alert_metrics()
        for rec in self:
            tz_name = rec.employee_id.tz or self.env.user.tz or 'UTC'
            try:
                tz = pytz.timezone(tz_name)
            except Exception:
                tz = pytz.UTC

            rec.check_in_local = ""
            if rec.check_in:
                local_dt = pytz.UTC.localize(rec.check_in).astimezone(tz)
                rec.check_in_local = local_dt.strftime('%b %d, %I:%M %p')

            rec.check_out_local = ""
            if rec.check_out:
                local_dt = pytz.UTC.localize(rec.check_out).astimezone(tz)
                rec.check_out_local = local_dt.strftime('%b %d, %I:%M %p')

            late_minutes = rec.late_minutes if metrics['late_minutes'] else 0.0
            early_minutes = rec.early_minutes if metrics['early_minutes'] else 0.0
            rec.late_duration = self._format_minutes_as_hhmm(late_minutes)
            rec.early_duration = self._format_minutes_as_hhmm(early_minutes)

    def _get_hr_recipient_emails(self):
        hr_group = self.env.ref('hr.group_hr_manager', raise_if_not_found=False)
        if not hr_group:
            return []
        return list({
            user.email
            for user in hr_group.user_ids
            if user.email
        })

    def _get_manager_recipient_emails(self):
        self.ensure_one()
        emails = set()
        for manager in (self.employee_id.parent_id, self.employee_id.leave_manager_id):
            if not manager:
                continue
            if manager.work_email:
                emails.add(manager.work_email)
            elif manager.user_id and manager.user_id.email:
                emails.add(manager.user_id.email)
        return list(emails)

    def _get_recipient_emails(self, recipient_mode):
        self.ensure_one()
        emails = set()
        if recipient_mode in ('hr', 'both'):
            emails.update(self._get_hr_recipient_emails())
        if recipient_mode in ('manager', 'both'):
            emails.update(self._get_manager_recipient_emails())
        return sorted(emails)

    def _send_attendance_alert_email(self, template_xmlid, recipient_mode, notification_field, log_prefix):
        template = self.env.ref(template_xmlid, raise_if_not_found=False)
        if not template:
            _logger.error("%sTemplate %s not found", log_prefix, template_xmlid)
            return 0

        sent_count = 0
        for attendance in self:
            if attendance[notification_field]:
                continue

            recipient_emails = attendance._get_recipient_emails(recipient_mode)
            if not recipient_emails:
                _logger.info("%sSkipping %s because no recipient email was found", log_prefix, attendance.employee_id.name)
                continue

            try:
                template.send_mail(
                    attendance.id,
                    force_send=True,
                    email_values={'email_to': ','.join(recipient_emails)},
                )
                attendance[notification_field] = True
                sent_count += 1
                _logger.info("%sSent notification for %s to %s", log_prefix, attendance.employee_id.name, ', '.join(recipient_emails))
            except Exception as exc:
                _logger.exception(
                    "%sFailed to send notification for %s: %s",
                    log_prefix,
                    attendance.employee_id.name,
                    exc,
                )
        return sent_count

    def _get_day_bounds(self, target_date=None):
        target_date = target_date or fields.Date.context_today(self)
        tz_name = self.env.context.get('tz') or self.env.user.tz or self.env.company.partner_id.tz or 'UTC'
        try:
            tz = pytz.timezone(tz_name)
        except Exception:
            tz = pytz.UTC

        local_start = tz.localize(fields.Datetime.to_datetime(f"{target_date} 00:00:00"))
        local_end = tz.localize(fields.Datetime.to_datetime(f"{target_date} 23:59:59"))

        day_start = local_start.astimezone(pytz.UTC).replace(tzinfo=None)
        day_end = local_end.astimezone(pytz.UTC).replace(tzinfo=None)
        return day_start, day_end

    def _get_late_attendances_for_day(self, target_date=None):
        day_start, day_end = self._get_day_bounds(target_date=target_date)
        metrics = self._supports_attendance_alert_metrics()
        domain = [
            ('check_in', '>=', day_start),
            ('check_in', '<=', day_end),
            ('late_notification_sent', '=', False),
        ]
        late_conditions = []
        if metrics['late_minutes']:
            late_conditions.append(('late_minutes', '>', 0))
        if metrics['attendance_status']:
            late_conditions.append(('attendance_status', '=', 'late'))

        if not late_conditions:
            _logger.warning(
                "LATE ALERT: Missing optional attendance fields late_minutes/attendance_status on hr.attendance; "
                "skipping late attendance notifications."
            )
            return self.browse()

        if len(late_conditions) == 2:
            domain = AND([domain, OR([late_conditions[:1], late_conditions[1:]])])
        else:
            domain.append(late_conditions[0])
        return self.search(domain)

    def _get_early_attendances_for_day(self, target_date=None):
        day_start, day_end = self._get_day_bounds(target_date=target_date)
        metrics = self._supports_attendance_alert_metrics()
        if not metrics['early_minutes']:
            _logger.warning(
                "EARLY ALERT: Missing optional attendance field early_minutes on hr.attendance; "
                "skipping early going notifications."
            )
            return self.browse()

        return self.search([
            ('check_out', '>=', day_start),
            ('check_out', '<=', day_end),
            ('early_minutes', '>', 0),
            ('check_out', '!=', False),
            ('early_notification_sent', '=', False),
        ])

    def _filter_company_attendance_scope(self, attendances, employee_ids, send_to_all, log_prefix):
        if send_to_all:
            return attendances
        if not employee_ids:
            _logger.info("%sNo employees selected in settings, skipping notifications", log_prefix)
            return self.browse()
        return attendances.filtered_domain([('employee_id', 'in', employee_ids.ids)])

    def _send_daily_late_coming_notifications(self, manual=False):
        company = self.env.company
        if not manual and not company.late_coming_notification_enabled:
            _logger.info("LATE ALERT: Notification disabled in settings")
            return 0
        attendances = self._filter_company_attendance_scope(
            self._get_late_attendances_for_day(),
            company.late_coming_employee_ids,
            company.late_coming_send_to_all,
            "LATE ALERT: ",
        )
        _logger.info("LATE ALERT: Found %d late attendance records for %s", len(attendances), fields.Date.today())
        return attendances._send_attendance_alert_email(
            'rishvi_hrms_module_v19.late_coming_alert_email_template',
            company.late_coming_recipient,
            'late_notification_sent',
            "LATE ALERT: ",
        )

    def _send_daily_early_going_notifications(self, manual=False):
        company = self.env.company
        if not manual and not company.early_going_notification_enabled:
            _logger.info("EARLY ALERT: Notification disabled in settings")
            return 0
        attendances = self._filter_company_attendance_scope(
            self._get_early_attendances_for_day(),
            company.early_going_employee_ids,
            company.early_going_send_to_all,
            "EARLY ALERT: ",
        )
        _logger.info("EARLY ALERT: Found %d early attendance records for %s", len(attendances), fields.Date.today())
        return attendances._send_attendance_alert_email(
            'rishvi_hrms_module_v19.early_going_alert_email_template',
            company.early_going_recipient,
            'early_notification_sent',
            "EARLY ALERT: ",
        )

    @api.model
    def _cron_send_daily_late_coming_notifications(self):
        sent = self._send_daily_late_coming_notifications()
        _logger.info("LATE ALERT: Daily cron finished. Total emails sent: %d", sent)

    @api.model
    def _cron_send_daily_early_going_notifications(self):
        sent = self._send_daily_early_going_notifications()
        _logger.info("EARLY ALERT: Daily cron finished. Total emails sent: %d", sent)
