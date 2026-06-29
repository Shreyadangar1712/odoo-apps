from odoo import fields, models
from odoo.exceptions import UserError
import requests
import logging

_logger = logging.getLogger(__name__)



class HrEmployee(models.Model):
    _inherit = 'hr.employee'   

    github_user_name = fields.Char(string="Github Username")