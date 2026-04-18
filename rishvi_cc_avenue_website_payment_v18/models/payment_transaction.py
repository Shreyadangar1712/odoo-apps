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
##########################################################################import logging

from pay_ccavenue import CCAvenue

from odoo import _, api, models
from odoo.exceptions import ValidationError
from odoo.addons.payment import utils as payment_utils

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    @api.model
    def _compute_reference(self, provider_code, prefix=None, separator='-', **kwargs):
        if provider_code == 'avenue' and not prefix:
            prefix = payment_utils.singularize_reference_prefix()
        return super()._compute_reference(
            provider_code, prefix=prefix, separator=separator, **kwargs
        )

    def _get_specific_rendering_values(self, processing_values):
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'avenue':
            return res

        self.ensure_one()
        return {
            **res,
            **self._ccavenue_get_redirect_rendering_values(),
        }

    def _ccavenue_get_redirect_rendering_values(self):
        """Prepare the rendering values for the CCAvenue redirect form."""
        self.ensure_one()

        web_base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        sale_order = self.sale_order_ids[:1]

        billing_name = self.partner_name or ''
        billing_tel = self.partner_phone or ''
        billing_address = self.partner_address or ''
        billing_city = self.partner_city or ''
        billing_state = self.partner_state_id.name if self.partner_state_id else ''
        billing_country = self.partner_country_id.name if self.partner_country_id else ''
        billing_zip = self.partner_zip or ''
        billing_email = self.partner_email or ''

        form_data = {
            'order_id': self.reference,
            'currency': self.currency_id.name,
            'amount': self.amount,  # full tx amount
            'redirect_url': f'{web_base_url}/payment/ccavenue/return',
            'cancel_url': f'{web_base_url}/payment/ccavenue/cancel',
            'billing_name': billing_name,
            'billing_tel': billing_tel,
            'billing_address': billing_address,
            'billing_city': billing_city,
            'billing_state': billing_state,
            'billing_country': billing_country,
            'billing_zip': billing_zip,
            'billing_email': billing_email,
        }

        # Optional sale order/customer metadata if needed later
        if sale_order:
            form_data.update({
                'merchant_param1': sale_order.name or '',
            })

        if self.provider_id.state == 'test':
            api_url = (
                'https://test.ccavenue.com/transaction/transaction.do'
                '?command=initiateTransaction'
            )
        else:
            api_url = (
                'https://secure.ccavenue.com/transaction/transaction.do'
                '?command=initiateTransaction'
            )

        ccavenue = CCAvenue(
            self.provider_id.working_key,
            self.provider_id.access_code,
            self.provider_id.merchant_key,
            f'{web_base_url}/payment/ccavenue/return',
            f'{web_base_url}/payment/ccavenue/cancel',
        )
        encrypted_data = ccavenue.encrypt(form_data)

        return {
            'encrypted_data': encrypted_data,
            'access_code': self.provider_id.access_code,
            'api_url': api_url,
        }

    @api.model
    def _get_tx_from_notification_data(self, provider_code, notification_data):
        tx = super()._get_tx_from_notification_data(provider_code, notification_data)
        if provider_code != 'avenue':
            return tx

        reference = notification_data.get('order_id')
        if not reference:
            raise ValidationError(_("CCAvenue: No reference found in notification data."))

        tx = self.search([
            ('reference', '=', reference),
            ('provider_code', '=', 'avenue'),
        ], limit=1)

        if not tx:
            raise ValidationError(_("CCAvenue: No transaction found matching reference %s.", reference))

        return tx

    def _handle_notification_data(self, provider_code, notification_data):
        tx = super()._handle_notification_data(provider_code, notification_data)
        if provider_code != 'avenue':
            return tx
        return tx

    def _process_notification_data(self, notification_data):
        super()._process_notification_data(notification_data)

        if self.provider_code != 'avenue':
            return

        status = (notification_data.get('order_status') or '').strip().lower()
        provider_reference = notification_data.get('tracking_id') or notification_data.get('bank_ref_no')
        if provider_reference:
            self.provider_reference = provider_reference

        if status in ('success', 'successful', 'shipped'):
            self._set_done()
        elif status in ('aborted', 'cancelled', 'canceled'):
            self._set_canceled(state_message=_("Payment was cancelled by the user or provider."))
        elif status in ('failure', 'failed'):
            self._set_error(_("Payment failed at CCAvenue."))
        elif status in ('pending', 'initiated'):
            self._set_pending(_("Payment is pending confirmation from CCAvenue."))
        else:
            _logger.warning(
                "CCAvenue: received unrecognized payment state '%s' for transaction %s",
                status, self.reference
            )
            self._set_error(_("Invalid payment status received from CCAvenue: %s", status))