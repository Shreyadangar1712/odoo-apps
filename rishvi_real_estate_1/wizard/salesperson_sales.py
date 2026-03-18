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
from odoo import exceptions
from odoo import api, fields, models 
from odoo.tools.translate import _
import time
import datetime
from datetime import datetime, date,timedelta
from dateutil import relativedelta

class salesperson_sales_check(models.TransientModel):
    _name = 'salesperson.sales.check'
    
    date_from= fields.Date('From',required=True, default=lambda *a: time.strftime('%Y-%m-01'))
    date_to= fields.Date('To',required=True, default= lambda *a: str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10],)

    user_ids= fields.Many2many('res.users', string='Salesperson',
                                 help="Only selected salespersons will be printed. "
                                      "Leave empty to print all salesperson.")


    def check_report(self):
        [data] = self.read()
        datas = {
            'ids': [],
            'model': 'ownership.contract',
            'form': data
        }
        return self.env.ref('rishvi_real_estate.report_sales_rep_rs').report_action([],data=datas)