# -*- coding: utf-8 -*-
from odoo import models, fields, api
from difflib import SequenceMatcher
import logging

_logger = logging.getLogger(__name__)

class LinnworkInfo(models.Model):
    _name = 'partner.similarity'
    _description = 'Similar Partner Records'

    partner_id = fields.Many2one('res.partner', string="Original Partner")
    existing_id = fields.Many2one('res.partner', string="Similar Partner")
    
    partner_address = fields.Text(compute="_compute_addresses", store=True)
    existing_address = fields.Text(compute="_compute_addresses", store=True)

    @api.depends('partner_id', 'existing_id')
    def _compute_addresses(self):
        for record in self:
            record.partner_address = record.partner_id.contact_address or ''
            record.existing_address = record.existing_id.contact_address or ''

    name_similarity = fields.Float(string="Name Similarity (%)")
    address_similarity = fields.Float(string="Address Similarity (%)")

    merge_disabled = fields.Boolean(string="Merge Disabled", default=False)
    merge_status = fields.Char(string="Merge Status", compute="_compute_merge_status")
    

    @api.depends('merge_disabled')
    def _compute_merge_status(self):
        for record in self:
            record.merge_status = "✅ Merged" if record.merge_disabled else "Pending"


    def get_similarity(self,str1, str2):
        str1 = str1.strip().lower() if str1 else ""
        str2 = str2.strip().lower() if str2 else ""
        if str1 =="" or str2 == "":
            return 0
        return round(SequenceMatcher(None, str1, str2).ratio() * 100, 2)

    #@api.model
    def compare_partners(self):
        _logger.info("Inside the compare partner")
        Partner = self.env['res.partner']
        Similarity = self.env['partner.similarity']

        unlinked_partners = Partner.search([('parent_id', '=', False),("sale_order_ids", "!=", False)])
        existing_partners = Partner.search([('parent_id', '=', False),("sale_order_ids", "!=", False)])
        
        for unlinked_partner in unlinked_partners:
            for existing in existing_partners:
                if existing.id == unlinked_partner.id:
                    continue
                name_similarity = self.get_similarity(unlinked_partner.name, existing.name)
                address_similarity = self.get_similarity(unlinked_partner.contact_address, existing.contact_address)

                if name_similarity > 60 or address_similarity > 60:
                    if not Similarity.search([('partner_id', '=', unlinked_partner.id), ('existing_id', '=', existing.id)]):

                        Similarity.create({
                            'partner_id': unlinked_partner.id,
                            'existing_id': existing.id,
                            'name_similarity': name_similarity,
                            'address_similarity': address_similarity,
                        })


    # def merge_the_user(self):
    #     Partner = self.env['res.partner']
    #     for record in self:
    #         if record.partner_id and record.existing_id:
    #             record.existing_id.write({'parent_id' : record.partner_id.id})
    #             record.merge_disabled = True
    #             child_partner=Partner.search([('parent_id', '=', record.existing_id.id)])
    #             for rec in child_partner:
    #                 rec.existing_id.write({'parent_id' : record.partner_id.id})

    def merge_the_user(self):
        Partner = self.env['res.partner']
        
        for record in self:
            if record.partner_id and record.existing_id:
                
                # Step 1: Move existing partner under original partner
                record.existing_id.write({
                    'parent_id': record.partner_id.id
                })
                
                record.merge_disabled = True

                # Step 2: Move any children of existing partner under original partner
                child_partners = Partner.search([
                    ('parent_id', '=', record.existing_id.id)
                ])
                
                for child in child_partners:
                    child.write({
                        'parent_id': record.partner_id.id
                    })

        
    



        