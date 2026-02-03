from odoo import models, fields


class LinnCountries(models.Model):
    _name = 'linn.country'
    _description = 'Linnworks Country Data'
    _rec_name = 'country_name'

    country_name = fields.Char(string='Country Name')
    country_code = fields.Char(string='Country Code')
    currency_ids = fields.Char(string='Currency')
    country_ids = fields.Char(string='Country IDS')
    continent = fields.Char(string='Continent')
    customs_required = fields.Boolean(string ="Customs Required")
    tax_rate = fields.Integer(string ="Tax Rate")
    address_format = fields.Char(string='Address Format')
    regions_count = fields.Integer(string ="Regions Count")
 