# -*- coding: utf-8 -*-
#############################################################################
#
#    Rishvi Pvt Ltd
#
#    Copyright (C) 2025-TODAY Rishvi Pvt Ltd (<https://www.rishvi.com>)
#    Author: Rishvi Development Team (<https://www.rishvi.com>)
#
#    This software is proprietary and confidential.
#
#    Unauthorized copying, modification, distribution, or use of this
#    software, via any medium, is strictly prohibited without the prior
#    written permission of Rishvi Pvt Ltd.
#
#    This software is licensed, not sold. A valid commercial license
#    from Rishvi Pvt Ltd is required to use this software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
#    OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
#    NON-INFRINGEMENT.
#
#    For licensing information, contact: support@rishvi.com
#
##########################################################################
import json
from odoo import http
from odoo.http import content_disposition, request
from odoo.tools import html_escape


class XLSXReportController(http.Controller):

    @http.route('/xlsx_reports', type='http', auth='user',
                methods=['POST'], csrf=False)
    def room_booking_xlsx_report(self, model, options, output_format,
                                     report_name):
        report_obj = request.env[model].sudo()
        options = json.loads(options)
        try:
            if output_format == 'xlsx':
                response = request.make_response(
                    None,
                    headers=[('Content-Type', 'application/vnd.ms-excel'),
                             ('Content-Disposition',
                              content_disposition(report_name + '.xlsx'))]
                )
                report_obj.get_xlsx_report(options, response)
                response.set_cookie('fileToken', 'dummy token')
                return response
        except Exception as e:
            s_error = http.serialize_exception(e)
            error = {
                'code': 200,
                'message': 'Odoo Server Error',
                'data': s_error
            }
            return request.make_response(html_escape(json.dumps(error)))
