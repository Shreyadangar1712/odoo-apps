from odoo import api, fields, models
import logging
from odoo import _
_logger = logging.getLogger(__name__)


class XeroTax(models.Model):
    _name = 'xero.tax'
    _description = 'Xero Tax'
    _rec_name = 'name'
   

    name = fields.Char(string="Tax Name", required=True)
    company_id = fields.Many2one(
        'res.company',
        string="Company",
        required=True,
        default=lambda self: self.env.company,
    )

    #for archive feature
    active = fields.Boolean(default=True)

    xero_tax_type_id = fields.Char(string="Xero Tax Type", index=True)
    xero_record_taxtype = fields.Char(string="Xero Report Tax Type")

    amount = fields.Float(string="Tax Amount")
    amount_type = fields.Selection(
        [
            ('percent', 'Percentage'),
            ('fixed', 'Fixed'),
            ('division', 'Division'),
            ('group', 'Group'),
        ],
        string="Amount Type",
        default='percent',
        required=True,
    )

    type_tax_use = fields.Selection(
        [
            ('sale', 'Sales'),
            ('purchase', 'Purchases'),
            ('none', 'None'),
        ],
        string="Tax Type",
        required=True,
    )

    price_include = fields.Boolean(string="Included in Price")

    price_include_override = fields.Selection(
        [
            ('tax_included', 'Tax Included'),
            ('tax_excluded', 'Tax Excluded'),
        ],
        string="Tax Include Override",
    )
    account_tax_id = fields.Many2one(
    'account.tax',
    string='Odoo Tax',
    ondelete='cascade'
)
    _sql_constraints = [
        (
            'xero_tax_unique_variant',
            'unique(company_id, xero_tax_type_id, type_tax_use, price_include)',
            'This Xero tax variant already exists for this company.'
        ),
    ]

    