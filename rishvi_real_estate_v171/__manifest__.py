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
    'name':'Real Estate.',
    'version':'1.1',
    'category':'Real Estate',
    'sequence':14,
    'summary':'',
    'description':""" Real Estate Management
        - Properties Hierarchy
        - Google Maps Integration
        - Units Reservation
        - Ownership Contracts Managament
        - Easy Tenant Management
        - Invoicing Management & Accounting Integration
        - Property Refund
        - Email Notifications
        - Integration with Odoo Website
        - Comprehensive Reporting
        """,
    'author':'Rishvi',
    'website':'https://rishvi.co.uk/',
    'depends':['base','account','analytic','project'],
    'data':[
        'security/real_estate_security.xml',
        'security/ir.model.access.csv',
        'security/ir.rule.xml',

        'wizard/sms_wizard_view.xml',
        'wizard/mail_wizard_view.xml',
        'wizard/installment_pay.xml',
        'wizard/realestate_pay.xml',
        'wizard/realestate_rental_pay.xml',
        'wizard/rental_contract_renewal.xml',
        'wizard/realestate_refund.xml',
        'wizard/duepayment.xml',
        'wizard/salesperson_sales.xml',
        'wizard/duepaymentunit.xml',
        'wizard/latepayment.xml',
        'wizard/latepaymentunit.xml',
        'wizard/occupancy.xml',

        'views/account_move.xml',
        'views/property_image.xml',
        'views/floor_plans.xml',
        'views/building_images.xml',
        'views/building_view.xml',

        'views/real_estate_payment_view.xml',
        'views/regions.xml',
        'views/building_desc_view.xml',
        'views/building_status_view.xml',
        'views/building_type_view.xml',
        'views/building_unit_view.xml',
        'views/installment_template_view.xml',
        'views/res_partner_view.xml',
        'views/unit_reservation_view.xml',
        'views/rental_contract_view.xml',
        'views/ownership_contract_view.xml',
        'views/real_estate_reports_view.xml',
        'views/configuration.xml',
        'views/template.xml',
        'views/installments_view.xml',

        'sequences/ownership_contract_sequence.xml',
        'sequences/rental_contract_sequence.xml',
        'sequences/reservation_sequence.xml',
        'sequences/property_sequence.xml',

        'report/report_sample.xml',
        'report/templates/report_reservation.xml',
        'report/templates/report_ownership_contract.xml',
        'report/templates/rental_contract.xml',
        'report/templates/report_quittance_letter.xml',
        'report/ownership_contract_bi_report.xml',
        'report/templates/occupany.xml',
        'report/templates/due_payments_customers.xml',
        'report/templates/due_payments_units.xml',
        'report/templates/late_payments_customers.xml',
        'report/templates/late_payments_units.xml',
        'report/rental_contract_bi_report.xml',

        'data/real_estate_demo.xml',
        'data/mail_template_data.xml',
    ],
    'installable':True,
    'auto_install':False,
    'application':True,

}

