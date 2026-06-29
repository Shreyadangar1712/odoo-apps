from odoo import models, fields, api
from odoo.exceptions import ValidationError


class StreamService(models.Model):
    _name = "stream.service"
    _description = "service"


    name = fields.Char(
        string="Service Name",
        required=True
    )



    