from odoo import models, fields


class SubSourceDetails(models.Model):
    _name = 'sub.source.details'


    name = fields.Char(string='Name', required=True)
