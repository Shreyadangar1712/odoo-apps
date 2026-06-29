from odoo import models, fields, _
from odoo.exceptions import UserError
import requests
import uuid
from datetime import timedelta
import logging

_logger = logging.getLogger(__name__)


class StreamIntegration(models.Model):
    _name = "stream.postal.services"
    _description = "Stream Postal Services"

    integration_id = fields.Many2one(
        "stream.integration",
        string="Integration",
        required=True
    )

    service_name = fields.Char(
        string="Service Name",
        required=True
    )

    default_location = fields.Char(
        string="Default Location",
        required=True
    )

    default_dimension_unit = fields.Selection([
        ("meter", "Meter"),
        ("cm", "Centimeter"),
        ("inch", "Inch"),
    ], default="meter", required=True)

    order_type = fields.Selection([
        ("delivery", "Delivery"),
        ("pickup", "Pickup"),
    ], default="delivery", required=True)

    label_type = fields.Selection([
        ("portrait", "Portrait Standard"),
        ("landscape", "Landscape"),
    ], default="portrait", required=True)

    copies = fields.Integer(
        default=1,
        required=True
    )

    service = fields.Char(
        string="Service"
    )

    service_level = fields.Selection([
        ("standard", "Standard"),
        ("express", "Express"),
    ], default="standard")



    def action_open_form(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'current', # Use 'new' to open in a popup modal
        }
    
    def action_update_postal_service(self):
        pass