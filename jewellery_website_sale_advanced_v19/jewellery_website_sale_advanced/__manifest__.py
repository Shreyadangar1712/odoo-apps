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
    'name': "Jewellery Website Sale Advanced",
    'author': "Rishvi",
    'website': "https://rishvi.co.uk/",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['account', 'base', 'web', 'sale', 'product', 'website_sale', 'website_sale_stock',
                'website_sale_wishlist', 'website_sale_comparison', 'loyalty', 'sale_loyalty', 'website_payment',
                'website_mail', 'portal_rating', 'digest', 'delivery', 'website'],
    'data': [
        'security/ir.model.access.csv',
        'views/purity_unit_views.xml',
        'views/stone_master_views.xml',
        'views/metal_master_views.xml',
        'views/jewellery_master_view.xml',
        'views/sku_code_template.xml',
        'views/invoice_addons.xml',
        'views/delivery_track.xml',
        'views/my_invoice.xml',
        'views/discount_master_view.xml'
    ],
    'assets': {
        'web.assets_frontend': [
            'jewellery_website_sale_advanced/static/src/css/signup.css',
            'jewellery_website_sale_advanced/static/src/js/signup.js',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
    "license": "OPL-1",
    "price": 0,
    "currency": "EUR",
}

