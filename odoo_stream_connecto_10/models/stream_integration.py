from odoo import models, fields, _
from odoo.exceptions import UserError
import requests
import uuid
from datetime import timedelta
import logging

_logger = logging.getLogger(__name__)


class StreamIntegration(models.Model):
    _name = "stream.integration"
    _description = "Stream Integration"

    name = fields.Char(required=True)

    company_id = fields.Many2one(
        "res.company",
        required=True,
        ondelete="cascade"
    )

    stream_client_id = fields.Char("Stream Client ID")
    stream_client_secret = fields.Char("Stream Client Secret")
    stream_base_url = fields.Char("Stream Base URL")

    stream_access_token = fields.Text(readonly=True)
    stream_token_expiry = fields.Datetime(readonly=True)
    stream_connected = fields.Boolean(readonly=True)

    sender_partner_id = fields.Many2one(
        'res.partner',
        string='Sender Contact'
    )

    label_reference = fields.Char(string="Label Reference")


    shipping_service_ids = fields.Many2many(
        'sale.shipping.services',
        string='Shipping Services'
    )


    def action_stream_authenticate(self):
        self.ensure_one()

        if not self.stream_client_id or not self.stream_client_secret:
            raise UserError(_("Missing Client ID or Client Secret"))

        base_url = (
            self.stream_base_url.strip()
            if self.stream_base_url
            else "https://www.demo.go2stream.net"
        )

        url = f"{base_url}/api/oauth"

        payload = {
            "grant_type": "client_credentials",
            "client_id": self.stream_client_id.strip(),
            "client_secret": self.stream_client_secret.strip(),
        }

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Stream-Nonce": uuid.uuid4().hex,
        }

        try:
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=60,
            )

            _logger.info("STATUS %s", response.status_code)
            _logger.info("BODY %s", response.text)

            if "text/html" in response.headers.get("Content-Type", ""):
                raise UserError(
                    _("Stream returned HTML instead of JSON.")
                )

            if not response.ok:
                raise UserError(
                    _("Authentication Failed:\n%s") % response.text
                )

            data = response.json()

            expiry = fields.Datetime.now() + timedelta(
                seconds=data.get("expires_in", 3600)
            )

            self.write({
                "stream_access_token": data.get("access_token"),
                "stream_token_expiry": expiry,
                "stream_connected": True,
            })

            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Success"),
                    "message": _("Stream connected successfully."),
                    "type": "success",
                }
            }

        except requests.exceptions.RequestException as e:
            raise UserError(
                _("Network error: %s") % str(e)
            )
        
    def action_open_form(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'current', # Use 'new' to open in a popup modal
        }
