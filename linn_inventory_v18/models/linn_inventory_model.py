from odoo import models, fields, api

class LinnInventory(models.Model):
    _name = 'linn.inventory'
    _description = 'Linn Inventory Integration'

    name = fields.Char(string='Name', required=True)


    def action_sync_inventory(self):
        # Placeholder for integration logic
        for record in self:
            record.synced = True
