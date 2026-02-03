
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    partner_ids = fields.Many2many('res.partner', string="Default Followers in Projects")

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        partner_ids = self.env['ir.config_parameter'].sudo().get_param('rishvi_default_follower_project.default_partner_ids', False)
        if partner_ids:
            res.update(
                partner_ids=[(6, 0, list(map(int, partner_ids.split(','))))],
            )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('rishvi_default_follower_project.default_partner_ids', ','.join(map(str, self.partner_ids.ids)))