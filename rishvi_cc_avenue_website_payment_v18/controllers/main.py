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
from pay_ccavenue import CCAvenue
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class CustomPaymentCCAvenue(http.Controller):
    _return_url = '/payment/ccavenue/return'
    _cancel_url = '/payment/ccavenue/cancel'

    @http.route(['/payment/ccavenue/return', '/payment/ccavenue/cancel'],
                type='http', auth='public',
                methods=['POST'], csrf=False, save_session=False)
    def avenue_return(self, **post):
        if post:
            payment_provider = request.env['payment.provider'].sudo().search(
                [('code', '=', 'avenue')])
            web_url = request.env[
                'ir.config_parameter'].sudo().get_param('web.base.url')
            # Create an instance of CCAvenue
            ccavenue = CCAvenue(payment_provider.working_key,
                                payment_provider.access_code,
                                payment_provider.merchant_key,
                                web_url + '/payment/ccavenue/return',
                                web_url + '/payment/ccavenue/cancel')
            # Decrypt the data using the instance
            decrypted_data = ccavenue.decrypt(post)
            tx_sudo = request.env[
                'payment.transaction'].sudo()._get_tx_from_notification_data(
                'avenue', decrypted_data)
            tx_sudo._handle_notification_data('avenue', decrypted_data)
        return request.redirect('/payment/status')
