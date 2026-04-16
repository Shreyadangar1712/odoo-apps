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
    "name": "Tawk Discuss Integration",
    "version": "18.0.1.0.0",
    "category": "Discuss",
    "summary": "Import tawk.to chats into Odoo Discuss as threaded personal chats",
    'author':'Rishvi Ltd',
    'company': 'Rishvi Ltd',
    'maintainer': 'Rishvi Ltd',
    'website':'https://rishvi.co.uk/',
    "license": "LGPL-3",
    "depends": ["mail"],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "data/ir_cron.xml",
        "views/tawk_discuss_views.xml",
        "views/res_config_settings_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "tawk_discuss_integration/static/src/discuss/tawk_sidebar.js",
            "tawk_discuss_integration/static/src/discuss/tawk_sidebar.xml",
        ],
    },
    'images': ['static/description/banner.png'],
    "price": 150.0,
    "currency": "EUR",
    "installable": True,
    "application": True,
}