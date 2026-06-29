from odoo import models


class ResCompanyMessage(models.TransientModel):
    _name='res.company.message'
    _description = 'success/failure messages'