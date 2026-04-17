# -*- coding: utf-8 -*-
#############################################################################
#
#    Rishvi Pvt Ltd
#
#    Copyright (C) 2025-TODAY Rishvi Pvt Ltd (<https://www.rishvi.com>)
#    Author: Rishvi Development Team (<https://www.rishvi.com>)
#
#    This software is proprietary and confidential.
#
#    Unauthorized copying, modification, distribution, or use of this
#    software, via any medium, is strictly prohibited without the prior
#    written permission of Rishvi Pvt Ltd.
#
#    This software is licensed, not sold. A valid commercial license
#    from Rishvi Pvt Ltd is required to use this software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
#    OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
#    NON-INFRINGEMENT.
#
#    For licensing information, contact: support@rishvi.com
#
##########################################################################
import json
import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class TawkDiscussController(http.Controller):

    @http.route("/tawk_discuss/webhook", type="http", auth="public", methods=["POST"], csrf=False)
    def tawk_webhook(self, **kwargs):
        raw_body = request.httprequest.get_data() or b"{}"

        try:
            payload = json.loads(raw_body.decode("utf-8") or "{}")
        except Exception:
            payload = {}

        mixin = request.env["tawk.discuss.thread"].sudo()
        logger_model = request.env["tawk.discuss.webhook.log"].sudo()

        _logger.info("Tawk webhook headers: %s", dict(request.httprequest.headers))
        _logger.info("Tawk webhook raw body: %s", raw_body.decode("utf-8", errors="ignore"))

        if not mixin._verify_signature(raw_body, request.httprequest.headers):
            logger_model.create({
                "event": payload.get("event") or payload.get("type"),
                "chat_id": payload.get("chatId") or payload.get("id"),
                "status": "error",
                "error_message": "Invalid webhook signature",
                "payload": payload,
            })
            return request.make_response(
                "invalid signature",
                headers=[("Content-Type", "text/plain")],
                status=401,
            )

        try:
            parsed = mixin._normalize_webhook_payload(payload)
            _logger.info("Tawk parsed payload: %s", parsed)

            thread = request.env["tawk.discuss.thread"].sudo()._get_or_create_thread_from_payload(parsed)

            _logger.info(
                "Tawk thread resolved: id=%s chat_id=%s channel_id=%s parent_channel_id=%s",
                thread.id,
                thread.tawk_chat_id,
                thread.channel_id.id if thread.channel_id else False,
                thread.parent_channel_id.id if thread.parent_channel_id else False,
            )

            if parsed.get("message_body"):
                _logger.info("Tawk message body present, creating message for chat_id=%s", parsed.get("chat_id"))
                request.env["tawk.discuss.message"].sudo().create_from_webhook_payload(payload)
            else:
                _logger.info("Tawk webhook had no message_body, only thread update for chat_id=%s",
                             parsed.get("chat_id"))

            logger_model.create({
                "event": parsed.get("event"),
                "chat_id": parsed.get("chat_id"),
                "thread_id": thread.id,
                "status": "done",
                "payload": payload,
            })
            return request.make_response("ok", headers=[("Content-Type", "text/plain")], status=200)

        except Exception as error:
            _logger.exception("Tawk webhook processing failed: %s", error)
            logger_model.create({
                "event": payload.get("event") or payload.get("type"),
                "chat_id": payload.get("chatId") or payload.get("id"),
                "status": "error",
                "error_message": str(error),
                "payload": payload,
            })
            return request.make_response("error", headers=[("Content-Type", "text/plain")], status=500)

    @http.route("/tawk_discuss/sidebar_threads", type="json", auth="user")
    def tawk_sidebar_threads(self):
        return request.env["tawk.discuss.thread"].sudo().get_sidebar_threads()