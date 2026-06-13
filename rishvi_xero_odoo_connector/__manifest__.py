# -*- coding: utf-8 -*-
{
    'name': 'Odoo Xero Integration',
    'version': '19.0.0.0',
    'category': 'Services',
    'author': 'Rishvi Ltd.',
    'website': "www.rishvi.co.uk",
    'depends': ['base','account', 'purchase','stock','sale_management'],
    'summary': 'Xero Connector with REST API Xero Odoo Integration App xero accounting odoo xero connector odoo xero integration odoo xero accounting integration accounting app',
    'description': """
        Xero Connector with REST API
        ============================
        Seamlessly integrate Xero with Odoo for real-time financial data synchronization.

        This module enables smooth and automated exchange of accounting data between Odoo and Xero, including invoices, sales orders, purchase orders, products, customers, and payments.

        Key Features:
        - Real-time Xero–Odoo accounting integration
        - Secure REST API-based data synchronization
        - Automated invoice, sales, and purchase syncing
        - Centralized accounting workflow management
        - Reliable and scalable ERP connectivity

        A powerful accounting integration app designed to simplify bookkeeping and improve financial operations across Odoo and Xero.
        """,
        'data': [
        'views/xero_account.xml',
        'views/xero_account_view.xml',
        'views/xero_authentication_schedule.xml',
        'views/xero_invoice_view.xml',
        'views/xero_logs_view.xml',
        'views/xero_partner_category_view.xml',
        'views/xero_partner_view.xml',
        'views/xero_payment_view.xml',
        'views/xero_product_view.xml',
        'views/xero_purchase_order_view.xml',
        'views/xero_sale_order_view.xml',
        'views/xero_tax.xml',
        'views/tax.xml',
        'views/xero_dashboard_view.xml',
        'views/xero_logger_view.xml',
        'views/xero_product_category_view.xml',
        'views/res_company.xml',



        'wizard/connection_successfull_view.xml',

        'security/ir.model.access.csv',

        'data/type_demo_data.xml',
    ],
    'price': 259.00,
    'currency': 'EUR',
    'license': 'OPL-1',
    'installable': True,
    'auto_install': False,
    'assets': {
        'web.assets_backend': [
            # 'rishvi_xero_odoo_connector/static/src/js/dashboard.js',
            # 'rishvi_xero_odoo_connector/static/src/css/xero.css',
            # 'https://www.gstatic.com/charts/loader.js',
            # 'rishvi_xero_odoo_connector/static/src/xml/dashboard.xml',
            'rishvi_xero_odoo_connector/static/src/xml/xero_import_dashboard.xml',
                        'rishvi_xero_odoo_connector/static/src/xml/enableToggle.xml',

            'rishvi_xero_odoo_connector/static/src/js/xero_import_dashboard.js',
            'rishvi_xero_odoo_connector/static/src/scss/xero_dashboard.scss',

            'web/static/lib/jquery/jquery.js',
        ],
    },
}
