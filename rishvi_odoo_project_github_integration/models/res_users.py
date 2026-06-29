from odoo import fields, models

class ResUsers(models.Model):
    _inherit = "res.users"

    github_access = fields.Boolean(string="Github Operations Access")