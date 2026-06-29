
{
    'name': 'Stream Odoo Connector',
    'version': '19.1',
    'summary': 'Integration between Odoo and Stream Transport Management System',
    'description': """
Stream Odoo Connector

Features:
---------
* Export Sale Orders to Stream
* Consignment Creation
* Order Status Synchronization
* Run Details Synchronization
* Stream Depot Management
* Delivery Method Mapping
* Stream Services Configuration
* Automated Scheduled Jobs
* Webhook Integration
* Tracking Information Management
* Chatter Notifications for Status Updates

This module provides a complete integration between
Odoo Sales and the Stream Transport Platform.
    """,
    'category': 'Sales/Inventory',
    'author':'Rishvi Ltd',
    'company': 'Rishvi Ltd',
    'maintainer': 'Rishvi Ltd',
    'website': "www.rishvi.co.uk",
    'license': 'LGPL-3',

    'depends': [
        'mail',
        'web',
        'sale',
        'stock_delivery',
    ],

    'data': [
        'security/ir.model.access.csv',

        'data/ir_actions_server_data.xml',
        'data/ir_cron.xml',

        'views/res_company.xml',
        'views/sale_order.xml',
        'views/sale_order_line.xml',
        'views/delivery_carrier.xml',
        'views/run_details.xml',
        'views/stream_depot_views.xml',
        'views/stream_depot_delivery_method_views.xml',
        'views/stream_services.xml',

        'wizard/success_message.xml',
    ],
    'images': ['static/description/banner.png'],
    'price': 650.00,
    'currency': 'USD',
    'installable': True,
    'application': True,
    'auto_install': False,
}