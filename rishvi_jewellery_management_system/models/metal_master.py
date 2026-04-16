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

class MetalMaster(models.Model):
    _name = 'metal.master'
    _inherit='purity.units'
    _rec_name='rec_name'

    name=fields.Char("Metal Name",placeholder="e.g Gold or Silver",required=True)
    purity=fields.Many2one("purity.units")
    rate=fields.Float("Rate",placeholder="Set a Today rate for this metal",required=True)
    rec_name=fields.Char(compute='_compute_rec_name')

    __sql_constraints = [
        ('name_uniq', 'unique (name,purity)','This metal is already there. pls change the rate')
    ]
    
    @api.onchange('name')
    def set_upper(self):    
        self.name = str(self.name).upper()   
        return
        
    @api.model
    def _compute_rec_name(self):
        for rec in self:
            if (rec.purity == False) or (rec.name==False):
                rec.rec_name=""
            else:
                rec.rec_name=str(rec.name)+'  '+str(rec.purity.rec_name)
    def action_set_cost_price(self):
        db_product_template=self.env['product.template']
        product_dict =db_product_template.search([])
        for record in product_dict:
            price=record.calculation
            record.write({'standard_price':price,'list_price':price})
    
    def refresh_compute__price(self):
        db_product_template=self.env['product.pricelist']
        product_dict_pricelist =db_product_template.search([])
        product_dict =[]
        for item in product_dict_pricelist.item_ids:
            product_dict.append(item)
        purity_units = self.sudo().env['purity.units']
        for record in product_dict:
            record.product_tmpl_id._compute_total_metal()
            # Determine multiplier code in one lookup
            mul_code = float(purity_units.search([('name', '=', {7: 'DMUL', 8: 'PMUL'}.get(record.product_tmpl_id.categ_id.id, 'GMUL'))], limit=1).unit or 55.0)
            # Compute core values once
            metal_value = round(record.product_tmpl_id.metal_weight * record.product_tmpl_id.metal_rate, 2)
            making_value = round(metal_value * (record.product_tmpl_id.making_cost / 100), 2) if record.product_tmpl_id.making_cost else 0.0
            making_value+=int(float(record.product_tmpl_id.making_cost_per_gram)*float(mul_code))
            gst_value = round((int(record.product_tmpl_id.taxes_id.name[0]) / 100) * record.product_tmpl_id.list_price, 2) if record.product_tmpl_id.taxes_id else 0.0
            stone_code_multiple = mul_code * record.product_tmpl_id.stone_value_code

            price_breakup = {
                'Gold Value': f"₹{metal_value}",
                'Stone/Diamond Value': f"₹{stone_code_multiple}",
                f'Making Charge {record.product_tmpl_id.making_cost}%': f"₹{making_value}",
                'GST': f"₹{gst_value + 1}",
            }
            if record.product_tmpl_id.making_cost==0:
                price_breakup = {
                'Gold Value': f"₹{metal_value}",
                'Stone/Diamond Value': f"₹{stone_code_multiple}",
                f'Making Charge ': f"₹{making_value}",
                'GST': f"₹{gst_value + 1}",}

            price_breakup = {k: v for k, v in price_breakup.items() if v != "₹0"}

            if (price_breakup!=False and record.product_tmpl_id.discount_stone_price!=False and record.product_tmpl_id.discount_making_price!=False and record.product_tmpl_id.taxes_id.name[0]!=False):
                record.product_tmpl_id.apply_discount_to_price_breakup(price_breakup,record.product_tmpl_id.discount_stone_price,record.product_tmpl_id.discount_making_price,record.product_tmpl_id.taxes_id.name[0],record.product_tmpl_id.discount_making_percentage)

    def action_reset_show_price(self):
        db_product_template=self.env['product.template']
        product_dict =db_product_template.search([])
        purity_units = self.sudo().env['purity.units']
        for record in product_dict:
            if record.discount_stone_price!=0 or record.discount_making_price!=0:
                record.discount_stone_price=0
                record.discount_making_price=0
                record.discount_making_percentage=0
                mul_code = float(purity_units.search([('name', '=', {7: 'DMUL', 8: 'PMUL'}.get(record.categ_id.id, 'GMUL'))], limit=1).unit or 55.0)
                metal_value = round(record.metal_weight * record.metal_rate, 2)
                making_value = round(metal_value * (record.making_cost / 100), 2) if record.making_cost else 0.0
                making_value+=int(float(record.making_cost_per_gram)*float(mul_code))
                gst_value = round((int(record.taxes_id.name[0]) / 100) * record.list_price, 2) if record.taxes_id else 0.0
                stone_code_multiple = mul_code * record.stone_value_code

                price_breakup = {
                    'Gold Value': f"₹{metal_value}",
                    'Stone/Diamond Value': f"₹{stone_code_multiple}",
                    f'Making Charge {record.making_cost}%': f"₹{making_value}",
                    'GST': f"₹{gst_value + 1}",
                }
                if record.making_cost==0:
                    price_breakup = {
                    'Gold Value': f"₹{metal_value}",
                    'Stone/Diamond Value': f"₹{stone_code_multiple}",
                    f'Making Charge ': f"₹{making_value}",
                    'GST': f"₹{gst_value + 1}",}

                price_breakup = {k: v for k, v in price_breakup.items() if v != "₹0"}
                if (price_breakup!=False and record.discount_stone_price!=False and record.discount_making_price!=False and record.taxes_id.name[0]!=False):
                    record.apply_discount_to_price_breakup(price_breakup,record.discount_stone_price,record.discount_making_price,record.taxes_id.name[0],record.discount_making_percentage)