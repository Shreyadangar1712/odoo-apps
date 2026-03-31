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
from odoo import models,fields,api
_logger = logging.getLogger(__name__)

class TagTag(models.Model):
    _name = 'tag.tag'
    _description = "Tally Tags"

    name = fields.Char(string="Tag",required=True)

class FieldMapping(models.Model):
    _name = 'field.mapping'
    _description = "Field Mapping"

    name = fields.Char(string="Name",required=True)
    active = fields.Boolean(string="Active",default=True)
    mapping_line_ids = fields.One2many('mapping.line',inverse_name='mapping_field_id',string="Fields To Mapped")

class MappingLine(models.Model):
    _name = 'mapping.line'
    _description = "Tally Mapping Line"

    mapping_field_id = fields.Many2one('field.mapping', string="Mapping",help="Select the Tally tags that you want to map with Odoo field")
    tally_field_id = fields.Many2one('tag.tag', string="Tally Tag",help="Select the Tally tags that you want to map with Odoo field")
    model_field_id = fields.Many2one('ir.model.fields',domain="[('model', '=', 'account.move')]")
    fixed_text = fields.Char(string="Text",help="Fixed data that you want to send")
    default = fields.Char(string="Default",help="The data enter here will be send when there is no data in the field")
    fixed = fields.Boolean(string="Fixed",default=False,help="Select wether you want to send the fixed data or the field data")
