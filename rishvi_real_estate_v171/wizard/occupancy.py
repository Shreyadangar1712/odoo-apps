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
# from odoo import exceptions
from odoo import api, fields, models 
from odoo.tools.translate import _
import time
import datetime
from datetime import datetime, date,timedelta
from dateutil import relativedelta

class occupancy_check(models.TransientModel):
    _name = 'occupancy.check'
    
    region_check= fields.Boolean('Filter by region')
    building_check= fields.Boolean('Filter by building')
    unit_check= fields.Boolean('Filter by building unit')

    region_ids= fields.Many2many('regions', string='Region',
                                     help="Only selected Regions will be printed. "
                                          "Leave empty to print all Regions.")
    building_ids= fields.Many2many('building', string='Building',
                                     help="Only selected building will be printed. "
                                          "Leave empty to print all building.")
    unit_ids= fields.Many2many('product.template',domain=[('is_property', '=', True)], string='Building Unit',
                                     help="Only selected building unit will be printed. "
                                          "Leave empty to print all building unit.")


    def check_report(self):
        [data] = self.read()
        datas = {
            'ids': [],
            'model': 'product.template',
            'form': data
        }
        return self.env.ref('rishvi_real_estate.report_unit_occupancy').report_action([],data=datas)

