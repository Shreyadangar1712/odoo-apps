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
from odoo.exceptions import ValidationError


class jewelleryAddons(models.Model):
        _inherit = ['product.template']

        metal_type=fields.Many2one(comodel_name='metal.master',string='Metal Name')
        metal_pieces=fields.Integer(string='Metal Pieces',default=0)
        metal_weight=fields.Float(string='Gross Metal Weight',digits=(1,3),default=0) #Net Weight
        metal_color=fields.Char(string='Metal Color/Finish')
        metal_rate=fields.Float(related='metal_type.rate',digits=(1,2),default=0)
        metal_gross_weight=fields.Float( string="Gross Weight",digits=(1,3))
        metal_net_weight=fields.Float(string="Gross Weight",digits=(1,3)) # Gross Weight
        product_text1=fields.Char(Placeholder="text for discription")
        product_text2=fields.Char(Placeholder="text for discription")
        product_text3=fields.Char(Placeholder="text for discription")
        product_text4=fields.Char(Placeholder="text for discription")
        product_text5=fields.Char(Placeholder="text for discription")
        product_text6=fields.Char(Placeholder="text for discription")
        show_price=fields.Boolean(string= "Show Break-Up",default=False)
        show_bis=fields.Boolean(string= "Show Hallmark",default=True)

        #discount
        discount_stone_price=fields.Float(default=0)
        discount_making_price=fields.Float(default=0)
        discount_making_percentage=fields.Float(default=0)

        sku=fields.Char(string="SKU")
        @api.constrains('sku')
        def _check_sku_unique(self):
            sku_counts = self.search_count([('sku', '=', self.sku), ('id', '!=', self.id)])
            if sku_counts  > 0:
                raise ValidationError("Sku already exists!")
            
        def write(self, vals):
            res = super(jewelleryAddons, self).write(vals)
            return res
        
        stone_detail_ids = fields.One2many('stone.description', 'form_id', string='Stone Description')
        

        #making discription
        making_cost=fields.Float(string='Making Cost in %',min=0,default=0)
        making_cost_per_gram=fields.Float(string='Making Cost per gram',min=0,default=0)
        
        calculation=fields.Char(compute='_compute_total_metal',default=0,invisible=True)
        
        stone_value_code=fields.Float('Stone Value Code',digits=(1,3),default=0)

        has_pricelist = fields.Boolean(
            string="Has Pricelist?",
            compute="_compute_has_pricelist",
            store=False  # Don't store in DB, computed dynamically
        )

        @api.depends('product_variant_ids')
        def _compute_has_pricelist(self):
            pricelist_item_obj = self.env["product.pricelist.item"]
            
            for product in self:
                # Check if any pricelist exists for this product or its variants
                pricelist_count = pricelist_item_obj.search_count([
                    '|',
                    ('product_tmpl_id', '=', product.id),  # Match product template
                    ('product_id', 'in', product.product_variant_ids.ids)  # Match product variants
                ])
                product.has_pricelist = pricelist_count > 0



        def action_set_cost_price(self):
            for rec in self:
                price=rec.calculation
                self.env['product.template'].browse(rec.id).write({'standard_price':price,'list_price':price})
            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
            }
        def action_reset_product_show_price(self):
            for rec in self:
                rec.discount_stone_price=0
                rec.discount_making_price=0
                rec.discount_making_percentage=0
            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
            }
 
        metal_cost_total=fields.Float(compute='_compute_total_metal',default=0)
        @api.depends(
        'metal_rate', 'metal_weight', 'making_cost', 
        'making_cost_per_gram', 'metal_net_weight', 'taxes_id',
        'stone_value_code', 'stone_detail_ids', 'show_price', 'categ_id'
        )
        def _compute_total_metal(self):
            product_template = self.env['product.template']
            purity_units = self.sudo().env['purity.units']

            for rec in self:
                # Determine multiplier code in one lookup
                purity_rec = purity_units.search(
                    [('name', '=', {7: 'DMUL', 8: 'PMUL'}.get(rec.categ_id.id, 'GMUL'))],
                    limit=1
                )

                unit_value = purity_rec.unit or 55.0

                try:
                    mul_code = float(unit_value)
                except (ValueError, TypeError):
                    mul_code = 55.0

                # Compute core values once
                metal_value = round(rec.metal_weight * rec.metal_rate, 2)
                making_value = round(metal_value * (rec.making_cost / 100), 2) if rec.making_cost else 0.0
                making_value+=int(float(rec.making_cost_per_gram)*float(mul_code))
                gst_value = round((int(rec.taxes_id.name[0]) / 100) * rec.list_price, 2) if rec.taxes_id else 0.0
                stone_code_multiple = mul_code * rec.stone_value_code

                # Price Breakdown Calculation
                price_breakup = {
                    'Gold Value': f"₹{metal_value}",
                    'Stone/Diamond Value': f"₹{stone_code_multiple}",
                    f'Making Charge {rec.making_cost}%': f"₹{making_value}",
                    'GST': f"₹{gst_value + 1}",
                }
                if rec.making_cost==0:
                    price_breakup = {
                    'Gold Value': f"₹{metal_value}",
                    'Stone/Diamond Value': f"₹{stone_code_multiple}",
                    f'Making Charge ': f"₹{making_value}",
                    'GST': f"₹{gst_value + 1}",
                    }

                price_breakup = {k: v for k, v in price_breakup.items() if v != "₹0"}

                metal_detail = {}
                metal_detail = {
                        f"{rec.categ_id.name} PURITY": f"{rec.metal_type.purity.name} K" if rec.metal_type.purity else "",
                        'Gross Weight': round(rec.metal_net_weight, 3),
                        'Net Weight': round(rec.metal_weight, 3),
                    }

                stone_detail = {}
                for stone in rec.stone_detail_ids:
                    stone_type_name = ((stone.stone_type.name or '').strip().capitalize() if stone.stone_type else '')
                    if not stone_type_name:
                        continue

                    stone_detail[f"{stone_type_name} Weight"] = round(stone.stone_weight or 0.0, 3)
                    stone_detail[f"{stone_type_name} Color"] = stone.stone_color or ''
                    stone_detail[f"{stone_type_name} Clarity"] = stone.stone_Clarity or ''

                # Generate HTML Table (Merging Metal + Stone Details)
                description_string = f"""
                    <style>table {{ border-collapse: collapse; width: 100%; }}</style>
                    <table>
                        {"".join(
                            f"<tr><td>&#x2022; {k}: {v}{' Ct' if 'Weight' in k and k in stone_detail else ' gms' if 'Weight' in k else ''}</td></tr>"
                            for k, v in {**metal_detail, **stone_detail}.items() if v
                        )}
                        {"".join(f"<tr><td>&#x2022; {text}</td></tr>" for text in 
                                [rec.product_text1, rec.product_text2, rec.product_text3,
                                rec.product_text4, rec.product_text5, rec.product_text6] if text)}
                    </table>
                """

                if rec.show_price:
                    price_breakup_string=self.apply_discount_to_price_breakup(price_breakup,rec.discount_stone_price, rec.discount_making_price,rec.taxes_id.name[0],rec.discount_making_percentage)
                    description_string+=price_breakup_string


                rec.description_ecommerce = description_string

                rec.metal_cost_total = stone_code_multiple + (rec.metal_rate * rec.metal_weight)

                product_template.search([('name', '=', rec.name)]).write({
                    'standard_price': round(rec.metal_cost_total * (1 + (rec.making_cost / 100)), 2)
                })
                rec.calculation = round(
                    (rec.metal_rate * rec.metal_weight) * (1 + (rec.making_cost / 100)), 2
                ) + stone_code_multiple + int(rec.making_cost_per_gram * mul_code)




                 
        def action_confirm(self):
            super(jewelleryAddons,self).action_confirm()
        
        def apply_discount_to_price_breakup(self, price_breakup, discount_stone_price, discount_making_price,gst_percentage,discount_making_cost_percentage):

            description_string = "<br><table style='border:1px'><tr><th><h6>PRICE BREAKUP</h6></th></tr>"

            discount_map = {
                "Stone": discount_stone_price if discount_stone_price else 0,
                "Making": discount_making_price if discount_making_price else 0,
            }

            for key, value in price_breakup.items():
                original_price = float(value.strip("₹"))
                discount_value = 0

                for discount_key, discount_amount in discount_map.items():
                    if discount_key in key and discount_amount:
                        discount_value = discount_amount
                        break

                new_price = max(0,discount_value)  # Ensure the new price is not negative
                if discount_making_cost_percentage==100 and "Making" in key:                        
                    description_string += (
                        f"<tr><td>&#x2022; {key}</td>"
                        f"<td><s style='color:red'>₹{int(original_price)}</s> → ₹{int(new_price)}</td></tr>"
                    )
                elif discount_value and original_price!=new_price and new_price!=False:                        
                    description_string += (
                        f"<tr><td>&#x2022; {key}</td>"
                        f"<td><s style='color:red'>₹{int(original_price)}</s> → ₹{int(new_price)}</td></tr>"
                    )
                elif "GST" in key:
                    description_string += f"<tr><td>&#x2022; {key}</td><td>{gst_percentage} %</td></tr>"
                else:
                    description_string += f"<tr><td>&#x2022; {key}</td><td>₹{int(original_price)}</td></tr>"

            description_string += "</table>"

            return description_string


class stoneDiscription(models.Model):
    _name = 'stone.description'
    _description = 'Stone Discription'
    _rec_name='rec_name'

    stone_type=fields.Many2one('stone.master',string='Stone Name')
    stone_quantity=fields.Integer(string='Pcs',default=0)
    stone_weight=fields.Float(string='Stone Weight',digits=(1,3),default=0)
    stone_Clarity=fields.Char(string='Clarity')
    stone_discription=fields.Char(string='Stone Discription')
    stone_color=fields.Char(string="Color")
    rec_name=fields.Char(compute='_compute_rec_name',string='Stone Detail')
    form_id = fields.Many2one('product.template', 'Form Id', ondelete='cascade', required=True)
	
      
    @api.depends('stone_type')
    def _compute_rec_name(self):
        for rec in self:
            if (rec.stone_type.rec_name== False):
                rec.rec_name="" 
            else:
                rec.rec_name=str(rec.stone_type.rec_name)
    
    