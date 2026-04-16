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
import base64
import logging
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.date_utils import relativedelta


_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    @api.model
    def _get_month_range(self, year, month):
        date_start = fields.Date.to_date('%s-%02d-01' % (year, month))
        return date_start, date_start + relativedelta(day=31)

    @api.model
    def _get_month_label(self, month):
        return dict(self._fields['absent_reminder_month'].selection).get(str(month))

    def _get_absent_reminder_leave_domain(self, employee_ids, date_start, date_end):
        return [
            ('employee_id', 'in', employee_ids),
            ('state', 'in', ['validate', 'validate1']),
            ('date_from', '<=', date_end),
            ('date_to', '>=', date_start),
        ]

    def _build_absent_reminder_context(self, emp_leaves, date_start, date_end, month_name, year):
        absence_days = sum(emp_leaves.mapped('number_of_days'))
        absence_dates = []
        for leave in emp_leaves:
            current_date = leave.date_from.date()
            while current_date <= leave.date_to.date():
                if date_start <= current_date <= date_end:
                    absence_dates.append(current_date.strftime('%Y-%m-%d'))
                current_date += relativedelta(days=1)
        return {
            'absence_days': absence_days,
            'absence_dates': sorted(list(set(absence_dates))),
            'absence_month': month_name,
            'absence_year': year,
        }

    @api.model
    def _send_absent_reminder_emails(self, employees, date_start, date_end, month_name, year, require_leave=False, log_prefix=""):
        template = self.env.ref('rishvi_hrms_module_v19.absent_reminder_email_template', raise_if_not_found=False)
        if not template:
            raise UserError(_("Template missing."))

        employees = employees.filtered('work_email')
        if not employees:
            return 0, 0

        leaves = self.env['hr.leave'].sudo().search(
            self._get_absent_reminder_leave_domain(employees.ids, date_start, date_end)
        )
        leaves_by_employee = {}
        for leave in leaves:
            leaves_by_employee.setdefault(leave.employee_id.id, self.env['hr.leave'])
            leaves_by_employee[leave.employee_id.id] |= leave

        sent_count = 0
        for employee in employees:
            emp_leaves = leaves_by_employee.get(employee.id, self.env['hr.leave'])
            if require_leave and not emp_leaves:
                if log_prefix:
                    _logger.info("%sSkipping %s because no approved leave matched the period", log_prefix, employee.name)
                continue

            add_ctx = self._build_absent_reminder_context(emp_leaves, date_start, date_end, month_name, year)
            try:
                template.with_context(**add_ctx).send_mail(employee.id, force_send=True)
                sent_count += 1
                if log_prefix:
                    _logger.info("%sSent absence reminder to %s (%s days)", log_prefix, employee.name, add_ctx['absence_days'])
            except Exception as exc:
                _logger.exception(
                    "%sFailed to send absence reminder to %s: %s",
                    log_prefix,
                    employee.name,
                    exc,
                )
        return sent_count, len(leaves)

    birthday_spotlight_photo = fields.Binary(
        string="Snapshot Photo",
        related='company_id.birthday_spotlight_photo',
        readonly=False,
    )
    birthday_spotlight_text = fields.Text(
        string="Spotlight Message",
        related='company_id.birthday_spotlight_text',
        readonly=False,
    )
    birthday_spotlight_role = fields.Char(
        string="Spotlight Role",
        related='company_id.birthday_spotlight_role',
        readonly=False,
    )
    birthday_header_icon = fields.Binary(
        string="Birthday Header Icon",
        related='company_id.birthday_header_icon',
        readonly=False,
    )
    birthday_send_to_all_today = fields.Boolean(
        string="Send To All Employee Birthday Mail",
        related='company_id.birthday_send_to_all_today',
        readonly=False,
    )

    today_birthday_count = fields.Integer(
        string="Employees with Birthday Today",
        compute='_compute_today_birthdays',
        store=False,
    )
    today_birthday_employee_ids = fields.Many2many(
        'hr.employee',
        string="Today's Birthday Employees",
        compute='_compute_today_birthdays',
        store=False,
    )
    spotlight_employee_ids = fields.Many2many(
        'hr.employee',
        'res_config_settings_spotlight_emp_rel',
        string="Select Employees",
    )

    absent_reminder_month = fields.Selection(
        [
            ('1', 'January'),
            ('2', 'February'),
            ('3', 'March'),
            ('4', 'April'),
            ('5', 'May'),
            ('6', 'June'),
            ('7', 'July'),
            ('8', 'August'),
            ('9', 'September'),
            ('10', 'October'),
            ('11', 'November'),
            ('12', 'December'),
        ],
        string="Month",
        default=lambda self: str(fields.Date.today().month),
    )
    absent_reminder_year = fields.Integer(
        string="Year",
        default=lambda self: fields.Date.today().year,
    )
    absent_reminder_send_to_all = fields.Boolean(
        string="Send To All Employee Absent Reminder Mail",
        related='company_id.absent_reminder_send_to_all',
        readonly=False,
    )
    late_coming_notification_enabled = fields.Boolean(
        related='company_id.late_coming_notification_enabled',
        readonly=False,
    )
    late_coming_send_to_all = fields.Boolean(
        related='company_id.late_coming_send_to_all',
        readonly=False,
    )
    late_coming_recipient = fields.Selection(
        related='company_id.late_coming_recipient',
        readonly=False,
    )
    late_coming_employee_ids = fields.Many2many(
        'hr.employee',
        related='company_id.late_coming_employee_ids',
        readonly=False,
    )
    early_going_notification_enabled = fields.Boolean(
        related='company_id.early_going_notification_enabled',
        readonly=False,
    )
    early_going_send_to_all = fields.Boolean(
        related='company_id.early_going_send_to_all',
        readonly=False,
    )
    early_going_recipient = fields.Selection(
        related='company_id.early_going_recipient',
        readonly=False,
    )
    early_going_employee_ids = fields.Many2many(
        'hr.employee',
        related='company_id.early_going_employee_ids',
        readonly=False,
    )
    absent_reminder_employee_ids = fields.Many2many(
        'hr.employee',
        'res_config_settings_absent_emp_rel',
        string="Select Employees",
    )

    @api.depends()
    def _compute_today_birthdays(self):
        today = fields.Date.context_today(self)
        employees = self.env['hr.employee'].search([
            ('birthday', '!=', False),
            ('birthday', 'like', '-%02d-%02d' % (today.month, today.day)),
        ])
        for rec in self:
            rec.today_birthday_employee_ids = employees
            rec.today_birthday_count = len(employees)

    def _get_image_bytes(self, binary_field_value):
        if not binary_field_value:
            return None
        try:
            return base64.b64decode(binary_field_value)
        except Exception:
            _logger.warning("Failed to decode birthday image binary field.")
            return None

    def _build_birthday_html(self, employee, company, photo_cid, header_cid, has_photo, has_header):
        role = company.birthday_spotlight_role or employee.job_title or ''
        message = company.birthday_spotlight_text or (
            'Wishing you a very Happy Birthday! Hope you have a wonderful day and a great year ahead.'
        )

        header_img_html = ''
        if has_header:
            header_img_html = (
                '<img src="cid:{cid}" width="80" style="max-height:80px;margin-bottom:15px;display:block;" '
                'alt="Header Icon"/><br/>'
            ).format(cid=header_cid)

        photo_img_html = ''
        if has_photo:
            photo_img_html = (
                '<img src="cid:{cid}" width="180" height="180" '
                'style="width:180px;height:180px;object-fit:cover;border-radius:50%;border:5px solid '
                '#714B67;margin-bottom:16px;display:block;" alt="{name}"/>'
            ).format(
                cid=photo_cid,
                name=employee.name or '',
            )

        return """
<div style="margin:0;padding:0;background-color:#f4f6f9;font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;">
  <table width="100%" cellspacing="0" cellpadding="0" style="background-color:#f4f6f9;padding:24px 0;">
    <tr><td align="center">
      <table width="600" cellspacing="0" cellpadding="0"
             style="background-color:#ffffff;border-radius:10px;overflow:hidden;box-shadow:0 4px 16px rgba(0,0,0,0.09);">
        <tr>
          <td align="center" style="background:linear-gradient(135deg,#714B67 0%,#e91e8c 100%);padding:40px 24px;">
            {header_img}
            <h1 style="color:#ffffff;margin:0;font-size:28px;letter-spacing:2px;">Happy Birthday!</h1>
            <p style="color:#fce4ec;margin:8px 0 0 0;font-size:16px;">Wishing you a wonderful day!</p>
          </td>
        </tr>
        <tr>
          <td align="center" style="padding:32px 36px 16px 36px;">
            {photo_img}
            <h2 style="color:#2c3e50;margin:0;font-size:24px;">{name}</h2>
            <p style="color:#7f8c8d;margin:6px 0 0 0;font-size:15px;">{role}</p>
          </td>
        </tr>
        <tr>
          <td style="padding:16px 36px 32px 36px;text-align:center;">
            <div style="font-style:italic;background:#fff9e6;padding:20px;border-radius:8px;border-left:4px solid #f1c40f;text-align:left;color:#34495e;font-size:15px;line-height:1.7;">
              {message}
            </div>
          </td>
        </tr>
        <tr>
          <td style="background:#f4f6f9;padding:16px 36px;border-top:1px solid #e8e8e8;text-align:center;">
            <p style="color:#aaa;margin:0;font-size:12px;">With love from <strong>{company}</strong> HR Team</p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</div>""".format(
            header_img=header_img_html,
            photo_img=photo_img_html,
            name=employee.name or '',
            role=role,
            message=message,
            company=company.name or '',
        )

    def action_open_birthday_wizard(self):
        self.ensure_one()
        if self.birthday_send_to_all_today:
            employees_to_send = self.today_birthday_employee_ids
            if not employees_to_send:
                raise UserError(_("No employee has birthday today."))
        else:
            employees_to_send = self.spotlight_employee_ids
            if not employees_to_send:
                raise UserError(_("Please select at least one employee."))

        mail_server = self.env['ir.mail_server'].sudo().search([], order='sequence', limit=1)
        smtp_from = (
            mail_server.smtp_user
            or self.env['ir.config_parameter'].sudo().get_param('mail.catchall.domain')
            or 'noreply@example.com'
        )

        sent = 0
        for employee in employees_to_send:
            if not employee.work_email:
                continue

            company = employee.company_id or self.env.company
            photo_bytes = self._get_image_bytes(company.birthday_spotlight_photo)
            if not photo_bytes:
                photo_bytes = self._get_image_bytes(employee.image_256)
            header_bytes = self._get_image_bytes(company.birthday_header_icon)

            photo_cid = 'bday_photo_%d' % employee.id
            header_cid = 'bday_header_%d' % employee.id

            html_body = self._build_birthday_html(
                employee,
                company,
                photo_cid,
                header_cid,
                has_photo=bool(photo_bytes),
                has_header=bool(header_bytes),
            )

            msg_root = MIMEMultipart('related')
            msg_root['Subject'] = 'Happy Birthday %s!' % (employee.name or '')
            msg_root['From'] = smtp_from
            msg_root['To'] = employee.work_email

            msg_alt = MIMEMultipart('alternative')
            msg_root.attach(msg_alt)
            msg_alt.attach(MIMEText(html_body, 'html', 'utf-8'))

            if header_bytes:
                img = MIMEImage(header_bytes)
                img.add_header('Content-ID', '<%s>' % header_cid)
                img.add_header('Content-Disposition', 'inline', filename='header.png')
                msg_root.attach(img)

            if photo_bytes:
                img = MIMEImage(photo_bytes)
                img.add_header('Content-ID', '<%s>' % photo_cid)
                img.add_header('Content-Disposition', 'inline', filename='photo.png')
                msg_root.attach(img)

            try:
                self.env['ir.mail_server'].sudo().send_email(msg_root)
                _logger.info('Birthday email sent to %s (%s)', employee.name, employee.work_email)
                sent += 1
            except Exception as exc:
                _logger.error('Failed to send birthday email to %s: %s', employee.work_email, exc)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Birthday Announcements Sent'),
                'message': _('Successfully sent birthday announcement for %d employee(s).') % sent,
                'type': 'success',
                'sticky': False,
            },
        }

    def action_send_daily_late_coming_notifications(self):
        self.ensure_one()
        self.env['hr.attendance']._send_daily_late_coming_notifications(manual=True)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Late Coming Notifications'),
                'message': _('Daily late coming notifications have been processed.'),
                'type': 'success',
                'sticky': False,
            },
        }

    def action_send_daily_early_going_notifications(self):
        self.ensure_one()
        self.env['hr.attendance']._send_daily_early_going_notifications(manual=True)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Early Going Notifications'),
                'message': _('Daily early going notifications have been processed.'),
                'type': 'success',
                'sticky': False,
            },
        }

    def action_send_absent_reminder(self):
        self.ensure_one()
        if self.absent_reminder_send_to_all:
            employees_to_send = self.env['hr.employee'].search([('active', '=', True)])
            if not employees_to_send:
                raise UserError(_("No employees found to send reminders."))
        else:
            employees_to_send = self.absent_reminder_employee_ids
            if not employees_to_send:
                raise UserError(_("Please select at least one employee."))

        template = self.env.ref('rishvi_hrms_module_v19.absent_reminder_email_template', raise_if_not_found=False)
        if not template:
            raise UserError(_("Template missing."))

        today = fields.Date.context_today(self)
        year = self.absent_reminder_year or today.year
        month = int(self.absent_reminder_month or today.month)
        date_start, date_end = self._get_month_range(year, month)
        month_name = self._get_month_label(month)
        sent, _leave_count = self._send_absent_reminder_emails(
            employees_to_send,
            date_start,
            date_end,
            month_name,
            year,
            require_leave=False,
        )

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Reminders Sent'),
                'message': _('Sent monthly absence reminder to %d employee(s).') % sent,
                'type': 'success',
                'sticky': False,
            },
        }

    @api.model
    def _cron_send_monthly_absence_reminder(self):
        _logger.info("CRON: Starting Monthly Absence Reminder check.")
        today = fields.Date.context_today(self)
        year = today.year
        month = today.month

        date_start, date_end = self._get_month_range(year, month)

        _logger.info("CRON: Calculating absences for period %s to %s", date_start, date_end)
        month_name = self._get_month_label(month)

        template = self.env.ref('rishvi_hrms_module_v19.absent_reminder_email_template', raise_if_not_found=False)
        if not template:
            _logger.error("CRON: Template 'rishvi_hrms_module_v19.absent_reminder_email_template' not found!")
            return

        employees = self.env['hr.employee'].search([('work_email', '!=', False)])
        send_to_all = bool(self.env.company.absent_reminder_send_to_all)
        _logger.info("CRON: Found %d employees with work emails", len(employees))
        _logger.info("CRON: Send to all employees mode is %s", send_to_all)

        sent_count, leave_count = self._send_absent_reminder_emails(
            employees,
            date_start,
            date_end,
            month_name,
            year,
            require_leave=not send_to_all,
            log_prefix="CRON: ",
        )
        _logger.info("CRON: Found %d approved leave records in search period", leave_count)
        _logger.info("CRON: Monthly Absence Reminder finished. Total emails sent: %d", sent_count)
