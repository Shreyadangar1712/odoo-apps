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

from odoo.exceptions import UserError,ValidationError
from odoo import api, fields, models
from odoo.tools.translate import _
from datetime import date
import calendar
from dateutil.relativedelta import relativedelta

class rental_contract(models.Model):
    _name = "rental.contract"
    _description = "Rental Contract"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    @api.depends('loan_line.amount','loan_line.amount_residual')
    def _check_amounts(self):
        total_paid = 0
        total_nonpaid = 0
        amount_total= 0
        for rec in self:
            for line in rec.loan_line:
                amount_total+= line.amount
                total_nonpaid+= line.amount_residual
                total_paid+= (line.amount-line.amount_residual)

        self.paid = total_paid
        self.balance = total_nonpaid
        self.amount_total=amount_total

    def _voucher_count(self):
        voucher_obj = self.env['account.payment']
        voucher_ids = voucher_obj.search([('real_estate_ref', 'ilike', self.name)])
        self.voucher_count = len(voucher_ids)

    def _entry_count(self):
        move_obj = self.env['account.move']
        move_ids = move_obj.search([('rental_id', 'in', self.ids)])
        self.entry_count = len(move_ids)

    def _default_security_deposit_account(self):
        security_deposit_account = self.env['ir.config_parameter'].sudo().get_param(
            'rishvi_real_estate.security_deposit_account'
        )
        if not security_deposit_account:
            return False
        return self.env['account.account'].browse(int(security_deposit_account)).exists()

    def _default_income_account(self):
        account_income = self.env['ir.config_parameter'].sudo().get_param(
            'rishvi_real_estate.revenue_account'
        )
        if not account_income:
            return False
        return self.env['account.account'].browse(int(account_income)).exists()

    def auto_rental_invoice(self):
        try:
            rental_pool = self.env['loan.line.rs.rent']
            rental_line_ids=rental_pool.search([('loan_id.state','=','confirmed'),('date','<=',fields.Date.today())])
            account_move_obj = self.env['account.move']
            journal_pool = self.env['account.journal']
            journal = journal_pool.search([('type', '=', 'sale')], limit=1)

            for line in rental_line_ids:
                if not line.invoice_id:
                    inv_dict = {'ref': line.name, 'journal_id': journal.id,
                                'partner_id': line.contract_partner_id.id,
                                'move_type': 'out_invoice', 'rental_line_id': line.id,
                                'invoice_date_due': line.date,
                                'property_owner_id': line.loan_id.property_owner_id.id,
                                'ref': (line.loan_id.name + ' - ' + line.name),
                                }
                    if line.loan_id.apply_tax:
                        inv_dict['invoice_line_ids'] = [(0, None, {
                            'name': (line.loan_id.name + ' - ' + line.name),
                            'quantity': 1,
                            # 'analytic_account_id': line.loan_id.account_analytic_id.id,
                            'tax_ids': [(6, 0, (self.env.company.account_sale_tax_id.ids))],
                            'price_unit': line.amount, })]
                    else:
                        inv_dict['invoice_line_ids'] = [(0, None, {
                            'name': (line.loan_id.name + ' - ' + line.name),
                            'quantity': 1,
                            # 'analytic_account_id': line.loan_id.account_analytic_id.id,
                            'price_unit': line.amount, })]

                invoice = account_move_obj.create(inv_dict)
                invoice.action_post()
                line.invoice_id = invoice.id
        except:
            return "Internal Error"

    attach_line= fields.One2many("rental.attachment.line", "contract_id_att", "Documents")
    reservation_id=  fields.Many2one('unit.reservation','Reservation')
    paid= fields.Float(compute='_check_amounts', string='Paid',)
    balance= fields.Float(compute='_check_amounts', string='Balance',)
    amount_total= fields.Float(compute='_check_amounts', string='Total',)
    #rental_contract Info
    name= fields.Char('Name', size=64,readonly=True)
    origin= fields.Char('Source Document', size=64)
    date_from= fields.Date('Start Date', required=True)
    date_to= fields.Date('End Date', required=True)
    date= fields.Date('Date', default=fields.Date.context_today)
    apply_tax= fields.Boolean('Apply Tax')
    #Building Info
    building= fields.Many2one('building','Building', copy=False )
    no_of_floors= fields.Integer('# Floors')
    building_code= fields.Char('Code', size=16)
    #Building Unit Info
    building_unit= fields.Many2one('product.template','Building Unit', copy=False, required=False,domain=[('is_property', '=', True),('state', '=', 'free')])
    building_unit_ids = fields.Many2many('product.template',string='Building Units', store=True,tracking=True,
        required=True,
        # domain=[('is_property', '=', True),('state', '=', 'free')]
    )
    unit_code= fields.Char('Code', size=16)
    floor= fields.Char('Floor', size=16)
    address= fields.Char('Address')
    insurance_fee= fields.Integer('Insurance fee', required=True)
    rental_fee= fields.Integer('Rental fee', required=True)
    type= fields.Many2one('building.type','Building Unit Type', )
    status= fields.Many2one('building.status','Building Unit Status', )
    user_id= fields.Many2one('res.users','Salesman', default=lambda self: self.env.user,)
    partner_id= fields.Many2one('res.partner','Tenant', required=True)
    building_area= fields.Integer('Building Unit Area m²',)
    loan_line= fields.One2many('loan.line.rs.rent', 'loan_id')
    region= fields.Many2one('regions','Region', )
    state= fields.Selection([('draft','Draft'),
                             ('confirmed','Confirmed'),
                             ('renew','Renewed'),
                             ('cancel','Canceled'),
                             ], 'State', default=lambda *a: 'draft')
    account_income= fields.Many2one('account.account','Income Account', default=_default_income_account)
    account_analytic_id= fields.Many2one('account.analytic.account', 'Analytic Account')
    account_security_deposit= fields.Many2one('account.account', 'Security Deposit Account', default=_default_security_deposit_account)
    voucher_count= fields.Integer('Voucher Count',compute='_voucher_count')
    entry_count= fields.Integer('Entry Count',compute='_entry_count')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

    periodicity = fields.Selection([('days', 'Days'), ('weeks', 'Weeks'),
                                            ('months', 'Months'), ('years', 'Years'), ],
                                           string='Recurrence', required=True,
                                           help="Invoice automatically repeat at specified interval",
                                           default='months', tracking=True)

    recurring_interval = fields.Integer(string="Invoicing Period", help="Repeat every (Days/Week/Month/Year)", required=True, default=1, tracking=True)
    property_owner_id = fields.Many2one('res.partner', string="Owner",domain=[('is_owner', '=', True)])

    def action_draft(self):
        self.state =  "draft"
        
    @api.constrains('recurring_interval')
    def _check_recurring_interval(self):
        for record in self:
            if record.recurring_interval <= 0:
                raise ValidationError(_("The recurring interval must be positive"))

    def unlink(self):
        if self.state !='draft':
            raise UserError(_('You can not delete a contract not in draft state'))
        super(rental_contract, self).unlink()

    def view_vouchers(self):
        vouchers=[]
        voucher_obj = self.env['account.payment']
        voucher_ids = voucher_obj.search([('real_estate_ref', '=', self.name)])
        for obj in voucher_ids: vouchers.append(obj.id)
        return {
            'name': _('Receipts'),
            'domain': [('id', 'in', vouchers)],
            'view_type':'form',
            'view_mode':'tree,form',
            'res_model':'account.payment',
            'type':'ir.actions.act_window',
            'nodestroy':True,
            'view_id': False,
            'target':'current',
        }

    def view_entries(self):
        entries=[]
        entry_obj = self.env['account.move']
        entry_ids = entry_obj.search([('rental_id', 'in', self.ids)])
        for obj in entry_ids: entries.append(obj.id)

        return {
            'name': _('Journal Entries'),
            'domain': [('id', 'in', entries)],
            'view_type':'form',
            'view_mode':'tree,form',
            'res_model':'account.move',
            'type':'ir.actions.act_window',
            'nodestroy':True,
            'view_id': False,
            'target':'current',
        }

    def create_move(self,rec,debit,credit,move,account):
        move_line_obj = self.env['account.move.line']
        move_line_obj.create({
            'name': rec.name,
            'partner_id': rec.partner_id.id,
            'account_id': account,
            'debit': debit,
            'credit': credit,
            'move_id': move,
        })

    def generate_cancel_entries(self):
        journal_pool = self.env['account.journal']
        journal = journal_pool.search([('type', '=', 'sale')], limit=1)
        if not journal:
            raise UserError(_('Please set sales accounting journal!'))
        account_move_obj = self.env['account.move']
        total = 0
        for rec in self:
            if not rec.partner_id.property_account_receivable_id:
                raise UserError(_('Please set receivable account for partner!'))
            if not rec.account_income:
                raise UserError(_('Please set income account for this contract!'))
            for line in rec.loan_line:
                total+=line.amount
            account_move_obj.create({'ref' : rec.name, 'journal_id' : journal.id, 'rental_id':rec.id,
                                     'line_ids':[(0,0,{ 'name': rec.name,
                                                        'partner_id': rec.partner_id.id,
                                                        'account_id': rec.partner_id.property_account_receivable_id.id,
                                                        'debit': 0.0,
                                                        'credit': total}),
                                                 (0,0,{'name': rec.name,
                                                       'partner_id': rec.partner_id.id,
                                                       'account_id': rec.account_income.id,
                                                       'debit': total,
                                                       'credit': 0.0})
                                                 ]})

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        if self.filtered(lambda c: c.date_to and c.date_from > c.date_to):
            raise ValidationError(_('Contract start date must be less than contract end date.'))

    @api.onchange('date_from','date_to','rental_fee','insurance_fee','periodicity','recurring_interval')
    def action_calculate(self):
        self.prepare_lines()

    def action_confirm(self):
        for contract_obj in self:
            for unit_rec in contract_obj.building_unit_ids:
                unit_rec.write({'state': 'on_lease'})
            # unit = contract_obj.building_unit
            # unit.write({'state': 'on_lease'})
        self.write({'state':'confirmed'})

    def action_cancel(self):
        for contract_obj in self:
            for unit_rec in contract_obj.building_unit_ids:
                unit_rec.write({'state': 'free'})
            # unit = contract_obj.building_unit
            # unit.write({'state':  'free'})
        self.write({'state':'cancel'})

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('rental.contract')
        new_id = super(rental_contract, self).create(vals)
        return new_id

    @api.onchange('region')
    def onchange_region(self):
        if self.region:
            building_ids = self.env['building'].search([('region_id', '=', self.region.id)])
            buildings=[]
            for u in building_ids: buildings.append(u.id)
            return {'domain': {'building': [('id', 'in', buildings)]}}

    @api.onchange('building')
    def onchange_building(self):
        if self.building:
            units = self.env['product.template'].search([
                ('is_property', '=', True),
                ('building_id', '=', self.building.id),
                ('state', '=', 'free')
            ])
            building_obj = self.building
            if building_obj:
                self.building_code = building_obj.code
                self.region = building_obj.region_id
                self.property_owner_id = building_obj.partner_id
                self.account_analytic_id = building_obj.account_analytic_id
                self.no_of_floors = building_obj.no_of_floors

                return {
                    'domain': {
                        'building_unit': [('id', 'in', units.ids)],
                        'building_unit_ids': [('id', 'in', units.ids)],
                    }
                }
    
    @api.onchange('building_unit','building_unit_ids')
    def onchange_unit(self):
        unit_code = ""
        floor = ""
        address = ""
        building_area = 0
        rental_fee = 0
        insurance_fee = 0
        for bu in self.building_unit_ids:
            if bu.code:
                unit_code += bu.code + ", "
            if bu.floor:
                floor += bu.floor + ", "
            if bu.address:
                address += bu.address + ", "
            building_area += bu.building_area
            rental_fee += bu.rental_fee
            insurance_fee += bu.insurance_fee
        self.unit_code = unit_code
        self.floor = floor
        self.address = address
        self.building_area = building_area
        self.rental_fee = rental_fee
        self.insurance_fee = insurance_fee
        
        
        # self.building = self.building_unit.building_id.id
        # self.region = self.building_unit.region_id.id
        # self.status = self.building_unit.status.id
        # self.type = self.building_unit.ptype.id


    def generate_entries(self):
        journal_pool = self.env['account.journal']
        journal = journal_pool.search([('type', '=', 'sale')], limit=1)
        if not journal:
            raise UserError(_('Please set sales accounting journal!'))
        account_move_obj = self.env['account.move']
        total = 0
        for rec in self:
            if not rec.partner_id.property_account_receivable_id:
                raise UserError(_('Please set receivable account for partner!'))
            if not rec.account_income:
                raise UserError(_('Please set income account for this contract!'))
            if rec.insurance_fee and not rec.account_security_deposit :
                raise UserError(_('Please set security deposit account for this contract!'))

            for line in rec.loan_line:
                total+=line.amount
            if total <=0:
                raise UserError(_('Invalid Rental Amount!'))
            account_move_obj.create({'ref' : rec.name, 'journal_id' : journal.id, 'rental_id':rec.id,
                                     'line_ids':[(0,0,{ 'name': rec.name,
                                                        'partner_id': rec.partner_id.id,
                                                        'account_id': rec.partner_id.property_account_receivable_id.id,
                                                        'debit': total,
                                                        'credit': 0.0}),
                                                 (0,0,{'name': rec.name,
                                                       'partner_id': rec.partner_id.id,
                                                       'account_id': rec.account_income.id, 'debit': 0.0,
                                                       'credit': (total-rec.insurance_fee),}),
                                                 (0, 0, {'name': rec.name,
                                                         'partner_id': rec.partner_id.id,
                                                         'account_id': rec.account_security_deposit.id, 'debit': 0.0,
                                                         'credit': rec.insurance_fee, })
                                                 ]})
    def subtract_month(self,date, year=0, month=0):
        year, month = divmod(year*12 + month, 12)
        if date.month <= month:
            year = date.year - year - 1
            month = date.month - month + 12
        else:
            year = date.year - year
            month = date.month - month
        return date.replace(year = year, month = month)

    def add_months(self,sourcedate, months):
        month = sourcedate.month - 1 + months
        year = int(sourcedate.year + month / 12 )
        month = month % 12 + 1
        day = min(sourcedate.day,calendar.monthrange(year,month)[1])
        return date(year,month,day)

    def prepare_lines(self):
        for rec in self:
            rental_lines = []
            rec.loan_line = [(5, 0, 0)]

            if rec.periodicity and rec.date_from and rec.date_to:
                i = 1
                date_from = rec.date_from
                date_to = rec.date_to
                rental_fee = rec.rental_fee
                new_date = date_from

                if rec.insurance_fee:
                    rental_lines.append(
                        (0, 0, {
                            'serial': i,
                            'company_id': self.env.company.id,
                            'amount': rec.insurance_fee,
                            'date': date_from,
                            'name': _('Insurance Deposit')
                        })
                    )
                    i += 1

                rental_lines.append(
                    (0, 0, {
                        'serial': i,
                        'company_id': self.env.company.id,
                        'amount': rental_fee,
                        'date': date_from,
                        'name': _('Rental Fee')
                    })
                )
                i += 1

                while new_date < (date_to - relativedelta(**{rec.periodicity: rec.recurring_interval})):
                    new_date = new_date + relativedelta(**{rec.periodicity: rec.recurring_interval})
                    rental_lines.append(
                        (0, 0, {
                            'serial': i,
                            'company_id': self.env.company.id,
                            'amount': rental_fee,
                            'date': new_date,
                            'name': _('Rental Fee')
                        })
                    )
                    i += 1

                rec.loan_line = rental_lines

class loan_line_rs_rent(models.Model):
    _name = 'loan.line.rs.rent'
    _order = 'date'

    contract_partner_id= fields.Many2one(related='loan_id.partner_id', string="Partner", store=True)
    contract_building= fields.Many2one(related='loan_id.building', string="Building", store=True)
    contract_building_unit= fields.Many2one(related='loan_id.building_unit', string="Building Unit",domain=[('is_property', '=', True)], store=True)
    contract_region= fields.Many2one(related='loan_id.region',string="Region", store=True)
    date= fields.Date('Due Date')
    name= fields.Char('Name')
    serial= fields.Char('#')
    empty_col= fields.Char(' ',readonly=True)
    amount= fields.Float('Amount', digits=(16, 4))
    paid= fields.Boolean('Paid')
    loan_id= fields.Many2one('rental.contract', '',ondelete='cascade', readonly=True)
    company_id= fields.Many2one('res.company', readonly=True,  default=lambda self: self.env.user.company_id.id)
    contract_user_id= fields.Many2one(string='User', related= 'loan_id.user_id', store=True)
    invoice_id = fields.Many2one('account.move', string='Invoice', )
    payment_state = fields.Selection(related='invoice_id.payment_state', readonly=True, )
    invoice_state = fields.Selection(related='invoice_id.state', readonly=True, )
    amount_residual = fields.Monetary(related='invoice_id.amount_residual', readonly=True,)
    currency_id = fields.Many2one(related='invoice_id.currency_id', readonly=True)

    def make_invoice(self):
        for rec in self:
            if not rec.loan_id.partner_id.property_account_receivable_id:
                raise UserError(_('Please set receivable account for partner!'))
            if not rec.loan_id.account_income:
                raise UserError(_('Please set income account for this contract!'))
            account_move_obj = self.env['account.move']
            journal_pool = self.env['account.journal']
            journal = journal_pool.search([('type', '=', 'sale')], limit=1)
            inv_dict={'ref': rec.name, 'journal_id': journal.id,
                                     'partner_id': rec.contract_partner_id.id,
                                     'move_type': 'out_invoice', 'rental_line_id': rec.id,
                                     'invoice_date_due': rec.date,
                                     'property_owner_id': rec.loan_id.property_owner_id.id,
                                     'ref':(rec.loan_id.name + ' - ' + rec.name),
                                     }
            if self.loan_id.apply_tax:
                inv_dict['invoice_line_ids']= [(0, None, {
                    'name': (rec.loan_id.name + ' - ' + rec.name),
                    'quantity': 1,
                    # 'analytic_account_id': rec.loan_id.account_analytic_id.id,
                    'tax_ids': [(6, 0, (self.env.company.account_sale_tax_id.ids))],
                    'price_unit': rec.amount, })]
            else:
                inv_dict['invoice_line_ids']= [(0, None, {
                    'name': (rec.loan_id.name + ' - ' + rec.name),
                    'quantity': 1,
                    # 'analytic_account_id': rec.loan_id.account_analytic_id.id,
                    'price_unit': rec.amount, })]

            invoice= account_move_obj.create(inv_dict)
            # invoice.action_post()
            self.invoice_id= invoice.id

    def view_invoice(self):
        move = self.env['account.move'].sudo().search([('rental_line_id','=',self.id)])
        return {
            'name': _('Invoice'),
            'view_type': 'form',
            'res_id':move.id,
            'view_mode': 'form',
            'res_model': 'account.move',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
        }

    def send_multiple_installments_rent(self):
        ir_model_data = self.env['ir.model.data']
        template_id = ir_model_data.get_object_reference('rishvi_real_estate',
                                                         'email_template_installment_notification_rent')[1]
        template_res = self.env['mail.template']
        template = template_res.browse(template_id)
        template.send_mail(self.id, force_send=True)

class rental_attachment_line(models.Model):
    _name = 'rental.attachment.line'

    name= fields.Char('Name', required=True)
    file= fields.Binary('File',)
    contract_id_att= fields.Many2one('rental.contract', '',ondelete='cascade', readonly=True)

