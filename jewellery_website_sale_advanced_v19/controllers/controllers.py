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
import json
from odoo.addons.website_sale.controllers.main import WebsiteSale
from datetime import date
import requests
from odoo import models, api,fields, http, SUPERUSER_ID, tools, _
import logging
from werkzeug.exceptions import Forbidden, NotFound
from odoo.http import request, route

from odoo.tools.json import scriptsafe as json_scriptsafe

_logger = logging.getLogger(__name__)



class WebsiteAuth(WebsiteSale):
    @http.route(['/shop/cart'], type='http', auth="user", website=True, sitemap=False)
    def cart(self, access_token=None, revive='', **post):
        """
        Main cart management + abandoned cart revival
        access_token: Abandoned cart SO access token
        revive: Revival method when abandoned cart. Can be 'merge' or 'squash'
        """
        order = request.website.sale_get_order()
        if order and order.carrier_id:
            # Express checkout is based on the amout of the sale order. If there is already a
            # delivery line, Express Checkout form will display and compute the price of the
            # delivery two times (One already computed in the total amount of the SO and one added
            # in the form while selecting the delivery carrier)
            order._remove_delivery_line()
        if order and order.state != 'draft':
            request.session['sale_order_id'] = None
            order = request.website.sale_get_order()

        request.session['website_sale_cart_quantity'] = order.cart_quantity

        values = {}
        if access_token:
            abandoned_order = request.env['sale.order'].sudo().search([('access_token', '=', access_token)], limit=1)
            if not abandoned_order:  # wrong token (or SO has been deleted)
                raise NotFound()
            if abandoned_order.state != 'draft':  # abandoned cart already finished
                values.update({'abandoned_proceed': True})
            elif revive == 'squash' or (revive == 'merge' and not request.session.get('sale_order_id')):  # restore old cart or merge with unexistant
                request.session['sale_order_id'] = abandoned_order.id
                return request.redirect('/shop/cart')
            elif revive == 'merge':
                abandoned_order.order_line.write({'order_id': request.session['sale_order_id']})
                abandoned_order.action_cancel()
            elif abandoned_order.id != request.session.get('sale_order_id'):  # abandoned cart found, user have to choose what to do
                values.update({'access_token': abandoned_order.access_token})

        values.update({
            'website_sale_order': order,
            'date': fields.Date.today(),
            'suggested_products': [],
        })
        if order:
            order.order_line.filtered(lambda l: l.product_id and not l.product_id.active).unlink()
            values['suggested_products'] = order._cart_accessories()
            values.update(self._get_express_shop_payment_values(order))

        values.update(self._cart_values(**post))
        return request.render("website_sale.cart", values)

    @http.route(['/shop/cart/update'], type='http', auth="public", methods=['POST'], website=True)
    def cart_update(
        self, product_id, add_qty=1, set_qty=0,
        product_custom_attribute_values=None, no_variant_attribute_values=None,
        express=False, **kwargs
    ):
        """This route is called when adding a product to cart (no options)."""
        sale_order = request.website.sale_get_order(force_create=True)
        if sale_order.state != 'draft':
            request.session['sale_order_id'] = None
            sale_order = request.website.sale_get_order(force_create=True)

        if product_custom_attribute_values:
            product_custom_attribute_values = json_scriptsafe.loads(product_custom_attribute_values)

        if no_variant_attribute_values:
            no_variant_attribute_values = json_scriptsafe.loads(no_variant_attribute_values)

        sale_order._cart_update(
            product_id=int(product_id),
            add_qty=add_qty,
            set_qty=set_qty,
            product_custom_attribute_values=product_custom_attribute_values,
            no_variant_attribute_values=no_variant_attribute_values,
            **kwargs
        )

        request.session['website_sale_cart_quantity'] = sale_order.cart_quantity

        if express:
            return request.redirect("/shop/checkout?express=1")

        return request.redirect("/shop/cart")

    @http.route('/process-data', auth='public', type='http', methods=['POST'], csrf=False)
    def my_method(self, **kw):
        try:
            raw_data = request.httprequest.data.decode('utf-8')
            _logger.info("Raw /process-data payload: %s", raw_data)

            payload = json.loads(raw_data or "{}")
            post_data = str(payload.get('value', '')).strip()

            if len(post_data) != 6 or not post_data.isdigit():
                data = {'message': 'Please enter 6 digit of your area pincode'}
                return request.make_response(
                    json.dumps(data),
                    headers=[('Content-Type', 'application/json')]
                )

            url1 = "https://sequel247.com/api/checkServiceability"
            data1 = {
                "token": "974a83c8c20e7ddb1e49f8abe4382299",
                "pin_code": post_data,
            }

            response1 = requests.post(url1, json=data1, timeout=20)
            _logger.info("checkServiceability status=%s body=%s", response1.status_code, response1.text)

            url2 = "https://sequel247.com/api/shipment/calculateEDD"
            data2 = {
                "origin_pincode": "110005",
                "destination_pincode": post_data,
                "pickup_date": date.today().strftime("%Y-%m-%d"),
                "token": "974a83c8c20e7ddb1e49f8abe4382299",
            }

            response2 = requests.post(url2, json=data2, timeout=20)
            _logger.info("calculateEDD status=%s body=%s", response2.status_code, response2.text)

            res1 = response1.json() if response1.text else {}
            res2 = response2.json() if response2.text else {}

            response_message = str(res1.get('message', 'Unable to check serviceability'))
            status_value = str(res1.get('status', '')).lower()

            edd_data = res2.get('data') or {}
            estimated_date = edd_data.get("estimated_delivery")
            estimated_day = edd_data.get("estimated_day")

            if status_value == 'false':
                message = response_message
            elif estimated_date and estimated_day:
                message = f"{response_message}. Expected Delivery On {estimated_date}, {estimated_day}"
            else:
                message = response_message

            data = {'message': message}
            return request.make_response(
                json.dumps(data),
                headers=[('Content-Type', 'application/json')]
            )

        except Exception as e:
            _logger.exception("Error in /process-data")
            data = {'message': f'Something went wrong while checking pincode: {str(e)}'}
            return request.make_response(
                json.dumps(data),
                headers=[('Content-Type', 'application/json')],
                status=500
            )

        
        