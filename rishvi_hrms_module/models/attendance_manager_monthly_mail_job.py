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
import base64

from odoo import Command, _, api, fields, models


class HrAttendanceManagerMonthlyMailJob(models.TransientModel):
    _name = 'hr.attendance.manager.monthly.mail.job'
    _description = 'Attendance Manager Monthly Mail Job'
    _order = 'create_date desc, id desc'

    name = fields.Char(string="Job", readonly=True)
    report_id = fields.Many2one(
        'hr.attendance.manager.monthly.report',
        string="Report",
        required=True,
        ondelete='cascade',
        readonly=True,
    )
    requested_by_user_id = fields.Many2one(
        'res.users',
        string="Requested By",
        required=True,
        readonly=True,
        default=lambda self: self.env.user,
    )
    recipient_email = fields.Char(string="Recipient Email", required=True, readonly=True)
    state = fields.Selection(
        [
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('sent', 'Sent'),
            ('failed', 'Failed'),
        ],
        string="Status",
        default='pending',
        required=True,
        readonly=True,
    )
    error_message = fields.Text(string="Error", readonly=True)
    mail_id = fields.Many2one('mail.mail', string="Mail", readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            record.name = '%s - %s' % (
                record.requested_by_user_id.name or _('Attendance Preview'),
                record.report_id.month_label or _('Current Month'),
            )
        return records

    def action_process_now(self):
        self._process_jobs()

    @api.model
    def _cron_process_mail_queue(self):
        jobs = self.sudo().search([('state', '=', 'pending')], limit=10)
        jobs._process_jobs()

    def _process_jobs(self):
        attachment_model = self.env['ir.attachment'].sudo()
        mail_model = self.env['mail.mail'].sudo()

        for job in self:
            if job.state != 'pending':
                continue
            job.sudo().write({'state': 'processing', 'error_message': False})
            try:
                report = job.report_id.sudo().exists()
                if not report:
                    raise ValueError(_("The attendance preview record is no longer available."))

                attachments = attachment_model.create([
                    {
                        'name': report._build_export_filename('pdf'),
                        'type': 'binary',
                        'datas': base64.b64encode(report._generate_pdf_bytes()),
                        'res_model': job._name,
                        'res_id': job.id,
                        'mimetype': 'application/pdf',
                    },
                    {
                        'name': report._build_export_filename('xlsx'),
                        'type': 'binary',
                        'datas': base64.b64encode(report._generate_xlsx_bytes()),
                        'res_model': job._name,
                        'res_id': job.id,
                        'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    },
                    {
                        'name': report._build_export_filename('docx'),
                        'type': 'binary',
                        'datas': base64.b64encode(report._generate_docx_bytes()),
                        'res_model': job._name,
                        'res_id': job.id,
                        'mimetype': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                    },
                ])

                mail = mail_model.create({
                    'subject': _('Attendance Preview - %s') % (report.month_label or _('Current Month')),
                    'body_html': _(
                        '<p>Please find attached the attendance preview exports in PDF, XLSX, and DOCX formats.</p>'
                        '<p>Period: %s to %s</p>'
                    ) % (report.date_from, report.date_to),
                    'email_to': job.recipient_email,
                    'attachment_ids': [Command.set(attachments.ids)],
                })
                job.sudo().write({
                    'state': 'sent',
                    'mail_id': mail.id,
                })
            except Exception as exc:
                job.sudo().write({
                    'state': 'failed',
                    'error_message': str(exc),
                })
