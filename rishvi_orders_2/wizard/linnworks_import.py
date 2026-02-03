# my_module/wizards/import_wizard.py
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class LinnworksImportWizard(models.TransientModel):
    _inherit = 'linnworks.import.wizard'

    @api.model
    def _get_base_import_types(self):
        base_types = super()._get_base_import_types()
        additional_types = [
            ('import_orders', 'Import Orders'),
        ]
        return base_types + additional_types

    def action_import(self):
        if self.import_type == 'import_orders':
            integration_model = self.env['linnworks.integration'].search([], limit=1)
            if not integration_model:
                raise UserError(_("No Linnworks integration record found."))
            # if self.product_import_qty < 0:
                # print("\n\n\n=================mishan sharma")
            return integration_model.import_orders()
        return super().action_import()

