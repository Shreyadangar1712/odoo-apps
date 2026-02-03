from odoo import models, api, fields


class RishviDashboardDiscount(models.TransientModel):
    _name = 'rishvi.dashboard.discount'
    _description = 'Rishvi Dashboard Discount Enable'


    def action_enable_discounts(self):
        settings = self.env['res.config.settings'].sudo().create({
            'group_discount_per_so_line': True,  # Correct field for Odoo 18
        })
        settings.execute()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Success",
                "message": "Sales order line discounts have been enabled!",
                "sticky": True,
                "type": "success",
            },
        }



    @api.model
    def action_enable_pricelists(self):
        settings = self.env['res.config.settings'].sudo().create({
            'group_product_pricelist': True,  # Correct field for Odoo 18
        })
        settings.execute()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Success",
                "message": "Sales order Pricelists have been enabled!",
                "sticky": True,
                "type": "success",
            },
        }