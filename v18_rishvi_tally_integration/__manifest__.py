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
    'name': 'Tally-Odoo Connector',
    'summary': 'Connecting Tally with Odoo for strong accounting management!',
    'category': 'Accounting',
    'version': '1.0.0',
    'sequence': 1,
    'author':'Rishvi Ltd',
    'company': 'Rishvi Ltd',
    'maintainer': 'Rishvi Ltd',
    "license": "AGPL-3",
    'website': 'https://rishvi.co.uk/',
    'description': """Tally-Odoo Connector
    Tally connector
    Tally 
    Tally accounts""",
    'depends': ['l10n_in_sale'],
    'demo': [
        'data/demo.xml',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_view.xml',
        'views/tally_invoice.xml',
        'views/tally_export.xml',
        'views/tally_field_mapping.xml',
        'views/sequence.xml',
    ],
    'images': ['static/description/banner.png'],
    'price':150.0,
    'currency': 'EUR',
    "application": True,
    "installable": True,
    "auto_install": False,
}
