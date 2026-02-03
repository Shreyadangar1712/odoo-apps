from odoo import http
from odoo.http import request


class ComparePartnerController(http.Controller):

    @http.route('/partners/compare', type='jsonrpc', auth='user', methods=['POST'])
    def compare_one_partner(self, partner_id=None):
        """
        Call compare_partners() on ONE partner record only.
        """

        try:
            # Call method on the model
            request.env['res.partner'].sudo().search([], limit=1).compare_partners()

            return {
                "status": "success",
                "message": "Partner similarity comparison completed."
            }

        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
