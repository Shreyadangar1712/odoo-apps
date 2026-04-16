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

from odoo import models, fields, api



class invoiceAddons(models.Model):
    _inherit = ['account.move']

    new_invoice = fields.Binary(string='New Invoice')
    new_invoice_number=fields.Char(string="New Invoice No:", default="CINV0001", placeholder="CNV00001")
    tracking_id=fields.Char(string="Tracking ID ")
    tracking_url=fields.Char(string="url",compute='get_tracking_detail')

    def get_tracking_detail(self):
        for rec in self:
            rec.tracking_url="https://sequel247.com/track/"+str(rec.tracking_id)
        