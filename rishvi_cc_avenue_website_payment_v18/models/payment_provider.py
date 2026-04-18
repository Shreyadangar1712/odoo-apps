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

from odoo import api, fields, models


class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('avenue', 'CCAvenue')],
        ondelete={'avenue': 'set default'},
    )

    merchant_key = fields.Char(
        string='Merchant ID',
        groups='base.group_user',
        required_if_provider='avenue',
        help="CCAvenue Merchant ID.",
    )
    access_code = fields.Char(
        string='Access Code',
        groups='base.group_user',
        required_if_provider='avenue',
        help="CCAvenue Access Code.",
    )
    working_key = fields.Char(
        string='Working Key',
        groups='base.group_user',
        required_if_provider='avenue',
        help="CCAvenue Working Key.",
    )
    def _get_default_payment_method_codes(self):

        self.ensure_one()
        if self.code != 'avenue':
            return super()._get_default_payment_method_codes()
        return {'card'}