# -*- coding: utf-8 -*-

{
    "name": "Partial Delivery Dropship",
    "version": "18.0.1.0",
    "category": "Inventory",
    "description": "This module is for Partial delivery and purchase.",
    "author": "Rishvi Ltd",
    "company": "Rishvi Ltd",
    "maintainer": "Rishvi Ltd",
    "website": "https://rishvi.co.uk/",
    "images": ["static/description/banner.png"],
    "depends": ["sale_management","stock","purchase","stock_dropshipping"],
    "data": [
        "data/stock_data.xml",
        "views/sale.xml",
        "views/stock_rule.xml",
        "views/warehouse.xml",
    ],
    "price": 40,
    "currency": "USD",
    "installable": True,
    "application": False,
    "auto_install": False,
    "license": "OPL-1",
}
