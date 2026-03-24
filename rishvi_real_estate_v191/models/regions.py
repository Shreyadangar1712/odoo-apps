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
from odoo.tools.translate import _
from odoo import api, fields, models 

class regions(models.Model):
    _name = "regions"
    _description = "Region"
    _parent_name = "region_id"
    _parent_store = True
    _order = 'complete_name'
    _rec_name = 'complete_name'
    _inherit = ['mail.thread']

    @api.depends('name', 'region_id')
    def _compute_complete_name(self):
        """ Forms complete name of region from region to child region. """
        name = self.name
        current = self
        while current.region_id:
            current = current.region_id
            name = '%s/%s' % (current.name, name)
        self.complete_name = name


    @api.depends('name', 'region_id.complete_name')
    def _compute_complete_name(self):
        """ Forms complete name of location from parent location to child location. """
        if self.region_id.complete_name:
            self.complete_name = '%s/%s' % (self.region_id.complete_name, self.name)
        else:
            self.complete_name = self.name

    name= fields.Char('Name',required=True)
    complete_name = fields.Char(
        'Complete Name', compute='_compute_complete_name', recursive=True,
        store=True)
    child_ids= fields.One2many('regions', 'region_id', 'Contains')
    parent_left= fields.Integer('Left Parent', index=True)
    parent_right= fields.Integer('Right Parent', index=True)
    account= fields.Many2one('account.account','Discount Account', )
    account_me= fields.Many2one('account.account','Managerial Expenses Account', )
    region_id= fields.Many2one('regions','Parent Region', ondelete='cascade')
    parent_path = fields.Char(index=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    latlng_ids= fields.One2many('latlng.line', 'region_id', string='LatLng List',copy=True)
    map= fields.Char('Map')
    street = fields.Char()
    street2 = fields.Char()
    zip = fields.Char(change_default=True)
    city = fields.Char()
    state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict', domain="[('country_id', '=?', country_id)]")
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict')
    country_code = fields.Char(related='country_id.code', string="Country Code")

    def unit_status(self, unit_id):
        self.env.cr.execute("select state from building_unit where id = "+str(int(unit_id)))
        res = self.env.cr.dictfetchone()
        if res:
            if res["state"]:
                return res["state"]


class latlng_line(models.Model):
    _name = "latlng.line"
    
    lat = fields.Float('Latitude', digits=(9, 6), required=True)
    lng = fields.Float('Longitude', digits=(9, 6), required=True)
    url = fields.Char('URL', required=True)
    region_id = fields.Many2one('regions', 'Region')
    unit_id = fields.Many2one('product.template', 'Unit', domain=[('is_property', '=', True)], required=True)
    state = fields.Selection(string='State', related='unit_id.state', store=True, readonly=True)

    @api.onchange('unit_id')
    def onchange_unit(self):
        action_id = self.env.ref('rishvi_real_estate.building_unit_act1').id
        '#id=33&cids=1&action=317&model=product.template&view_type=form&menu_id=205'
        link = '#id=%s&action=%s&model=product.template&view_type=form' % (
            self.unit_id.id, action_id)
        self.url = link

    @api.onchange('url')
    def onchange_url(self):
        if self.url:
            url = self.url
            self.unit_id = int(((url.split("#")[1]).split("&")[0]).split("=")[1])
        else:
            self.unit_id = None
            self.state = None