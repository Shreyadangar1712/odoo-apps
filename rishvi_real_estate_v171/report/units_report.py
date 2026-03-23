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
from odoo import api, fields, models, tools
from odoo import api, fields, models 

class report_units(models.Model):
    _name = "units.report"
    _description = "Units Statistics"
    _auto = False
    
    partner_id= fields.Many2one('res.partner','Owner', )
    building_id= fields.Many2one('building','Building', )
    nbr= fields.Integer('# Units', readonly=True)  
    desc= fields.Many2one('building.desc','Building Description', )
    rooms= fields.Char('Rooms', size=32 )
    type= fields.Many2one('building.type','Building Unit Type', )
    state= fields.Many2one('building.status','Building Unit Status', )

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
