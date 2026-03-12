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
import logging

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter

from odoo import models

_logger = logging.getLogger(__name__)


class RoomBookingReportXlsx(models.AbstractModel):
    _name = "report.rishvi_hotel_management_system.report_room_booking_xlsx"
    _inherit = "report.report_xlsx.abstract"

    def generate_xlsx_report(self, workbook, data, obj):
        """Generate XLSX report for Room Booking"""
        import json

        _logger.info("=== GENERATE XLSX REPORT START ===")
        _logger.info(f"Data received: {data}")

        # Parse the JSON string from options
        if data.get("options"):
            try:
                options_data = json.loads(data.get("options", "{}"))
                booking_data = options_data.get("booking", [])
            except json.JSONDecodeError:
                booking_data = []
        else:
            booking_data = data.get("booking", [])

        _logger.info(f"Booking data: {booking_data}")

        # Create worksheet
        sheet = workbook.add_worksheet("Room Booking")

        # Define formats
        cell_format = workbook.add_format(
            {"font_size": 14, "bold": True, "align": "center", "border": True}
        )
        head = workbook.add_format(
            {"align": "center", "bold": True, "font_size": 23, "border": True}
        )
        body = workbook.add_format(
            {"align": "left", "text_wrap": True, "border": True, "valign": "top"}
        )

        # Create header
        sheet.merge_range("A1:F1", "Room Booking", head)
        sheet.set_column("A2:F2", 18)
        sheet.set_row(0, 30)
        sheet.set_row(1, 20)

        # Write column headers
        sheet.write("A2", "Sl No.", cell_format)
        sheet.write("B2", "Guest Name", cell_format)
        sheet.write("C2", "Room No.", cell_format)
        sheet.write("D2", "Check In", cell_format)
        sheet.write("E2", "Check Out", cell_format)
        sheet.write("F2", "Reference No.", cell_format)

        # Write data rows
        row = 2
        value = 1

        _logger.info(f"Total records to write: {len(booking_data)}")

        for record in booking_data:
            _logger.info(f"Writing record {value}: {record}")

            partner_id = record.get("partner_id", "")
            room = record.get("room", "")
            checkin = record.get("checkin_date", "")
            checkout = record.get("checkout_date", "")
            ref_no = record.get("name", "")

            sheet.write(row, 0, value, body)
            sheet.write(row, 1, str(partner_id), body)
            sheet.write(row, 2, str(room), body)
            sheet.write(row, 3, str(checkin), body)
            sheet.write(row, 4, str(checkout), body)
            sheet.write(row, 5, str(ref_no), body)

            row += 1
            value += 1

        _logger.info("=== GENERATE XLSX REPORT END ===")