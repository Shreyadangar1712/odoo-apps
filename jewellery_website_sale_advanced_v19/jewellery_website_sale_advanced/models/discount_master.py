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


class discountRewardAddons(models.Model):
    _inherit = 'product.pricelist.item'

    base = fields.Selection(
        selection=[
            ('making_cost', 'Making Cost'),
            ('stone_price', 'On Stone'),
            ('stone_price_making_cost', 'On Stone & Making'),
            ('list_price', 'Sales Price'),
            ('standard_price', 'Cost'),
            ('pricelist', 'Other Pricelist')
        ],
        string="Based on",
        default='list_price',
        required=True,
        help="Base price for computation.\n"
             "Sales Price: The base price will be the Sales Price.\n"
             "Cost Price: The base price will be the cost price.\n"
             "Other Pricelist: Computation of the base price based on another Pricelist.")
    on_making_cost=fields.Float(string="On Making cost")
    on_stone_cost=fields.Float(string="On Stone cost")

    def _compute_base_price(self, product, quantity, uom, date, currency=None, **kwargs):

        currency = currency or self.env.company.currency_id
        currency.ensure_one()

        rule_base = self.base or 'list_price'
        if rule_base == 'pricelist' and self.base_pricelist_id:
            price = self.base_pricelist_id._get_product_price(
                product, quantity, currency=self.base_pricelist_id.currency_id, uom=uom, date=date
            )
            src_currency = self.base_pricelist_id.currency_id
        elif rule_base == "making_cost":
            src_currency = product.cost_currency_id
            db= product
            

            sm=""
            if db.categ_id.id==7:
                sm='DMUL'
            elif db.categ_id.id==8:
                sm='PMUL'
            else:
                sm='GMUL'
            multipier_code_value=self.env['purity.units'].sudo().search([('name','=',sm)])
            mul_code=55.0
            for i in multipier_code_value:
                mul_code=float(self.env['purity.units'].sudo().browse(i.id).unit)
                break

            stone_code_multiple=mul_code*db.stone_value_code 
            new_making_cost=db.making_cost*round(1-(self.price_discount/100),6) #Discount
            new_per_gram_making=int(float(db.making_cost_per_gram)*float(mul_code))*round(1-(self.price_discount/100),6)
            db.discount_stone_price=0
            db.discount_making_price=round((float(db.metal_rate)*float(db.metal_weight))*(round((new_making_cost)/100,6)),6)+new_per_gram_making

            new_value=round((float(db.metal_rate)*float(db.metal_weight))*(1+round((new_making_cost)/100,6)),6)+stone_code_multiple+new_per_gram_making
            
            increased_new_value=int(new_value/float(1-round(self.price_discount/100,6)))    
            price=int(increased_new_value)
            
        elif rule_base == "stone_price":
            src_currency = product.cost_currency_id
            db= product

            sm=""
            if db.categ_id.id==7:
                sm='DMUL'
            elif db.categ_id.id==8:
                sm='PMUL'
            else:
                sm='GMUL'
            multipier_code_value=self.env['purity.units'].sudo().search([('name','=',sm)])
            mul_code=55.0
            for i in multipier_code_value:
                mul_code=float(self.env['purity.units'].sudo().browse(i.id).unit)
                break
            
            new_making_cost=db.making_cost*round(1-(self.price_discount/100),6)

            stone_code_multiple=mul_code*db.stone_value_code*round(1-(self.price_discount/100),6) 
            new_stone_code_multiple=stone_code_multiple#Discount

            db.discount_stone_price=stone_code_multiple
            db.discount_making_price=0

            new_value=round((float(db.metal_rate)*float(db.metal_weight))*(round((new_making_cost)/100,6)),6)+new_stone_code_multiple+int(float(db.making_cost_per_gram)*float(mul_code))
            
            increased_new_value=int(new_value/float(1-round(self.price_discount/100,6)))    
            price=int(increased_new_value)
        
        elif rule_base == "stone_price_making_cost":
            src_currency = product.cost_currency_id
            db= product

            sm=""
            if db.categ_id.id==7:
                sm='DMUL'
            elif db.categ_id.id==8:
                sm='PMUL'
            else:
                sm='GMUL'
            multipier_code_value=self.env['purity.units'].sudo().search([('name','=',sm)])
            mul_code=55.0
            for i in multipier_code_value:
                mul_code=float(self.env['purity.units'].sudo().browse(i.id).unit)
                break
            
            new_stone_code_multiple=mul_code*db.stone_value_code*round(1-(self.on_stone_cost/100),6)

            new_making_cost=db.making_cost*round(1-(self.on_making_cost/100),6) #Discount
            new_per_gram_making=int(float(db.making_cost_per_gram)*float(mul_code))*round(1-(self.on_making_cost/100),6)

            db.discount_stone_price=new_stone_code_multiple
            db.discount_making_price=round((float(db.metal_rate)*float(db.metal_weight))*(round((new_making_cost)/100,6)),6)+new_per_gram_making
            db.discount_making_percentage=self.on_making_cost

            new_value=round((float(db.metal_rate)*float(db.metal_weight))*(1+round((new_making_cost)/100,6)),6)+new_stone_code_multiple+new_per_gram_making
            
            increased_new_value=int(new_value/float(1-round(self.price_discount/100,6)))    
            price=int(increased_new_value)        
            
        elif rule_base == "standard_price":
            src_currency = product.cost_currency_id
            price = product._price_compute(rule_base, uom=uom, date=date)[product.id]
        else: # list_price
            src_currency = product.currency_id
            price = product._price_compute(rule_base, uom=uom, date=date)[product.id]

        if src_currency != currency:
            price = src_currency._convert(price, currency, self.env.company, date, round=False)

        return price

   
    