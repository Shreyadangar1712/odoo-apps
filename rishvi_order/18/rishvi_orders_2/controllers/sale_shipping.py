# -*- coding: utf-8 -*-
import logging

from odoo import http, _
from odoo.http import request
from odoo import models, api, exceptions, fields

import requests

_logger = logging.getLogger(__name__)


class Controller(http.Controller):

        @http.route('/fetch_postal_services', type='jsonrpc', auth='user', csrf=False)
        def fetch_postal_services(self, **kwargs):
            """
            Fetch postal services from Linnworks API (via configured base URL & token)
            and store them in 'sale.shipping.services' model.
            """
            _logger.info("Inside the Import Fetch Postal Services")
            try:
                # Step 1: Get config from system parameters
                ir_config = request.env["ir.config_parameter"].sudo()
                lw_token = ir_config.get_param("lw_token")
                rishvi_base_api_url = ir_config.get_param("rishvi_base_api_url")
                lw_customer_id = ir_config.get_param("lw_customer_id")
                rishvi_app = ir_config.get_param("rishvi_app")

                if not lw_token or not rishvi_base_api_url:
                    return {"success": False, "message": " Token or Base URL not configured in System Parameters."}
                

                # Step 2: Build full URL
                url = f"{rishvi_base_api_url}/Inventory/postal-services"

                # Step 3: Headers & params
                headers = {
                    "accept": "*/*"
                }
                params = {
                    "appName": rishvi_app,
                    "appToken": lw_token
                }

                # Step 4: Make GET request
                response = requests.get(url, headers=headers, params=params, timeout=10)
                response.raise_for_status()  # Raises exception for HTTP errors

                data = response.json()

                # Step 5: Clear old services (optional)
                request.env['sale.shipping.services'].sudo().search([]).unlink()

                # Step 6: Save new services
                for item in data:
                    country_code = item.get("countryCode")
                    vendor_name = item.get('vendorName')
                    vendor = request.env['res.partner'].sudo().search([('name', '=', vendor_name)], limit=1)
                    if not vendor and vendor_name:
                        vendor = request.env['res.partner'].sudo().create({'name': vendor_name})
                    # Try to find a matching country in Odoo
                    country = request.env['res.country'].sudo().search([
                        '|',
                        ('code', '=', country_code),
                        ('name', 'ilike', country_code)
                    ], limit=1)

                    # If not found, you can assign None or a default (like Worldwide country if you have one)
                    country_id = country.id if country else False
                    request.env['sale.shipping.services'].sudo().create({
                        'postal_service_name': item.get('postalServiceName') or "Unnamed Service",
                        'service_id': item.get('serviceId') or 0,
                        'vendor_id': vendor.id if vendor else False,
                        'amount': 0.0,
                        'active': True,
                        'service_country': country_id,
                    })

                # Step 7: Return saved services
                services = [
                    {
                        "id": service.id,
                        "service_id": service.service_id,
                        "name": service.postal_service_name,
                        "amount": service.amount,
                        "vendor_id": service.vendor_id,
                        "service_country": service.service_country,
                    }
                    for service in request.env['sale.shipping.services'].sudo().search([('active', '=', True)])
                ]

                return {"success": True, "data": services}

            except requests.exceptions.RequestException as e:
                _logger.error("Linnworks API request failed: %s", e)
                return {"success": False, "message": f"API request failed: {e}"}

            except Exception as e:
                _logger.exception(" Error fetching postal services: %s", e)
                return {"success": False, "message": str(e)}
