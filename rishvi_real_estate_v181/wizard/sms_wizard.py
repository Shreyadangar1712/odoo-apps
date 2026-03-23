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
import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import requests

_logger = logging.getLogger(__name__)


class sms_wizard(models.TransientModel):
    _name = 'sms.wizard'

    def action_apply(self):
        loans = self.env['loan.line.rs.own'].browse(self.env.context.get('active_ids', []))
        sms_conf = self.env['sms']
        sms_conf_ids = sms_conf.search([], limit=1, order='id desc')
        sms_conf_obj = sms_conf.browse(sms_conf_ids)
        sms_text = sms_conf_obj.name

        api_key = 'eab846b9'
        api_secret = '540380c7'

        for loan in loans:
            if not loan.contract_partner_id.mobile:
                raise UserError(_('Please set partner mobile number!'))

            values = {
                "partner": loan.contract_partner_id.name,
                "date": loan.date or None,
                "amount": round(loan.amount, 2) or 0.0,
                "contract": loan.contract or '',
                "building": loan.contract_building.name or None,
                "unit": loan.contract_building_unit.name or None,
            }

            message_text = sms_text.format(**values)

            try:
                # Use Vonage REST API directly
                url = "https://rest.nexmo.com/sms/json"

                payload = {
                    'api_key': api_key,
                    'api_secret': api_secret,
                    'to': '002' + loan.contract_partner_id.mobile,
                    'from': '00201007394256',
                    'text': message_text,
                }

                response = requests.post(url, data=payload)
                data = response.json()

                if data['messages'][0]['status'] == '0':
                    _logger.info(f"SMS sent successfully to {loan.contract_partner_id.mobile}")
                else:
                    error_text = data['messages'][0].get('error-text', 'Unknown error')
                    raise UserError(
                        _("Failed to send SMS. Error: %s") % error_text
                    )

            except Exception as e:
                raise UserError(_("SMS sending failed: %s") % str(e))

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: