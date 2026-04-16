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
import hashlib
import hmac
import json
import logging
from datetime import timedelta
import base64
import requests
from markupsafe import Markup
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import html_escape
from datetime import datetime
from urllib.parse import quote
_logger = logging.getLogger(__name__)


class TawkDiscussMixin(models.AbstractModel):
    _name = "tawk.discuss.mixin"
    _description = "Tawk Discuss Common Helpers"

    def _tawk_get_param(self, key, default=False):
        return self.env["ir.config_parameter"].sudo().get_param(key, default)

    def _tawk_set_param(self, key, value):
        self.env["ir.config_parameter"].sudo().set_param(key, value or "")

    def _tawk_enabled(self):
        return self._tawk_get_param("tawk_discuss_integration.enabled") == "True"

    def _tawk_headers(self):
        api_key = self._tawk_get_param("tawk_discuss_integration.api_key")
        bearer = self._tawk_get_param("tawk_discuss_integration.access_token")
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        auth = None
        if api_key:
            auth = (api_key, "")
        elif bearer:
            headers["Authorization"] = f"Bearer {bearer}"
        else:
            raise UserError(_("Please configure Tawk API Key or Access Token in settings."))
        return headers, auth

    def _tawk_post(self, method, payload=None, timeout=30):
        headers, auth = self._tawk_headers()
        url = f"https://api.tawk.to/v1/{method}"

        _logger.info("Tawk API POST url=%s payload=%s", url, payload)

        try:
            response = requests.post(
                url,
                headers=headers,
                auth=auth,
                data=json.dumps(payload or {}),
                timeout=timeout,
            )
            _logger.info("Tawk API response status=%s body=%s", response.status_code, response.text)
            response.raise_for_status()
        except requests.RequestException as error:
            raise UserError(_("Tawk API request failed: %s") % error) from error

        data = response.json()
        if isinstance(data, dict) and not data.get("ok", True):
            raise UserError(_("Tawk API error: %s") % (data.get("message") or data.get("error") or _("Unknown error")))
        return data.get("data") if isinstance(data, dict) and "data" in data else data

    def _tawk_group(self):
        xmlid = self._tawk_get_param("tawk_discuss_integration.group_id")
        if not xmlid:
            group_id = self._tawk_get_param("tawk_discuss_integration.group_res_id")
            if group_id:
                return self.env["res.groups"].browse(int(group_id)).exists()
            return self.env["res.groups"]
        return self.env.ref(xmlid, raise_if_not_found=False) or self.env["res.groups"].browse(int(self._tawk_get_param("tawk_discuss_integration.group_res_id", 0) or 0)).exists()

    def _tawk_parent_channel(self):
        channel_id = int(self._tawk_get_param("tawk_discuss_integration.parent_channel_id", 0) or 0)
        return self.env["discuss.channel"].browse(channel_id).exists()

    def _ensure_tawk_parent_channel(self):
        channel = self._tawk_parent_channel()
        group = self._tawk_group()
        if channel:
            vals = {}
            if group and channel.group_ids != group:
                vals["group_ids"] = [(6, 0, group.ids)]
            if vals:
                channel.write(vals)
            return channel
        vals = {
            "name": self._tawk_get_param("tawk_discuss_integration.parent_channel_name", "Tawk") or "Tawk",
            "channel_type": "channel",
        }
        if group:
            vals["group_ids"] = [(6, 0, group.ids)]
        channel = self.env["discuss.channel"].sudo().create(vals)
        self._tawk_set_param("tawk_discuss_integration.parent_channel_id", channel.id)
        return channel

    def _sync_channel_members(self, channel):
        group = self._tawk_group()
        if not group:
            return
        partners = group.users.filtered(lambda u: u.active and not u.share).mapped("partner_id")
        if partners:
            channel.sudo().add_members(partner_ids=partners.ids, open_chat_window=False, post_joined_message=False)

    def _channel_name_from_visitor(self, visitor_name=None, visitor_email=None, chat_id=None):
        if visitor_name:
            return visitor_name.strip()[:120]
        if visitor_email:
            return visitor_email.strip()[:120]
        return _("Visitor %s") % (chat_id or "-")

    def _find_chat_payload_value(self, payload, *keys, default=False):
        current = payload or {}
        for key in keys:
            if not isinstance(current, dict):
                return default
            current = current.get(key, default)
            if current is default:
                return default
        return current

    def _tawk_to_odoo_datetime(self, value):
        if not value:
            return False
        if isinstance(value, fields.Datetime):
            return value
        if not isinstance(value, str):
            return value

        # Example input: 2026-04-08T13:55:53.464Z
        value = value.strip()

        try:
            if value.endswith("Z"):
                # handle ISO format with Zulu timezone
                dt = fields.Datetime.from_string(
                    value.replace("T", " ").replace("Z", "")
                )
                return dt
        except Exception:
            pass

        try:
            # Python ISO parser fallback
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return dt.replace(tzinfo=None)
        except Exception:
            pass

        try:
            # final fallback for standard Odoo format
            return fields.Datetime.to_datetime(value)
        except Exception:
            return False

    def _normalize_webhook_payload(self, payload):
        event = payload.get("event") or payload.get("type") or payload.get("name") or payload.get("trigger")
        data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
        chat = data.get("chat") if isinstance(data.get("chat"), dict) else data
        visitor = chat.get("visitor") if isinstance(chat.get("visitor"), dict) else data.get("visitor", {})
        message = data.get("message") if isinstance(data.get("message"), dict) else {}

        sender = message.get("sender") if isinstance(message.get("sender"), dict) else {}

        sender_type = sender.get("t") or sender.get("type") or data.get("senderType") or "u"
        if sender_type == "visitor":
            sender_type = "v"
        elif sender_type == "agent":
            sender_type = "a"
        elif sender_type == "system":
            sender_type = "s"

        sender_name = (
                sender.get("n")
                or sender.get("name")
                or data.get("senderName")
                or visitor.get("name")
                or payload.get("visitor_name")
                or "Visitor"
        )

        message_body = (
                message.get("text")
                or message.get("msg")
                or data.get("text")
                or data.get("msg")
                or ""
        )

        return {
            "event": event,
            "chat_id": chat.get("id") or data.get("chatId") or data.get("id"),
            "visitor_id": visitor.get("id") or data.get("visitorId"),
            "visitor_name": visitor.get("name") or data.get("name") or payload.get("visitor_name"),
            "visitor_email": visitor.get("email") or data.get("email") or payload.get("visitor_email"),
            "status": chat.get("status") or data.get("status"),
            "created_on": chat.get("createdOn") or data.get("createdOn") or payload.get("createdOn") or data.get(
                "time"),
            "updated_on": chat.get("updatedOn") or data.get("updatedOn") or payload.get("updatedOn") or data.get(
                "time"),
            "message_id": message.get("id") or data.get("messageId"),
            "message_type": message.get("type") or data.get("messageType") or "msg",
            "message_sender_type": sender_type,
            "message_sender_name": sender_name,
            "message_body": message_body,
            "raw": payload,
        }

    def _verify_signature(self, raw_body, headers):
        secret = self._tawk_get_param("tawk_discuss_integration.webhook_secret")
        if not secret:
            _logger.warning("Tawk webhook secret not configured. Signature check skipped.")
            return True

        signature = (
                headers.get("X-Tawk-Signature")
                or headers.get("x-tawk-signature")
        )

        if not signature:
            _logger.warning("Missing Tawk webhook signature header.")
            return False

        expected = hmac.new(
            secret.encode("utf-8"),
            raw_body,
            hashlib.sha1,
        ).hexdigest()

        matched = hmac.compare_digest(signature.strip(), expected)
        if not matched:
            _logger.warning("Invalid Tawk signature. incoming=%s expected=%s", signature, expected)
        return matched

    def _message_body_from_tawk_message(self, thread, message):
        msg_type = message.get("message_type") or "msg"

        if msg_type == "nav" and message.get("payload"):
            data = message["payload"].get("data", {})
            return html_escape(data.get("url") or message.get("body") or _("Visitor navigated"))
        return html_escape(message.get("body") or _("(no text)")).replace("\n", "<br/>")

class TawkDiscussThread(models.Model):
    _name = "tawk.discuss.thread"
    _description = "Tawk Discuss Thread"
    _inherit = ["mail.thread", "mail.activity.mixin", "tawk.discuss.mixin"]
    _order = "last_message_time desc, id desc"
    _rec_name = "display_name"

    name = fields.Char(required=True, tracking=True)
    active = fields.Boolean(default=True)
    tawk_chat_id = fields.Char(required=True, index=True, tracking=True)
    tawk_visitor_id = fields.Char(index=True)
    visitor_name = fields.Char(tracking=True)
    visitor_email = fields.Char(tracking=True)
    status = fields.Selection([("open", "Open"), ("closed", "Closed"), ("unknown", "Unknown")], default="unknown", tracking=True)
    created_on = fields.Datetime(tracking=True)
    updated_on = fields.Datetime(tracking=True)
    last_message_time = fields.Datetime(tracking=True)
    parent_channel_id = fields.Many2one("discuss.channel", required=True, ondelete="cascade")
    channel_id = fields.Many2one("discuss.channel", required=True, ondelete="cascade")
    message_ids = fields.One2many("tawk.discuss.message", "thread_id")
    message_count = fields.Integer(compute="_compute_message_count", store=False)
    last_mail_message_id = fields.Many2one("mail.message", readonly=True)
    webhook_log_ids = fields.One2many("tawk.discuss.webhook.log", "thread_id")
    display_name = fields.Char(compute="_compute_display_name", store=False)
    visitor_partner_id = fields.Many2one("res.partner", string="Visitor Partner", ondelete="set null")

    _sql_constraints = [
        ("tawk_chat_id_unique", "unique(tawk_chat_id)", "Tawk chat id must be unique."),
    ]

    def _get_tawk_chat_url(self):
        self.ensure_one()
        property_id = (self._tawk_get_param("tawk_discuss_integration.property_id") or "").strip()
        chat_id = (self.tawk_chat_id or "").strip()

        if not property_id or not chat_id:
            return False

        return "https://dashboard.tawk.to/#/inbox/%s/all/chats/chat/%s" % (
            quote(property_id, safe=""),
            quote(chat_id, safe=""),
        )

    def _get_tawk_chat_link_html(self):
        self.ensure_one()
        url = self._get_tawk_chat_url()
        if not url:
            return ""

        safe_url = html_escape(url)
        return """
            <div class="mt-2">
                <a href="%s" target="_blank" rel="noopener noreferrer">
                    Open Tawk Chat
                </a>
            </div>
        """ % safe_url

    def _get_or_create_visitor_partner(self):
        self.ensure_one()

        if self.visitor_partner_id:
            return self.visitor_partner_id

        partner = self.env["res.partner"]

        if self.visitor_email:
            partner = self.env["res.partner"].sudo().search(
                [("email", "=", self.visitor_email)],
                limit=1,
            )

        if not partner and self.visitor_name:
            partner = self.env["res.partner"].sudo().create({
                "name": self.visitor_name,
                "email": self.visitor_email or False,
            })

        if partner:
            self.visitor_partner_id = partner.id

        return partner

    @api.depends("name", "tawk_chat_id")
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = "%s [%s]" % (rec.name, rec.tawk_chat_id)

    def _compute_message_count(self):
        counts = self.env["tawk.discuss.message"]._read_group([("thread_id", "in", self.ids)], ["thread_id"], ["__count"])
        mapped = {thread.id: count for thread, count in counts}
        for rec in self:
            rec.message_count = mapped.get(rec.id, 0)

    @api.model
    def _thread_vals_from_payload(self, payload):
        created_on = self._tawk_to_odoo_datetime(payload.get("created_on"))
        updated_on = self._tawk_to_odoo_datetime(payload.get("updated_on"))
        last_message_time = updated_on or created_on or fields.Datetime.now()

        return {
            "name": self._channel_name_from_visitor(
                payload.get("visitor_name"),
                payload.get("visitor_email"),
                payload.get("chat_id"),
            ),
            "tawk_chat_id": payload.get("chat_id"),
            "tawk_visitor_id": payload.get("visitor_id"),
            "visitor_name": payload.get("visitor_name"),
            "visitor_email": payload.get("visitor_email"),
            "status": payload.get("status") if payload.get("status") in ("open", "closed") else "unknown",
            "created_on": created_on,
            "updated_on": updated_on,
            "last_message_time": last_message_time,
        }

    @api.model
    def _get_or_create_thread_from_payload(self, payload):
        if not payload.get("chat_id"):
            raise ValidationError(_("Missing chat id in Tawk payload."))

        _logger.info("Tawk payload received for thread resolution: %s", payload)

        thread = self.search([("tawk_chat_id", "=", payload["chat_id"])], limit=1)
        vals = self._thread_vals_from_payload(payload)

        if thread:
            vals.pop("tawk_chat_id", None)
            thread.write(vals)
            _logger.info(
                "Existing Tawk thread updated: thread_id=%s channel_id=%s",
                thread.id,
                thread.channel_id.id if thread.channel_id else False,
            )
            return thread

        parent = self._ensure_tawk_parent_channel()
        child_channel = self._create_tawk_sub_channel(parent, payload)

        vals.update({
            "parent_channel_id": parent.id,
            "channel_id": child_channel.id,
        })

        thread = super(TawkDiscussThread, self).create([vals])[0]

        _logger.info(
            "New Tawk thread created: thread_id=%s chat_id=%s child_channel_id=%s parent_id=%s",
            thread.id,
            thread.tawk_chat_id,
            child_channel.id,
            parent.id,
        )
        return thread

    def _post_message_to_discuss(self, tawk_message):
        self.ensure_one()

        message_html = self._message_body_from_tawk_message(self, {
            "sender_type": tawk_message.sender_type,
            "sender_name": tawk_message.sender_name,
            "message_type": tawk_message.message_type,
            "body": tawk_message.body,
            "message_time": tawk_message.message_time,
            "payload": tawk_message.payload or {},
        })

        tawk_link_html = self._get_tawk_chat_link_html()
        final_body = "%s%s" % (message_html, tawk_link_html)

        visitor_partner = self._get_or_create_visitor_partner()

        msg_vals = {
            "body": Markup(final_body),
            "message_type": "comment",
            "subtype_xmlid": "mail.mt_comment",
        }

        # incoming visitor message => left side
        if tawk_message.sender_type == "v" and visitor_partner:
            msg_vals["author_id"] = visitor_partner.id

        msg = self.channel_id.sudo().message_post(**msg_vals)
        tawk_message.mail_message_id = msg.id
        self.last_mail_message_id = msg.id
        return msg

    def action_open_discuss_channel(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.name,
            "res_model": "discuss.channel",
            "res_id": self.channel_id.id,
            "view_mode": "form",
            "target": "current",
        }

    @api.model
    def action_test_connection(self):
        property_id = self._tawk_get_param("tawk_discuss_integration.property_id")
        if not property_id:
            raise UserError(_("Please configure Property ID first."))
        self._tawk_post("property.info", {"propertyId": property_id})
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Success"),
                "message": _("Tawk connection successful."),
                "type": "success",
                "sticky": False,
            },
        }

    @api.model
    def action_prepare_parent_channel(self):
        parent = self._ensure_tawk_parent_channel()
        self._sync_channel_members(parent)

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Done"),
                "message": _("Parent channel '%s' is ready. Tawk visitor chats will appear under it as child threads.") % parent.name,
                "type": "success",
            },
        }

    @api.model
    def _cron_tawk_history_sync(self):
        if not self._tawk_enabled():
            return

        icp = self.env["ir.config_parameter"].sudo()
        property_id = icp.get_param("tawk_discuss_integration.property_id")
        history_method = (icp.get_param("tawk_discuss_integration.history_method") or "").strip()
        history_since = icp.get_param("tawk_discuss_integration.history_since")

        if not property_id:
            _logger.info("Tawk history sync skipped: property_id not configured.")
            return

        if not history_method:
            _logger.info("Tawk history sync skipped: history_method not configured.")
            return

        payload = {"propertyId": property_id}
        if history_since:
            payload["startTime"] = history_since

        try:
            data = self._tawk_post(history_method, payload)
        except Exception as error:
            _logger.warning(
                "Tawk history sync skipped. Unsupported or unavailable endpoint. method=%s error=%s",
                history_method,
                error,
            )
            return

        chats = data if isinstance(data, list) else data.get("chats") or data.get("data") or []
        for chat in chats:
            self._import_chat_payload(chat)

        icp.set_param("tawk_discuss_integration.history_since", fields.Datetime.now())

    @api.model
    def _import_chat_payload(self, chat_payload):
        payload = {
            "chat_id": chat_payload.get("id") or chat_payload.get("chatId"),
            "visitor_id": (chat_payload.get("visitor") or {}).get("id"),
            "visitor_name": (chat_payload.get("visitor") or {}).get("name"),
            "visitor_email": (chat_payload.get("visitor") or {}).get("email"),
            "status": chat_payload.get("status"),
            "created_on": chat_payload.get("createdOn"),
            "updated_on": chat_payload.get("updatedOn"),
        }
        thread = self._get_or_create_thread_from_payload(payload)
        messages = chat_payload.get("messages") or []
        for line in messages:
            self.env["tawk.discuss.message"]._create_from_chat_message(thread, line)
        return thread

    @api.model
    def _create_tawk_sub_channel(self, parent, payload):
        name = self._channel_name_from_visitor(
            payload.get("visitor_name"),
            payload.get("visitor_email"),
            payload.get("chat_id"),
        )

        self._sync_channel_members(parent)

        if hasattr(parent, "_create_sub_channel"):
            channel = parent.sudo()._create_sub_channel(name=name)
        else:
            channel = self.env["discuss.channel"].sudo().create({
                "name": name,
                "channel_type": "channel",
                "parent_channel_id": parent.id,
            })

        self._sync_channel_members(channel)
        return channel

    # @api.model
    # def get_sidebar_threads(self):
    #     records = self.search([], order="last_message_time desc, id desc", limit=200)
    #     current_partner = self.env.user.partner_id
    #     result = []
    #
    #     for rec in records:
    #         channel = rec.channel_id
    #         if not channel:
    #             continue
    #
    #         self_member = channel.channel_member_ids.filtered(
    #             lambda m: m.partner_id == current_partner
    #         )[:1]
    #
    #         result.append({
    #             "id": rec.id,
    #             "name": rec.name,
    #             "channel_id": channel.id,
    #             "visitor_name": rec.visitor_name,
    #             "visitor_email": rec.visitor_email,
    #             "unread_count": self_member.message_unread_counter if self_member else 0,
    #         })
    #
    #     return result

    @api.model
    def _debug_log_thread_channel_map(self, label="Tawk Debug"):
        threads = self.search([], order="id asc")
        _logger.info("========== %s ==========", label)
        print("========== %s ==========" % label)
        for rec in threads:
            channel = rec.channel_id
            parent = channel.parent_channel_id if channel else False
            msg = (
                "THREAD id=%s name=%s | channel_id=%s channel_name=%s | parent_id=%s parent_name=%s"
                % (
                    rec.id,
                    rec.name,
                    channel.id if channel else False,
                    channel.name if channel else False,
                    parent.id if parent else False,
                    parent.name if parent else False,
                )
            )
            _logger.info(msg)
            print(msg)
        _logger.info("===================================")
        print("===================================")

    @api.model
    def _ensure_child_channel_for_thread(self, thread):
        parent = thread.parent_channel_id or self._ensure_tawk_parent_channel()
        channel = thread.channel_id

        if channel and channel.parent_channel_id and channel.parent_channel_id.id == parent.id:
            return channel

        payload = {
            "visitor_name": thread.visitor_name,
            "visitor_email": thread.visitor_email,
            "chat_id": thread.tawk_chat_id,
        }
        child_channel = self._create_tawk_sub_channel(parent, payload)

        old_channel = thread.channel_id
        thread.write({
            "parent_channel_id": parent.id,
            "channel_id": child_channel.id,
        })

        _logger.info(
            "Tawk thread repaired: thread=%s old_channel=%s new_child_channel=%s",
            thread.id,
            old_channel.id if old_channel else False,
            child_channel.id,
        )
        return child_channel

    @api.model
    def action_repair_thread_channels(self):
        """Run from UI/buttons. No shell needed."""
        parent = self._ensure_tawk_parent_channel()
        self._sync_channel_members(parent)

        threads = self.search([])
        repaired = 0

        self._debug_log_thread_channel_map(label="BEFORE REPAIR")

        for thread in threads:
            before_channel = thread.channel_id
            channel = self._ensure_child_channel_for_thread(thread)
            if not before_channel or before_channel.id != channel.id:
                repaired += 1

        self._debug_log_thread_channel_map(label="AFTER REPAIR")

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Done"),
                "message": _("Tawk thread repair completed. Repaired threads: %s") % repaired,
                "type": "success",
                "sticky": False,
            },
        }

    @api.model
    def get_sidebar_threads(self):
        records = self.search([], order="last_message_time desc, id desc", limit=200)
        current_partner = self.env.user.partner_id
        result = []

        _logger.info("========== GET SIDEBAR THREADS DEBUG ==========")

        for rec in records:
            channel = self._ensure_child_channel_for_thread(rec)
            parent = channel.parent_channel_id if channel else False

            self_member = channel.channel_member_ids.filtered(
                lambda m: m.partner_id == current_partner
            )[:1]

            row = {
                "id": rec.id,
                "name": rec.name,
                "channel_id": channel.id if channel else False,
                "visitor_name": rec.visitor_name,
                "visitor_email": rec.visitor_email,
                "unread_count": self_member.message_unread_counter if self_member else 0,
            }
            result.append(row)

            _logger.info(
                "SIDEBAR ROW -> thread_id=%s name=%s channel_id=%s channel_name=%s parent_id=%s parent_name=%s",
                rec.id,
                rec.name,
                channel.id if channel else False,
                channel.name if channel else False,
                parent.id if parent else False,
                parent.name if parent else False,
            )

        _logger.info("FINAL SIDEBAR RESULT: %s", result)
        _logger.info("===============================================")
        return result

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            _logger.info(
                "Tawk thread ORM create complete: thread_id=%s chat_id=%s channel_id=%s",
                rec.id,
                rec.tawk_chat_id,
                rec.channel_id.id if rec.channel_id else False,
            )
        return records

    def action_create_missing_initial_message(self):
        for rec in self:
            if rec.message_ids:
                continue
            text = rec.tawk_chat_id
            if not text:
                continue
            self.env["tawk.discuss.message"].create({
                "thread_id": rec.id,
                "tawk_message_id": "manual_fix_%s" % rec.id,
                "sender_type": "v",
                "sender_name": rec.visitor_name or "Visitor",
                "message_type": "msg",
                "body": text,
                "payload": {"source": "manual_fix"},
                "message_time": fields.Datetime.now(),
                "imported_from": "history",
            })
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Done"),
                "message": _("Missing initial messages created."),
                "type": "success",
                "sticky": False,
            },
        }


class TawkDiscussMessage(models.Model):
    _name = "tawk.discuss.message"
    _description = "Tawk Discuss Message"
    _order = "message_time asc, id asc"
    _inherit = ["tawk.discuss.mixin"]

    thread_id = fields.Many2one("tawk.discuss.thread", required=True, ondelete="cascade", index=True)
    tawk_message_id = fields.Char(index=True)
    sender_type = fields.Selection([("a", "Agent"), ("v", "Visitor"), ("s", "System"), ("u", "Unknown")], default="u")
    sender_name = fields.Char()
    message_type = fields.Char(default="msg")
    body = fields.Text()
    payload = fields.Json()
    message_time = fields.Datetime(index=True)
    mail_message_id = fields.Many2one("mail.message", readonly=True, ondelete="set null")
    imported_from = fields.Selection([("webhook", "Webhook"), ("history", "History")], default="webhook")

    _sql_constraints = [
        ("tawk_message_unique", "unique(thread_id, tawk_message_id)", "Tawk message id must be unique per thread."),
    ]

    @api.model
    def _create_from_chat_message(self, thread, line, imported_from="history"):
        sender = line.get("sender") or {}
        external_id = line.get("id") or "%s_%s_%s" % (
            thread.tawk_chat_id,
            line.get("time") or fields.Datetime.now(),
            hashlib.sha1((json.dumps(line, sort_keys=True, default=str)).encode()).hexdigest()[:12],
        )
        existing = self.search([("thread_id", "=", thread.id), ("tawk_message_id", "=", external_id)], limit=1)
        if existing:
            return existing
        msg = self.create({
            "thread_id": thread.id,
            "tawk_message_id": external_id,
            "sender_type": sender.get("t") or "u",
            "sender_name": sender.get("n") or sender.get("name") or thread.visitor_name,
            "message_type": line.get("type") or "msg",
            "body": line.get("msg") or "",
            "payload": line,
            "message_time": self._tawk_to_odoo_datetime(line.get("time")) or fields.Datetime.now(),
            "imported_from": imported_from,
        })
        thread.last_message_time = msg.message_time or fields.Datetime.now()
        return msg

    @api.model
    def create_from_webhook_payload(self, payload):
        thread_payload = self._normalize_webhook_payload(payload)
        thread = self.env["tawk.discuss.thread"]._get_or_create_thread_from_payload(thread_payload)

        msg_external_id = thread_payload.get("message_id") or "%s_%s" % (
            thread.tawk_chat_id,
            hashlib.sha1(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()[:16],
        )

        existing = self.search([
            ("thread_id", "=", thread.id),
            ("tawk_message_id", "=", msg_external_id)
        ], limit=1)
        if existing:
            return existing

        message_time = self._tawk_to_odoo_datetime(
            thread_payload.get("updated_on")
            or thread_payload.get("created_on")
        ) or fields.Datetime.now()

        payload_time = fields.Datetime.to_string(message_time)
        line = {
            "id": msg_external_id,
            "type": thread_payload.get("message_type") or "msg",
            "msg": thread_payload.get("message_body") or "",
            "time": payload_time,
            "sender": {
                "t": thread_payload.get("message_sender_type") or "u",
                "n": thread_payload.get("message_sender_name") or thread_payload.get("visitor_name") or "Visitor",
            },
            "data": payload.get("data") if isinstance(payload.get("data"), dict) else payload,
        }

        msg = self._create_from_chat_message(thread, line, imported_from="webhook")

        if not msg.message_time:
            msg.message_time = message_time if not isinstance(message_time, str) else fields.Datetime.now()

        return msg

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            if rec.thread_id and rec.thread_id.channel_id:
                # avoid duplicate post if already linked
                if not rec.mail_message_id:
                    rec.thread_id._post_message_to_discuss(rec)
        return records


class TawkDiscussWebhookLog(models.Model):
    _name = "tawk.discuss.webhook.log"
    _description = "Tawk Webhook Log"
    _order = "received_at desc, id desc"

    received_at = fields.Datetime(default=fields.Datetime.now, required=True)
    event = fields.Char()
    chat_id = fields.Char(index=True)
    thread_id = fields.Many2one("tawk.discuss.thread", ondelete="set null")
    status = fields.Selection([("done", "Done"), ("error", "Error")], default="done")
    error_message = fields.Text()
    payload = fields.Json(required=True)


class TawkDiscussActions(models.TransientModel):
    _name = "tawk.discuss.actions"
    _description = "Tawk Discuss Actions"
    _inherit = ["tawk.discuss.mixin"]

    def action_sync_history_now(self):
        self.env["tawk.discuss.thread"]._cron_tawk_history_sync()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {"title": _("Done"), "message": _("History sync completed."), "type": "success"},
        }
