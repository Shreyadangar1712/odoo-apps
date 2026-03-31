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

from odoo import fields, models, api, _

class ProductTemplate(models.Model):

    _inherit = "product.template"

    @api.model
    def _get_tally_default_ledger(self):
        return self.env['ir.config_parameter'].sudo().get_param('rishvi_tally_integration.ledger_by') or 'category'

    @api.onchange('categ_id')
    def _onchange_categ_id_update_fields(self):
        if self.categ_id and self.categ_id.export_ledger:
            self.export_ledger = self.categ_id.export_ledger
        if self.categ_id and self.categ_id.local_ledger:
            self.export_ledger = self.categ_id.local_ledger

    export_ledger = fields.Char(string="Export Tally Ledger")
    local_ledger = fields.Char(string="Local Tally Ledger")
    ledger_by = fields.Char(selection=[('category','Category'),('product','Product')], string="Tally Ledger By", help="If the tally ledger is not set in journal then this has been used by default tax ledger.", default=_get_tally_default_ledger)

class ProductCategory(models.Model):

    _inherit = "product.category"

    export_ledger = fields.Char(string="Export Tally Ledger")
    local_ledger = fields.Char(string="Local Tally Ledger")

class AccountJournal(models.Model):

    _inherit = "account.journal"

    ledger_local = fields.Char(string="Local Tally Ledger")
    ledger_export = fields.Char(string="Export Tally Ledger")

class AccountTax(models.Model):

    _inherit = "account.tax"

    ledger_name = fields.Char(string="Tally Ledgername")
