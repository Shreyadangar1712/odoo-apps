# -*- coding: utf-8 -*-
#############################################################################
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
import time
from datetime import datetime, date,timedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class Parser(models.AbstractModel):
    _name = 'report.rishvi_real_estate.report_late_payments_customers'
    _description = 'Report Late Payments Customers'

    def _get_lines(self,start_date, end_date, partner_ids):
        now = datetime.today().date()
        domain = [('date','>=',start_date),('date','<=',end_date),('date','<',now),('amount_residual','>',0)]
        if partner_ids: domain.append(('contract_partner_id','in',self.partner_ids.ids))
        loans=self.env['loan.line.rs.own'].search(domain)
        return loans

    def _get_total(self,start_date, end_date, partner_ids):
        now = datetime.today().date()
        domain = [('date','>=',start_date),('date','<=',end_date),('date','<',now),('amount_residual','>',0)]
        if partner_ids: domain.append(('contract_partner_id','in',self.partner_ids.ids))
        loans=self.env['loan.line.rs.own'].search(domain)
        sum=0.0
        for line in loans:
            sum+=line.amount_residual
        return sum

    def _get_total(self,start_date, end_date, partner_ids):
        now = datetime.today().date()
        sum=0
        if len(partner_ids)>0:
            contract_ids = self.env['ownership.contract'].search([('partner_id', 'in', partner_ids)])        
        else:
            contract_ids = self.env['ownership.contract'].search([])
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        contracts=[]
        for obj in contract_ids: contracts.append(obj.id)
        contracts=self.env['ownership.contract'].browse(contracts)
        for contract in contracts:
            for line in contract.loan_line:
                if line.total_remaining_amount and line.date < now and line.date>=start_date and line.date <=end_date:
                    sum+=line.amount
        return sum

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data.get('form'):
            raise UserError(_("Form content is missing, this report cannot be printed."))

        due_payment = self.env['ir.actions.report']._get_report_from_name('rishvi_real_estate.report_late_payments_customers')

        return {
            'doc_ids': self.ids,
            'doc_model': due_payment.model,
            'date_start':data['form']['date_start'],
            'date_end':data['form']['date_end'],
            'get_lines': self._get_lines(data['form']['date_start'],data['form']['date_end'],data['form']['partner_ids']),
            'get_total': self._get_total(data['form']['date_start'],data['form']['date_end'],data['form']['partner_ids']),
        }