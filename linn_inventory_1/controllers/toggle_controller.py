from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)

class InventorySyncController(http.Controller):

    @http.route('/inventory/sync/toggle', type='json', auth='user')
    def toggle_sync(self, enable=False):
        _logger.info("Inside the toggle_sync")
        config = request.env['sync.controller.cron'].sudo().search([], limit=1)
        if not config:
            config = request.env['sync.controller.cron'].sudo().create({'enable_inventory_sync': enable})
        else:
            config.sudo().write({'enable_inventory_sync': enable})
        return {'success': True, 'enabled': enable}