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
    'name': 'CCAvenue Payment Acquirer For eCommerce Website',
    'version': '18.0.1.0.0',
    'author': "Rishvi",
    'maintainer': 'Rishvi',
    'website': "https://rishvi.co.uk/",
    'images': ['static/description/banner.png'],
    'depends': ['payment', 'account', 'website_sale','base'],
    'data': [
        'views/payment_provider_views.xml',
        'views/cc_avenue_templates.xml',
        'data/payment_provider_data.xml',
    ],
    'external_dependencies': {'python': ['pay_ccavenue']},
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
    "price": 0,
    "currency": "EUR",
}
