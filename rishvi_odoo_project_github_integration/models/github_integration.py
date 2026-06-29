from odoo import models, fields

class GithubRepository(models.Model):
    _name = 'github.repository'



    name = fields.Char(required=True)
    repo_url = fields.Char()
    full_name = fields.Char()


  