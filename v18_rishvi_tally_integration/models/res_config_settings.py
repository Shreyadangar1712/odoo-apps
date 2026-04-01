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

from odoo import models, api, fields, _

class Configuration(models.Model):
    _name = 'res.configuration'
    _description = "Configurations"

    name = fields.Char(string="Configuration Name", required=True)
    ledger_by = fields.Selection(selection=[('category','Goup By Category'),('product','Group By Product')], string="Tally Ledger Group By", help="If the tally ledger is not set in journal then this has been used by default tax ledger.", default="category")
    bill_allocation  = fields.Boolean(string="Want to Use Bill Alloaction in XML")
    active = fields.Boolean(default=True, help="Set active to false to hide the configuration without removing it.")
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True, default=lambda self: self.env.company)
    field_mapping_id = fields.Many2one('field.mapping', string="Tags Mapping")

    acc_journal_ledger = fields.Char(string="Default Tally Journal Ledger", help="If the tally legder is not set in journal then this has been used by default journal ledger.")
    acc_category_ledger = fields.Char(string="Default Tally Product Ledger", help="If the tally legder is not set in Product or Category then this has been used by default ledger.")
    acc_tax_ledger = fields.Char(string="Default Tally Tax Ledger", help="If the tally ledger is not set in journal then this has been used by default tax ledger.")

    gst_ovr_dn_nature_local = fields.Char(string="Local", help="Local GSTOVRDNNATURE.", default="Sales Taxable",
                                          required="1")
    gst_ovr_dn_nature_interstate = fields.Char(string="Interstate", help="Interstate GSTOVRDNNATURE.",
                                               default="Interstate Sales Taxable", required="1")
    gst_ovr_dn_nature_overseas = fields.Char(string="Overseas", help="Overseas GSTOVRDNNATURE.",
                                             default="Exports LUT/Bond", required="1")




