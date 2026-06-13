from odoo import fields,models

class XeroAccount(models.Model):
    _name = 'xero.account'
    _description = 'Xero Imported Accounts'
    _rec_name = 'name'

    name = fields.Char(string='Account Name')
    code = fields.Char(string='Account Code')
    xero_account_id = fields.Char(string='Xero Account ID')
    account_type = fields.Char(string='Account Type')
    xero_account_type = fields.Many2one('xero.account.account', string='Xero Account Type')
    # xero_tax_type = fields.Many2one('xero.tax.type', string='Tax Type')
    xero_tax_type_for_accounts = fields.Many2one('xero.tax.type', string="Tax Type")
    active = fields.Boolean(default=True)


    xero_description = fields.Char(string='Description')
    enable_payments_to_account = fields.Boolean(string='Enable Payments')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    # status = fields.Selection([
    #     ('imported', 'Imported'),
    #     ('synced', 'Synced'),
    # ], default='imported', string='Status')



    def _compute_display_name(self):
        for record in self:
            record.display_name = f"{record.code} {record.name}"