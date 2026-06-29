
import requests
import uuid
import logging
import json
from datetime import datetime
from odoo.fields import Datetime
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    stream_exported = fields.Boolean(
        string="Stream Exported",
        default=False
    )

    booking_required = fields.Boolean(
        string="Booking Required",
        default=False
    )

    update_addresses = fields.Boolean(
        string="Update Addresses",
        default=False
    )

    order_type = fields.Selection([
        ('delivery', 'Delivery'),
        ('collection', 'Collection'),
        ('multi', 'Multi'),
    ], string="Stream Order Type", default='collection')

    stream_consignment_no = fields.Char("Stream Consignment No", readonly=True, copy=False)
    stream_tracking_id = fields.Char("Stream Tracking ID", readonly=True, copy=False)
    stream_tracking_url = fields.Char("Stream Tracking URL", readonly=True, copy=False)
    stream_services = fields.Many2many(
        'stream.service',
        string='Stream Shipping Services',
        copy=False,
    )

    run_detail_ids = fields.One2many(
        "stream.run.details",
        "sale_order_id",
        string="Run Details",
    )
    stream_status = fields.Selection([
        ('unconfirmed', 'Unconfirmed'),
        ('confirmed', 'Confirmed'),
        ('planned', 'Planned'),
        ('released', 'Released'),
        ('held', 'Held'),
        ('collected', 'Collected'),
        ('part_collected', 'Part Collected'),
        ('delivered', 'Delivered'),
        ('part_delivered', 'Part Delivered'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], string="Stream Status",readonly=True)

    stream_last_event = fields.Char(
        string="Last Stream Event",
        readonly=True,
    )

    stream_last_update = fields.Datetime(
        string="Last Stream Update",
        readonly=True,
    )
  
    @api.model
    def cron_export_sale_orders_to_stream(self):
        orders = self.search([
            ('state', '=', 'sale'),
            ('stream_exported', '=', False),
        ])
        _logger.info("STREAM CRON: Found %s orders", len(orders))

        for order in orders:
            try:
                # Call directly on single record, bypass popup return
                order._export_single_order_to_stream()
                _logger.info("STREAM CRON SUCCESS: %s", order.name)
            except Exception as e:
                _logger.exception("STREAM CRON FAILED: %s | %s", order.name, str(e))

  
    def action_export_to_stream(self):
        try:
            # Process all selected orders first, then return popup
            for order in self:
                order._export_single_order_to_stream()


            # Only reached if ALL orders exported successfully
            success_form = self.env.ref('odoo_stream_connector.export_successfull_view', False)
            _logger.info("SUCCESS FORM ID: %s", success_form.id if success_form else "Not Found")
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
           
        except Exception as e:
            _logger.exception("STREAM EXPORT FAILED: %s | %s", self.name, str(e))
            raise ValidationError(f"Stream export failed: {str(e)}")

    def _export_single_order_to_stream(self):
        order = self  

        try:
            if order.state != 'sale':
                raise ValidationError(f"Order {order.name} must be confirmed before exporting.")

            if order.stream_exported:
                raise ValidationError(f"Order {order.name} has already been exported to Stream.")

            if not order.order_line:
                raise ValidationError(f"Order {order.name} has no order lines.")

            company = order.company_id

            if not company.stream_base_url:
                raise ValidationError("Stream Base URL is not configured.")
            if not company.stream_client_id:
                raise ValidationError("Stream Client ID is not configured.")
            if not company.stream_client_secret:
                raise ValidationError("Stream Client Secret is not configured.")

            partner = order.partner_id
            if not partner:
                raise ValidationError(f"Order {order.name} has no customer.")
            if not partner.name:
                raise ValidationError("Customer name is missing.")
            if not partner.street:
                raise ValidationError("Customer street address is required.")
            if not partner.zip:
                raise ValidationError("Customer postcode is required.")

            for line in order.order_line:
                if line.product_uom_qty <= 0:
                    raise ValidationError(
                        f"Invalid quantity for product: {line.product_id.display_name}"
                    )

            base_url = company.stream_base_url.rstrip("/")
            client_id = company.stream_client_id.strip()
            client_secret = company.stream_client_secret.strip()

            # AUTHENTICATE
            session = requests.Session()

            auth_res = session.post(
                f"{base_url}/api/oauth",
                json={
                    "grant_type": "client_credentials",
                    "client_id": client_id,
                    "client_secret": client_secret,
                },
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "Stream-Nonce": str(uuid.uuid4()),
                },
                timeout=60,
                allow_redirects=False,
            )

            _logger.info("AUTH STATUS: %s", auth_res.status_code)
            _logger.info("AUTH RESPONSE: %s", auth_res.text[:300])

            if auth_res.status_code in (301, 302, 303, 307, 308):
                raise ValidationError(
                    "Stream auth redirected — check Base URL. Location: %s"
                    % auth_res.headers.get("Location", "Unknown")
                )

            if "text/html" in auth_res.headers.get("Content-Type", ""):
                raise ValidationError("Stream auth returned HTML — check Base URL.")

            auth_res.raise_for_status()

            token = auth_res.json().get("access_token")
            if not token:
                raise ValidationError("No access token received from Stream.")

            _logger.info("TOKEN RECEIVED: %s...", token[:15])

            # BUILD PAYLOAD
            payload = self._build_stream_payload(order, client_id)
            _logger.info("ORDER TYPE: %s", order.order_type)
            _logger.info("ORDER PAYLOAD:\n%s", json.dumps(payload, indent=2))

            # POST ORDER
            res = session.post(
                f"{base_url}/api/orders/orders",
                json=payload,
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "Stream-Nonce": str(uuid.uuid4()),
                    "Stream-Party": client_id,
                    "Authorization": f"Bearer {token}",
                },
                timeout=60,
                allow_redirects=False,
            )

            _logger.info("ORDER STATUS: %s", res.status_code)
            _logger.info("ORDER RESPONSE HEADERS: %s", dict(res.headers))
            _logger.info("ORDER RESPONSE: %s", res.text[:1000])

            if res.status_code in (301, 302, 303, 307, 308):
                raise ValidationError(
                    "Stream order endpoint redirected — check credentials/permissions. Location: %s"
                    % res.headers.get("Location", "Unknown")
                )

            if "text/html" in res.headers.get("Content-Type", ""):
                raise ValidationError("Stream returned HTML instead of JSON — check credentials.")

            if res.status_code not in (200, 201):
                raise ValidationError(f"Stream error {res.status_code}: {res.text[:300]}")

            # HANDLE RESPONSE
            response_data = res.json()
            api_response = response_data.get("response", {})

            _logger.info("STREAM FULL RESPONSE: %s", response_data)

            if not api_response:
                raise ValidationError("Empty response received from Stream.")

            if not api_response.get("valid"):
                # Collect all error-severity messages to show user
                errors = [
                    e.get("message", "")
                    for e in api_response.get("errors", [])
                    if e.get("severity") == "error"
                ]
                raise ValidationError(
                    "Stream rejected order %s:\n%s" % (order.name, "\n".join(errors) or str(api_response))
                )

            # Log warnings (non-blocking)
            for err in api_response.get("errors", []):
                _logger.warning(
                    "STREAM WARNING [%s] %s: %s",
                    err.get("severity"), err.get("code"), err.get("message"),
                )

            consignment_no = api_response.get("consignmentNo", "")
            tracking_id = api_response.get("trackingId", "")
            tracking_url = api_response.get("trackingURL", "")

            if not consignment_no:
                raise ValidationError("No consignment number received from Stream.")

            # SAVE & LOG SUCCESS
            order.write({
                "stream_exported": True,
                "stream_consignment_no": consignment_no,
                "stream_tracking_id": tracking_id,
                "stream_tracking_url": tracking_url,
            })

          

            _logger.info("STREAM SUCCESS | Order: %s | Consignment: %s", order.name, consignment_no)
            return True
        
        except Exception as e:
            _logger.exception("STREAM EXPORT FAILED | Order: %s | Error: %s", order.name, str(e))
            raise

    # PAYLOAD DISPATCHER
    def _build_stream_payload(self, order, client_id):
        if order.order_type == 'collection':
            return self._build_collection_payload(order, client_id)
        if order.order_type == 'delivery':
            return self._build_delivery_payload(order, client_id)
        if order.order_type == 'multi':
            return self._build_multi_payload(order, client_id)
        raise ValidationError("Invalid Stream Order Type selected.")

    # COLLECTION PAYLOAD
    def _build_collection_payload(self, order, client_id):
        partner = order.partner_id
        return {
            "header": {
                "orderNo": order.name,
                "orderDate": fields.Date.today().isoformat(),
                "partner": {"id": client_id, "name": order.company_id.name},
                "orderType": "COLLECTION",
                "serviceLevel": "Standard",
                "services": self._services(order),
                "customerOrderNo": order.name,
                "customer": {
                    "name": partner.name,
                    "address": self._address(partner),
                    "contact": self._contact(partner),
                },
            },
            "collection": {
                "address": self._address(partner),
                "contact": self._contact(partner),
                "required": self._required(),
                "collectionMethod": self._collection_method(order),
                "items": self._items(order),
            },
        }

    
    def _build_delivery_payload(self, order, client_id):
        partner = order.partner_id
        delivery_partner = order.partner_shipping_id or partner
        return {
            "header": {
                "orderNo": order.name,
                "orderDate": fields.Date.today().isoformat(),
                "partner": {"id": client_id, "name": order.company_id.name},
                "orderType": "DELIVERY",
                "serviceLevel": "Standard",
                "services": self._services(order),
                "customerOrderNo": order.name,
                "updateAddresses": order.update_addresses,
                "customer": {
                    "name": partner.name,
                    "address": self._address(partner),
                    "contact": self._contact(partner),
                },
            },
            "delivery": {
                "address": self._address(delivery_partner),
                "contact": self._contact(delivery_partner),
                "required": self._required(),
                "items": self._items(order),
                "deliveryMethod": self._delivery_method(order),
                "bookingRequired": order.booking_required,
                "updateAddresses": order.update_addresses,
            },
        }
    def _delivery_method(self, order):
        return order.carrier_id.steam_delivery.name if order.carrier_id else ""


    # MULTI PAYLOAD
    # NOTE: delivery legs are NESTED inside collection.delivery[] array
    def _build_multi_payload(self, order, client_id):
        partner = order.partner_id
        delivery_partner = order.partner_shipping_id or partner
        company_partner = order.company_id.partner_id

        return {
            "header": {
                "orderNo": order.name,
                "orderDate": fields.Date.today().isoformat(),
                "partner": {"id": client_id, "name": order.company_id.name},
                "orderType": "MULTI",
                "serviceLevel": "Standard",
                "services": self._services(order),
                "customerOrderNo": order.name,
                
                "customer": {
                    "name": partner.name,
                    "address": self._address(partner),
                    "contact": self._contact(partner),
                },
            },
            "collection": {
                "address": self._address(company_partner),   # collect FROM warehouse
                "contact": self._contact(company_partner),
                "required": self._required(),
                "collectionMethod": self._collection_method(order),
                "delivery": [                                 # deliver TO customer (array!)
                    {
                        "address": self._address(delivery_partner),
                        "contact": self._contact(delivery_partner),
                        "required": self._required(),
                        "items": self._items(order),
                    }
                ],
            },
        }

    # HELPERS
    def _address(self, partner):
        return {
            "name": partner.name or "",
            "address1": partner.street or "",
            "address2": partner.street2 or "",
            "address3": partner.city or "",
            "address4": partner.state_id.name if partner.state_id else "",
            "address5": "",

            "postcode": partner.zip or "",
            "country": partner.country_id.code if partner.country_id else "GB",

            "addressRef": None,
            "altLat": None,
            "altLong": None,
            "externalAddressId": None,
            "lat": None,
            "long": None,
            "locationNotes": None,
            "nuts": None,
            "vehicleType": None,
            "what3words": None,
        }
    def _contact(self, partner):
        return {
            "name": partner.name or "",
            "tel1": partner.phone or "",

            "mobile": partner.phone or "",
            "email": partner.email or "",
         
        }

    def _required(self):
        return {
            "fromDateTime": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "toDateTime": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
    def _services(self, order):
        return [
            {"code": service.name}
            for service in order.stream_services
        ]

    def _items(self, order):
        today = fields.Date.today()
        company = order.company_id
        return [
            {
                "sequence": idx + 1,
                "code": line.product_id.default_code or line.product_id.name,
                "description": (line.name or "")[:50],
                "quantity": int(line.product_uom_qty),
                "weight": float(line.stream_weight),
                "cube": float(line.stream_cube),
                "onHandDate": (today.strftime("%Y-%m-%d")
                        if company.onHandset
                        else None
                    ),
                "stockLocation": line.stream_stock_location_id.name if line.stream_stock_location_id else "",
            }
            for idx, line in enumerate(order.order_line)
        ]
    def _collection_method(self, order):
        return order.carrier_id.steam_delivery.name if order.carrier_id else ""
    
    def _parse_stream_datetime(self,value):
        if not value or value == "0":
            return False

        try:
            # Stream sends: 2026-06-20T07-00Z
            return datetime.strptime(
                value,
                "%Y-%m-%dT%H-%MZ"
            )
        except Exception:
            return False



    def action_sync_run_details(self):
        self.ensure_one()

        if not self.stream_consignment_no:
            raise ValidationError(
                _("No Stream Consignment Number found.")
            )

        company = self.company_id

        base_url = company.stream_base_url.rstrip("/")
        client_id = company.stream_client_id.strip()
        client_secret = company.stream_client_secret.strip()

        session = requests.Session()

        # Authenticate
        auth_res = session.post(
            f"{base_url}/api/oauth",
            json={
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
            },
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Stream-Nonce": str(uuid.uuid4()),
            },
            timeout=60,
        )

        auth_res.raise_for_status()

        token = auth_res.json().get("access_token")

        if not token:
            raise ValidationError(_("Failed to get Stream token."))

        # Retrieve Order Details
        response = session.get(
            f"{base_url}/api/orders/orders/{self.stream_consignment_no}",
            headers={
                "Accept": "application/json",
                "Stream-Nonce": str(uuid.uuid4()),
                "Stream-Party": client_id,
                "Authorization": f"Bearer {token}",
            },
            timeout=60,
        )

        response.raise_for_status()

        data = response.json()

        if not data.get("response", {}).get("valid"):
            raise ValidationError(_("Stream returned invalid response."))

        order_data = data.get("response", {}).get("order", {})
        groups = order_data.get("groups", [])

        if not groups:
            raise ValidationError(_("No groups found in Stream response."))

        for group in groups:

            run = group.get("runDetails")

            if not run:
                continue


            _logger.info(f'{order_data}')

            vals = {
                "sale_order_id": self.id,

                "stream_run_id": run.get("id"),
                "description": run.get("description"),
                "group_sequence": run.get("groupSequence"),

                "vehicle": run.get("vehicle"),
                "vehicle_name": run.get("vehicleName"),
                "vehicle_type": run.get("vehicleType"),

                "driver": run.get("driver"),
                "driver_name": run.get("driverName"),

                "dispatched": run.get("dispatched"),
                "departed": run.get("departed"),
                "completed": run.get("completed"),
                "start_postcode": run.get("start", {}).get("postcode"),
                "start_lat": run.get("start", {}).get("lat"),
                "start_long": run.get("start", {}).get("long"),
                "start_actual_datetime": self._parse_stream_datetime(
                        run.get("start", {}).get("actualDateTime")
                    ),
                    "start_planned_datetime": self._parse_stream_datetime(
                        run.get("start", {}).get("plannedDateTime")
                    ),
                    "end_actual_datetime": self._parse_stream_datetime(
                        run.get("end", {}).get("actualDateTime")
                    ),
                    "end_planned_datetime": self._parse_stream_datetime(
                        run.get("end", {}).get("plannedDateTime")
                    ),
   
                "end_postcode": run.get("end", {}).get("postcode"),
                "end_lat": run.get("end", {}).get("lat"),
                "end_long": run.get("end", {}).get("long"),
            }

            run_record = self.env["stream.run.details"].search(
                [("sale_order_id", "=", self.id)],
                limit=1,
            )

            if run_record:
                run_record.write(vals)
            else:
                self.env["stream.run.details"].create(vals)

        return True
    


#cron job to sync run details
    @api.model
    def cron_sync_stream_run_details(self):

        orders = self.search([
            ("stream_consignment_no", "!=", False),
        ])

        _logger.info(
            "STREAM RUN DETAILS CRON STARTED | Orders Found=%s",
            len(orders),
        )

        for order in orders:
            try:

                existing_run = self.env[
                    "stream.run.details"
                ].search(
                    [
                        ("sale_order_id", "=", order.id)
                    ],
                    limit=1,
                )

                if existing_run:
                    _logger.info(
                        "Skipping %s | Run Details Already Exist",
                        order.name,
                    )
                    continue

                _logger.info(
                    "Fetching Run Details For Order %s",
                    order.name,
                )

                order.action_sync_run_details()

                _logger.info(
                    "Run Details Synced For %s",
                    order.name,
                )

            except Exception as e:

                _logger.exception(
                    "Failed Syncing Run Details For %s | %s",
                    order.name,
                    str(e),
                )

        _logger.info(
            "STREAM RUN DETAILS CRON COMPLETED"
        )

        return True
    

    def update_stream_status(
        self,
        event_code,
        event_desc=None,
    ):
        self.ensure_one()

        _logger.info(
            "INSIDE update_stream_status()"
        )

        _logger.info(
            "ORDER: %s",
            self.name
        )

        _logger.info(
            "EVENT CODE: %s",
            event_code
        )

        status_mapping = {
            "UNCONFIRMED": "unconfirmed",
            "CONFIRMED": "confirmed",
            "PLANNED": "planned",
            "RELEASED": "released",
            "HELD": "held",
            "COLLECTED": "collected",
            "PARTCOLLECTED": "part_collected",
            "DELIVERED": "delivered",
            "PARTDELVRD": "part_delivered",
            "COMPLETED": "completed",
            "CANCELLED": "cancelled",
        }

        vals = {
            "stream_status": status_mapping.get(
                event_code
            ),
            "stream_last_event": (
                event_desc or event_code
            ),
            "stream_last_update": (
                fields.Datetime.now()
            ),
        }

        _logger.info(
            "VALUES TO WRITE: %s",
            vals
        )

        self.write(vals)

        _logger.info(
            "WRITE SUCCESSFUL"
        )

        self.message_post(
            body=f"Stream Status Updated: {event_code}"
        )

        _logger.info(
            "CHATTER MESSAGE POSTED"
        )

        _logger.info(
            "STREAM STATUS UPDATED | Order=%s | Status=%s",
            self.name,
            event_code,
        )
        

    @api.model
    def cron_sync_stream_order_status(self):

        orders = self.search([
            ("stream_consignment_no", "!=", False),
            ("stream_exported", "=", True),
        ])

        _logger.info(
            "STREAM STATUS CRON STARTED | Orders Found=%s",
            len(orders)
        )

        for order in orders:
            try:
                order._fetch_stream_order_status()

            except Exception:
                _logger.exception(
                    "FAILED TO SYNC STATUS | %s",
                    order.name
                )


    def _fetch_stream_order_status(self):

        self.ensure_one()

        company = self.company_id

        base_url = company.stream_base_url.rstrip("/")
        client_id = company.stream_client_id.strip()
        client_secret = company.stream_client_secret.strip()

        session = requests.Session()

        auth_res = session.post(
            f"{base_url}/api/oauth",
            json={
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
            },
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Stream-Nonce": str(uuid.uuid4()),
            },
            timeout=60,
        )

        auth_res.raise_for_status()

        token = auth_res.json().get("access_token")

        if not token:
            raise ValidationError(
                "Unable to get Stream token."
            )

        response = session.get(
            f"{base_url}/api/orders/status/{self.stream_consignment_no}",
            headers={
                "Accept": "application/json",
                "Stream-Nonce": str(uuid.uuid4()),
                "Stream-Party": client_id,
                "Authorization": f"Bearer {token}",
            },
            timeout=60,
        )

        _logger.info(
            "STATUS API RESPONSE [%s]: %s",
            self.name,
            response.text
        )

        response.raise_for_status()

        data = response.json()

        result = data.get("response", {})

        if not result.get("valid"):
            _logger.warning(
                "INVALID RESPONSE FOR %s",
                self.name,
            )
            return

        stream_status = result.get("orderStatus")

        _logger.info(
            "STREAM STATUS [%s] = %s",
            self.name,
            stream_status
        )

        if stream_status:
            self.update_stream_status(
                stream_status,
                f"Updated from Stream Cron ({stream_status})"
            )
        