from odoo import models, fields, api, _

class AccountTax(models.Model):
    _inherit = 'account.tax'

    same_tax_country_ids = fields.Many2many(
        'linn.country',
        string="Linnworks Countries",
        compute='_compute_same_tax_countries',
        store=False,
        help="Countries that have the same tax rate as this tax."
    )

    @api.depends('amount')
    def _compute_same_tax_countries(self):
        """Automatically link countries having the same tax rate as this tax."""
        for tax in self:
            # Search for countries having this tax rate
            countries = self.env['linn.country'].search([('tax_rate', '=', tax.amount)])
            tax.same_tax_country_ids = countries
 