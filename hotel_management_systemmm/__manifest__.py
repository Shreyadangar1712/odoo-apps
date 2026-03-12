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
{
    'name': 'Hotel Management',
    'version': '16.0.1.0.0',
    'category': 'Industries',
    'summary': """A complete Hotel Management System that cover all areas of 
     Hotel services""" ,
    'description': """The module helps you to manage rooms, amenities, 
     services, food, events and vehicles. End Users can book rooms and reserve 
     foods from hotel.""",
    'author': 'rishvi',
    'company': 'rishvi',
    'maintainer': 'rishvi',
    'website': 'https://rishvi.co.uk/',
    'depends': ['account', 'event', 'fleet', 'lunch','report_xlsx'],
    'data': [
        'security/hotel_management_odoo_groups.xml',
        'security/hotel_management_odoo_security.xml',
        'security/ir.model.access.csv',
        'data/ir_data_sequence.xml',
        'views/account_move_views.xml',
        'views/hotel_menu_views.xml',
        'views/hotel_amenity_views.xml',
        'views/hotel_service_views.xml',
        'views/hotel_floor_views.xml',
        'views/hotel_room_views.xml',
        'views/lunch_product_views.xml',
        'views/fleet_vehicle_model_views.xml',
        'views/room_booking_views.xml',
        'views/maintenance_team_views.xml',
        'views/maintenance_request_views.xml',
        'views/cleaning_team_views.xml',
        'views/cleaning_request_views.xml',
        'views/food_booking_line_views.xml',
        'views/dashboard_view.xml',
        'wizard/room_booking_detail_views.xml',
        'wizard/sale_order_detail_views.xml',
        'views/reporting_views.xml',
        'report/room_booking_reports.xml',
        'report/sale_order_reports.xml',
    ],

    'images': ['static/description/banner.png'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
    "price": 50,
    "currency": "EURO",
}
