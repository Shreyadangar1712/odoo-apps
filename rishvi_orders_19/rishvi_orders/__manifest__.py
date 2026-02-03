# -*- coding: utf-8 -*-

{
    "name": "Rishvi Orders",
    "version": "19.0.1.0.0",
    "category": "General",
    "depends": ["sale","crm","product","web",'base',"contacts","point_of_sale","linn_inventory_1"],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_cron.xml",
        'views/sale_shipping_services.xml',

        "views/sale_order.xml",
        "views/contact_merger.xml",
        'views/source.xml',
        'views/sub_source.xml',
        'views/taxes.xml',
        'views/currency.xml',
        'views/customer.xml',
        'views/linn_countries.xml',
        'views/linn_orders_operation.xml',
    ],
    'assets': {
    'web.assets_backend': [
            'rishvi_orders/static/src/xml/linn_orders_dashboard.xml',
            'rishvi_orders/static/src/js/linn_orders_dashboard.js',
            'rishvi_orders/static/src/scss/linn_orders_dashboard.scss',

    ],
    },
    "images": [
    "static/description/cover.jpg",
],
    "installable": True,
    "application": False,
    "auto_install": True,
    "license": "OPL-1",
}
