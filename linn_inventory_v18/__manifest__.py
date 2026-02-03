{
    'name': 'Linn Inventory',
    'version': '1.0',
    'summary': 'Custom inventory management module integrated with Linnworks.',
    'category': 'Inventory',
    'author': 'vinodkumar kotecha',
    'depends': ['stock','point_of_sale'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron.xml',
        'views/linn_inventory_views.xml',
        'views/linn_inventory_config.xml',
        'views/product_template.xml',
        'views/warehouse_template.xml',
        'views/product_category_custom.xml',
        # 'views/product_category_view.xml',
        'views/pricelist.xml',
        'views/product_properties.xml',
       
    ],
    'assets': {
        'web.assets_backend': [
            'linn_inventory/static/src/js/linn_dashboard.js',
            'linn_inventory/static/src/xml/linn_dashboard.xml',
            'linn_inventory/static/src/scss/product_kanban.scss',
             'linn_inventory/static/src/scss/linn_dashboard.scss',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
