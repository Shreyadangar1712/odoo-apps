from odoo import models, fields, api
from difflib import SequenceMatcher


class ResPartner(models.Model):
    _inherit = 'res.partner'


    def get_similarity(self,str1, str2):
        str1 = str1.strip().lower() if str1 else ""
        str2 = str2.strip().lower() if str2 else ""
        return round(SequenceMatcher(None, str1, str2).ratio() * 100, 2)

    def compare_partners(self):
        # self.ensure_one()
        Partner = self.env['res.partner']
        Similarity = self.env['partner.similarity']

        unlinked_partners = Partner.search([('parent_id', '=', False)])
        existing_partners = Partner.search([('parent_id', '!=', False)])
        
        for existing in existing_partners:
            name_similarity = self.get_similarity(self.name, existing.name)
            address_similarity = self.get_similarity(self.contact_address, existing.contact_address)

            if name_similarity > 50 or address_similarity > 50:
                Similarity.create({
                    'partner_id': self.id,
                    'existing_id': existing.id,
                    'name_similarity': name_similarity,
                    'address_similarity': address_similarity,
                })


