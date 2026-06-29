import logging

from odoo import http
from odoo.http import request
import json


_logger = logging.getLogger(__name__)


class StreamWebhookController(http.Controller):

    @http.route(
        "/webhooks/webhooks",
        type="json",
        auth="public",
        methods=["POST"],
        csrf=False
    )
    def create_webhook(self, **payload):

        _logger.info(
            "Webhook Received | Payload: %s",payload)

        return {
            "response": {
                "valid": True,
                "errors": [],
                "id": None,
            }
        }
    @http.route(
        "/receive/stream",
        type="json",
        auth="public",
        methods=["POST"],
        csrf=False
    )
    def recevice_webhook(self, **payload):

        _logger.info(
            "Webhook Received | Payload: %s",payload)

        return {
            "response": {
                "valid": True,
                "errors": [],
                "id": None,
            }
        }

    @http.route(
    "/webhooks/stream",
    type="http",
    auth="public",
    methods=["POST"],
    csrf=False,
)
    def stream_webhook(self, **kwargs):

        try:
            payload = json.loads(
                request.httprequest.data.decode("utf-8")
            )

            _logger.info("############################################")
            _logger.info("STREAM WEBHOOK RECEIVED")
            _logger.info(
                json.dumps(payload, indent=4)
            )
            _logger.info("############################################")

            event = payload.get("event", {})
            order = payload.get("order", {})

            event_code = event.get("event_code")
            event_desc = event.get("event_desc")
            consignment_no = order.get("id")

            _logger.info(
                "EVENT CODE: %s",
                event_code
            )
            _logger.info(
                "EVENT DESC: %s",
                event_desc
            )
            _logger.info(
                "CONSIGNMENT NO: %s",
                consignment_no
            )

            if not consignment_no:
                _logger.info(
                    "NO CONSIGNMENT NUMBER FOUND IN WEBHOOK"
                )
                return request.make_json_response(
                    {"success": False}
                )

            sale_order = request.env[
                "sale.order"
            ].sudo().search(
                [
                    (
                        "stream_consignment_no",
                        "=",
                        consignment_no,
                    )
                ],
                limit=1,
            )

            _logger.info(
                "SALE ORDER SEARCH RESULT: %s",
                sale_order.name if sale_order else "NOT FOUND"
            )

            if not sale_order:
                _logger.info(
                    "NO SALE ORDER FOUND FOR %s",
                    consignment_no,
                )

                return request.make_json_response(
                    {"success": False}
                )

            _logger.info(
                "CALLING update_stream_status()"
            )

            sale_order.update_stream_status(
                event_code,
                event_desc,
            )

            _logger.info(
                "update_stream_status() COMPLETED"
            )

            return request.make_json_response(
                {"success": True}
            )

        except Exception as e:

            _logger.exception(
                "STREAM WEBHOOK ERROR"
            )

            return request.make_json_response(
                {
                    "success": False,
                    "error": str(e),
                }
            )