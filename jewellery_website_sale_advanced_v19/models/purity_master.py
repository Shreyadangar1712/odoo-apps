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


class PurityUnit(models.Model):
    _name = 'purity.units'
    _description='Purity Master'
    _rec_name='rec_name'

    name=fields.Char(string="Value",placeholder="Set a name like 22",required=True)
    unit=fields.Char(string="Unit",placeholder="Set a Unit like Carat or Percentage(%)")
    rec_name=fields.Char(compute='_compute_rec_name')
    
    @api.model
    def _compute_rec_name(self):
        for rec in self:
            if rec.unit==False:
                rec.rec_name=str(rec.name)
            else:
                rec.rec_name=str(rec.name)+' '+str(rec.unit)
    
    @api.model
    def create_form(self, name, unit,rec_name):
        self.create({
            'name': name,
            'unit': unit,
            'rec_name': rec_name
        })
