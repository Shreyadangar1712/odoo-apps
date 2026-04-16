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
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    tawk_enabled = fields.Boolean(
        string="Enable Tawk Integration",
        config_parameter="tawk_discuss_integration.enabled",
    )
    tawk_api_key = fields.Char(
        string="Tawk API Key",
        config_parameter="tawk_discuss_integration.api_key",
    )
    tawk_access_token = fields.Char(
        string="Access Token",
        config_parameter="tawk_discuss_integration.access_token",
    )
    tawk_property_id = fields.Char(
        string="Property ID",
        config_parameter="tawk_discuss_integration.property_id",
    )
    tawk_webhook_secret = fields.Char(
        string="Webhook Secret",
        config_parameter="tawk_discuss_integration.webhook_secret",
    )
    tawk_history_method = fields.Char(
        string="History API Method",
        config_parameter="tawk_discuss_integration.history_method",
        default="chat.list",
        help="Example: chats.get. Adjust this according to your enabled Tawk endpoint.",
    )
    tawk_history_since = fields.Datetime(
        string="History Sync Since",
        config_parameter="tawk_discuss_integration.history_since",
    )
    tawk_parent_channel_id = fields.Many2one("discuss.channel", string="Parent Tawk Channel")
    tawk_parent_channel_name = fields.Char(
        string="Parent Channel Name",
        config_parameter="tawk_discuss_integration.parent_channel_name",
        default="Tawk",
    )
    tawk_group_id = fields.Many2one("res.groups", string="Allowed Internal Group")

    def get_values(self):
        res = super().get_values()
        icp = self.env["ir.config_parameter"].sudo()

        parent_channel_id = int(icp.get_param("tawk_discuss_integration.parent_channel_id", 0) or 0)
        group_id = int(icp.get_param("tawk_discuss_integration.group_res_id", 0) or 0)

        res.update(
            tawk_parent_channel_id=self.env["discuss.channel"].browse(parent_channel_id).exists().id if parent_channel_id else False,
            tawk_group_id=self.env["res.groups"].browse(group_id).exists().id if group_id else False,
        )
        return res

    def set_values(self):
        super().set_values()
        icp = self.env["ir.config_parameter"].sudo()
        for rec in self:
            icp.set_param("tawk_discuss_integration.parent_channel_id", rec.tawk_parent_channel_id.id or "")
            icp.set_param("tawk_discuss_integration.group_res_id", rec.tawk_group_id.id or "")

    # -------------------------
    # Button wrapper methods
    # -------------------------
    def action_test_connection(self):
        self.ensure_one()
        return self.env["tawk.discuss.thread"].sudo().action_test_connection()

    def action_prepare_parent_channel(self):
        self.ensure_one()
        result = self.env["tawk.discuss.thread"].sudo().action_prepare_parent_channel()

        icp = self.env["ir.config_parameter"].sudo()
        parent_channel_id = int(icp.get_param("tawk_discuss_integration.parent_channel_id", 0) or 0)
        self.tawk_parent_channel_id = self.env["discuss.channel"].browse(parent_channel_id).exists()
        return result