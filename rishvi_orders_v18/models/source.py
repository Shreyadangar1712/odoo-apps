from odoo import models, fields


class SourceDetails(models.Model):
    _name = 'source.details'


    name = fields.Char(string='Name', required=True)
