# -*- coding: utf-8 -*-
{
    'name': "Default Follower Project and Task",
    'summary': "Add default follwers in projects and Task.",
    'description': """
        Add default follwers in projects and Task.
    """,
    'author': "Rishvi Ltd",
    'website': "https://rishvi.co.uk/",
    # for the full list
    'category': 'Project Management',
    'version': '18.0.0.1',
    'depends': ['project'],
    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
        'views/project_views.xml',
    ],
    'qweb': [],
    'images': ['static/description/banner.png'],
    'license': 'OPL-1',
    'installable': True,
    'live_test_url': '',
    'price': 19.99,
    'currency': 'USD',
    'auto_install': False,
    'application': True,
}

