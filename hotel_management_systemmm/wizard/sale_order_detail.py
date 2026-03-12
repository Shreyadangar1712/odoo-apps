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
import io
from odoo import fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools import date_utils

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class SaleOrderWizard(models.TransientModel):
    _name = "sale.order.detail"
    _description = "Room Booking Details"

    checkin = fields.Date(help="Choose the Checkin Date", string="Check In")
    checkout = fields.Date(help="Choose the Checkout Date", string="Check Out")

    def action_sale_order_pdf(self):
        data = {
            'booking': self.generate_data(),
        }
        return self.env.ref(
            'rishvi_hotel_management_system.action_report_sale_order').report_action(
            self, data=data)

    def action_sale_order_excel(self):
        booking_data = self.generate_data()

        # Convert datetime to string format for Excel
        for rec in booking_data:
            if rec.get("checkin_date"):
                rec["checkin_date"] = rec["checkin_date"].strftime("%Y-%m-%d %H:%M:%S")
            if rec.get("checkout_date"):
                rec["checkout_date"] = rec["checkout_date"].strftime("%Y-%m-%d %H:%M:%S")

        # Return proper action with correct report name
        return {
            "type": "ir.actions.report",
            "report_type": "xlsx",
            "report_name": "rishvi_hotel_management_system.report_sale_order_xlsx",
            "data": {
                "booking": booking_data,
            },
        }

    def generate_data(self):
        domain = []
        if self.checkin and self.checkout:
            if self.checkin > self.checkout:
                raise ValidationError(_(
                    'Check-in date should be less than Check-out date'))
        if self.checkin:
            domain.append(('checkin_date', '>=', self.checkin), )
        if self.checkout:
            domain.append(('checkout_date', '<=', self.checkout), )
        room_booking = self.env['room.booking'].search_read(domain=domain,
                                                            fields=[
                                                                'partner_id',
                                                                'name',
                                                                'checkin_date',
                                                                'checkout_date',
                                                                'amount_total'])
        for rec in room_booking:
            rec['partner_id'] = rec['partner_id'][1]
        return room_booking

    def get_xlsx_report(self, data, response):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        cell_format = workbook.add_format(
            {'font_size': '14px', 'bold': True, 'align': 'center',
             'border': True})
        head = workbook.add_format(
            {'align': 'center', 'bold': True, 'font_size': '23px',
             'border': True})
        body = workbook.add_format(
            {'align': 'left', 'text_wrap': True, 'border': True})
        sheet.merge_range('A1:F1', 'Sale Order', head)
        sheet.set_column('A2:F2', 18)
        sheet.set_row(0, 30)
        sheet.set_row(1, 20)
        sheet.write('A2', 'Sl No.', cell_format)
        sheet.write('B2', 'Guest Name', cell_format)
        sheet.write('C2', 'Check In', cell_format)
        sheet.write('D2', 'Check Out', cell_format)
        sheet.write('E2', 'Reference No.', cell_format)
        sheet.write('F2', 'Total Amount', cell_format)
        row = 2
        column = 0
        value = 1
        for i in data['booking']:
            sheet.write(row, column, value, body)
            sheet.write(row, column + 1, i['partner_id'], body)
            sheet.write(row, column + 2, i['checkin_date'], body)
            sheet.write(row, column + 3, i['checkout_date'], body)
            sheet.write(row, column + 4, i['name'], body)
            sheet.write(row, column + 5, "{:.2f}".format(i['amount_total']),
                        body)
            row = row + 1
            value = value + 1
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()



