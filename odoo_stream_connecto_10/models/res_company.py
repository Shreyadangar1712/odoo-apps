import requests
import uuid
from datetime import timedelta
from odoo import models, fields, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = "res.company"

    stream_client_id = fields.Char("Stream Client ID")
    stream_client_secret = fields.Char("Stream Client Secret")
    stream_base_url = fields.Char(string="Stream Base URL")
    stream_webhook_url = fields.Char(
        string="Stream Webhook URL"
    )


    stream_access_token = fields.Text(readonly=True)
    stream_token_expiry = fields.Datetime(readonly=True)
    stream_connected = fields.Boolean(readonly=True)
    onHandset =fields.Boolean(default=True)

    def action_stream_authenticate(self):
        self.ensure_one()

        if not self.stream_client_id or not self.stream_client_secret:
            raise UserError(_("Missing Client ID or Client Secret"))

        base_url = self.stream_base_url or "https://www.demo.go2stream.net"
        api_root = "api"
        auth_endpoint = "oauth"

        url = f"{base_url}/{api_root}/{auth_endpoint}"

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

        _logger.info("STREAM AUTH URL: %s", url)
        _logger.info("STREAM PAYLOAD: %s", payload)
        _logger.info("STREAM HEADERS: %s", headers)

        try:
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=60,
            )
            _logger.info("ORDER STATUS: %s", response.status_code)
            _logger.info("ORDER HEADERS: %s", dict(response.headers)) 
            _logger.info("ORDER RESPONSE: %s", response.text[:500])   

            _logger.info("STATUS: %s", response.status_code)
            _logger.info("RESPONSE TEXT: %s", response.text)

            if "text/html" in response.headers.get("Content-Type", ""):
                raise UserError(
                    _("Stream returned HTML login page instead of API response. Wrong endpoint or missing API base path.")
                )

            if not response.ok:
                raise UserError(_("Authentication Failed: %s") % response.text)

            data = response.json()

            expiry = fields.Datetime.now() + timedelta(
                seconds=data.get("expires_in", 3600)
            )

            self.write({
                "stream_access_token": data.get("access_token"),
                "stream_token_expiry": expiry,
                "stream_connected": True,
            })

            success_form = self.env.ref('odoo_stream_connector.connection_successfull_view', False)
            return {
                        'name': _('Notification'),
                        'type': 'ir.actions.act_window',
                        'view_type': 'form',
                        'view_mode': 'form',
                        'res_model': 'res.company.message',
                        'views': [(success_form.id, 'form')],
                        'view_id': success_form.id,
                        'target': 'new',
                    }

        except requests.exceptions.RequestException as e:
            _logger.exception("Stream connection error")
            raise UserError(_("Network error connecting to Stream: %s") % str(e))


    def action_stream_fetch_depots(self):
        self.ensure_one()

        if not self.stream_access_token or self.stream_token_expiry < fields.Datetime.now():
            try:
                self.action_stream_authenticate() 
            except UserError:
                raise UserError(_("Stream access token is missing or expired. Please authenticate first."))

        base_url = self.stream_base_url or "https://www.demo.go2stream.net"
        api_root = "api"
        depots_endpoint = "/depots/depots"

        url = f"{base_url}/{api_root}/{depots_endpoint}"

        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.stream_access_token}",
            "Stream-Nonce": uuid.uuid4().hex,
            'Stream-party': self.stream_client_id,  
        }

        _logger.info("STREAM DEPOTS URL: %s", url)
        _logger.info("STREAM HEADERS: %s", headers)

        

        try:
            response = requests.get(
                url,
                headers=headers,
                timeout=60,
            )
            _logger.info("DEPOTS STATUS: %s", response.status_code)
            _logger.info("DEPOTS HEADERS: %s", dict(response.headers))  
            _logger.info("DEPOTS RESPONSE: %s", response.text[:1000])   

            if "text/html" in response.headers.get("Content-Type", ""):
                raise UserError(
                    _("Stream returned HTML login page instead of API response. Wrong endpoint or missing API base path.")
                )

            if not response.ok:
                raise UserError(_("Failed to fetch depots from Stream: %s") % response.text)

            data = response.json()
            depots = data.get("response", {}).get("depots", [])

            for depot in depots:

                vals = {
                    # Depot
                    "external_id": depot.get("id"),
                    "name": depot.get("address", {}).get("name"),

                    # Address
                    "address1": depot.get("address", {}).get("address1"),
                    "address2": depot.get("address", {}).get("address2"),
                    "address3": depot.get("address", {}).get("address3"),
                    "city": depot.get("address", {}).get("address4"),
                    "state": depot.get("address", {}).get("address5"),
                    "country": depot.get("address", {}).get("country"),
                    "postcode": depot.get("address", {}).get("postcode"),
                    "latitude": depot.get("address", {}).get("lat"),
                    "longitude": depot.get("address", {}).get("long"),

                    # Contact
                    "contact_name": depot.get("contact", {}).get("name"),
                    "phone": depot.get("contact", {}).get("tel1"),
                    "phone2": depot.get("contact", {}).get("tel2"),
                    "mobile": depot.get("contact", {}).get("mobile"),
                    "email": depot.get("contact", {}).get("email"),

                    # Stock
                    "stock_location_id": depot.get("stockLocation", {}).get("id"),
                    "stock_location_name": depot.get("stockLocation", {}).get("name"),

                   
                }

                for method in depot.get("deliveryMethods", []):
                    delivery = self.env["stream.depot.delivery.method"].search(
                        [("steam_delivery", "=", method.get("id"))],
                        limit=1
                    )

                    if not delivery:
                        delivery = self.env["stream.depot.delivery.method"].create({
                            "external_id": method.get("id"),
                            "steam_delivery": method.get("id"),
                            "name": method.get("name"),
                        })

                existing = self.env["stream.depot"].search(
                    [("external_id", "=", depot.get("id"))],
                    limit=1
                )

                if existing:
                    existing.write(vals)
                else:
                    self.env["stream.depot"].create(vals)

            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Success"),
                    "message": _("Depots fetched and created successfully."),
                    "type": "success",
                }
            }

        except requests.exceptions.RequestException as e:
            _logger.exception("Error fetching depots from Stream")
            raise UserError(_("Network error fetching depots from Stream: %s") % str(e))
        
    
    def action_register_webhook(self):
        self.ensure_one()

        base_url = self.stream_base_url or "https://www.demo.go2stream.net"

        if not self.stream_access_token or self.stream_token_expiry < fields.Datetime.now():
            try:
                self.action_stream_authenticate()  # Ensure we have a valid token before fetching depots
            except UserError:
                raise UserError(_("Stream access token is missing or expired. Please authenticate first."))


        url = f"{base_url}/api//webhooks/webhooks"
     
        payload = {
        "event": "ORDERSTATUS",
        "event_type": "CONSHEADER",
        "url_path": f"{self.stream_webhook_url}/webhooks/stream",
        "http_method": "POST",
        "content_type": "application/json"
    }

        headers = {
        "Authorization": f"Bearer {self.stream_access_token}",
        "Content-Type": "application/json",
        "Stream-Nonce": uuid.uuid4().hex,
        "Stream-Party": self.stream_client_id.strip()
        }

        _logger.info("========== WEBHOOK REGISTRATION START ==========")
        _logger.info("Webhook URL: %s", url)
        _logger.info("Request Headers: %s", headers)
       

        try:
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=30,
            )

            _logger.info("Response Status: %s", response.status_code)
            _logger.info("Response Headers: %s", dict(response.headers))
            _logger.info("Response Body:\n%s", response.text)

            response.raise_for_status()

            _logger.info("Webhook registration completed successfully.")
            _logger.info("========== WEBHOOK REGISTRATION END ==========")

            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "Success",
                    "message": "Webhook registered successfully.",
                    "type": "success",
                    "sticky": False,
                },
            }

        except requests.exceptions.HTTPError as e:
            _logger.exception(
                "HTTP Error while registering webhook. "
                "Status=%s Response=%s",
                getattr(response, "status_code", "N/A"),
                getattr(response, "text", "N/A"),
            )
            raise UserError(f"HTTP Error:\n{str(e)}")

        except requests.exceptions.Timeout:
            _logger.exception("Webhook request timeout after 30 seconds")
            raise UserError("Webhook request timed out.")

        except requests.exceptions.RequestException as e:
            _logger.exception("Request failed")
            raise UserError(f"Request failed:\n{str(e)}")

        except Exception as e:
            _logger.exception("Unexpected error during webhook registration")
            raise UserError(f"Unexpected error:\n{str(e)}")

        finally:
            _logger.info("========== WEBHOOK REGISTRATION FINISHED ==========")


    
    def retrive_register_webhook(self):
        self.ensure_one()


        if not self.stream_access_token or self.stream_token_expiry < fields.Datetime.now():
            try:
                self.action_stream_authenticate()  # Ensure we have a valid token before fetching depots
            except UserError:
                raise UserError(_("Stream access token is missing or expired. Please authenticate first."))


        base_url = self.stream_base_url or "https://www.demo.go2stream.net"
        url = f"{base_url}/api//webhooks/webhooks"


        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Stream-Nonce": uuid.uuid4().hex,
            'Stream-party': self.stream_client_id,
            "Authorization": f"Bearer {self.stream_access_token}",
        }

        try:
            _logger.info("========== STREAM WEBHOOK REGISTER ==========")
            _logger.info("Request URL: %s", url)

            response = requests.get(
                url,
                headers=headers,
                timeout=30,
            )

            _logger.info("Status Code: %s", response.status_code)
            _logger.info("Response: %s", response.text)

            response.raise_for_status()

            result = response.json()

            if not result.get("response", {}).get("valid"):
                errors = result.get("response", {}).get("errors", [])
                raise UserError(
                    "Webhook registration failed:\n%s"
                    % "\n".join(errors)
                )

            subscriptions = (
                result
                .get("response", {})
                .get("subscriptions", [])
            )

            subscription_ids = [
                str(sub.get("id"))
                for sub in subscriptions
            ]

            _logger.info(
                "Webhook registered successfully: %s",
                subscription_ids,
            )

            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "Success",
                    "message": (
                        "Webhook registered successfully. "
                        f"Subscription IDs: {', '.join(subscription_ids)}"
                    ),
                    "type": "success",
                    "sticky": False,
                },
            }

        except Exception as e:
            _logger.exception("Webhook registration failed")
            raise UserError(str(e))