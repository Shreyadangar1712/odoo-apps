from odoo import api, fields, models, _

class XeroLogger(models.Model):
    _name = 'xero.logger'
    _rec_name = 'odoo_name'
    _description = 'Xero Logger'

    odoo_name = fields.Char('Name')
    odoo_object = fields.Char('Object')
    message = fields.Char('Message')
    activity = fields.Char('Activity')
    xero_ref = fields.Char('Xero Ref')
    status_code = fields.Char('Status Code')
    status = fields.Selection([('failed', 'Failed'), ('done', 'Done')])