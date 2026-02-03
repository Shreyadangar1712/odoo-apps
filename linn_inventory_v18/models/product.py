from odoo import models, fields, api, exceptions ,_
import logging
from odoo.http import request
import requests
from odoo.exceptions import ValidationError
import base64
from io import BytesIO
from PIL import Image
import time

import requests
from datetime import datetime, timedelta, timezone

_logger = logging.getLogger(__name__)


class ProductCategory(models.Model):
    _inherit = 'product.category'

    linnworks_category_id = fields.Char(
        string='Linnworks Category ID',
        help='External Linnworks unique category identifier (UUID).'
    )


class ProductProduct(models.Model):
    _inherit = 'product.template'

    default_code = fields.Char(
        String='SKU', compute='_compute_default_code',
        inverse='_set_default_code', store=True)
    
    linn_description = fields.Html(
        string="Linnworks Description",
        sanitize=True,
        sanitize_tags=False,
        help="Description synced from Linnworks."
    )
    weight=fields.Float("Weight")
    length=fields.Float("Length")
    height=fields.Float("Height")




    linnworks_item_id = fields.Char()
    linnworks_location_id = fields.Char()
    linnworks_available_quantity = fields.Float(string="Linnworks Available Quantity" ,copy=False)
    
    barcode = fields.Char(
        string='Barcode',
        index=True,
        required=False,
        unique=False
    )
    
    
    image_url = fields.Char(string="Linn Image URL")
    # image_1920 = fields.Binary(
    #     string="Image",
    #     compute="_compute_image",
    #     store=True,
    #     attachment=False
    # )
       
    
    

    def update_for_linnwork_product(self):
        _logger.info(f"Product with Linworks Id {self.linnworks_item_id}")
        
        ir_config = request.env["ir.config_parameter"].sudo()
        lw_token = ir_config.get_param("lw_token")
        lw_customer_id = ir_config.get_param("lw_customer_id")
        rishvi_base_api_url = ir_config.get_param("rishvi_base_api_url")
        rishvi_app = ir_config.get_param("rishvi_app")
        
        url = f"{rishvi_base_api_url}/Inventory/inventory-item/{self.linnworks_item_id}"

        params = {
            "appName": rishvi_app,
            "appToken": lw_token
        }

        headers = {
            "accept": "*/*"
        }
        try:
            response = requests.get(url, headers=headers, params=params,timeout=10)
            response.raise_for_status()
            Product = request.env['product.product']
            StockQuant = request.env['stock.quant']
            sku = response.json()['sku']
            itemid = response.json()['linnworksId']
            name = response.json()['name']
            barcode = response.json()['barcode']
            image = response.json()['imageUrl']
            tax = 0.0
            category_id = response.json()['categoryId']
            category_name = response.json()['categoryName']
            retail_price = response.json()['price']
            description= response.json()['description']
            sku_levels=response.json()['stockLevels']
            extended_properties=response.json()['extendedProperties']

            try:
                if image:
                    try:
                        response = requests.get(image)
                        response.raise_for_status()
                        img_data = response.content
                        img_base64 = base64.b64encode(img_data).decode('utf-8')
                        image = img_base64
                    except requests.exceptions.RequestException as e:
                        _logger.error(f"Failed to download image for SKU {sku}: {e}")
                        image = None  # If there is an issue, set image to None
                
                productCategory = request.env['product.category']
                category = productCategory.search([('linnworks_category_id', '=', category_id)], limit=1)
                if not category:
                    if not category_id or not category_name:
                        category = productCategory.create({'name':'All'})
                    else:
                        category = productCategory.create({'linnworks_category_id': category_id,'name':category_name})
                product = Product.search([('linnworks_item_id', '=', itemid)], limit=1)
                
                if not product:
                    existing_barcode_product = Product.search([('barcode', '=', barcode)], limit=1) if barcode else None
                    create_vals = {'name': name,
                                   'default_code': sku,
                                   'type': 'consu',
                                   'is_storable': True,
                                   'categ_id': category.id if category else False,
                                   'image_1920': image,
                                   'list_price': retail_price,
                                   'barcode':barcode,
                                   'available_in_pos':True,
                                   'linn_description': description,
                                   'linnworks_item_id':itemid,}
                    if barcode and not existing_barcode_product:
                        create_vals['barcode'] = barcode
                    elif existing_barcode_product:
                        _logger.warning(f"Barcode {barcode} already exists for product (ID: {existing_barcode_product.id}). Skipping barcode assignment for new product with SKU {sku}.")
                        create_vals['barcode'] = ""
                    product = Product.create(create_vals)
                else:
                    product.write({'name': name,
                                   'default_code': sku,
                                   'type': 'consu',
                                   'is_storable': True,
                                   'available_in_pos': True,
                                   'categ_id': category.id if category else False,
                                   'image_1920': image,
                                   'barcode':barcode,
                                   'linn_description': description,
                                   'list_price': retail_price})
                #extented propertys
                if extended_properties and product:
                    product_property_obj = request.env['product.property']
                    existing_properties = product_property_obj.search([('product_id', '=', product.id)])
                    existing_keys = existing_properties.mapped('key')
                    for key,value in extended_properties.items():
                        key = key
                        value = value   
                        if key in existing_keys:
                            prop_record = existing_properties.filtered(lambda r: r.key == key)
                            prop_record.write({'value': value})
                        else:
                            product_property_obj.create({
                                'key': key,
                                'value': value,
                                'product_id': product.id,
                            })
 
                for level in sku_levels:
                    warehouse = request.env['stock.warehouse'].search([
                        "|",
                        ("linnexternal_id", "=", level['locationId']),
                        ("name", "=",level['warehouseName'])
                    ], limit=1)
                    
                    location = warehouse.lot_stock_id
                    if warehouse:
                        _logger.info(warehouse)
                        quant = request.env['stock.quant'].search([('product_id', '=', product.id),('location_id', '=', location.id)], limit=1)
                        if quant:
                            quant.sudo().write({'quantity': level['quantity']})
                           
                        else:
                            quant=request.env['stock.quant'].sudo().create({
                            'product_id': product.id,
                            'location_id': location.id,
                            'quantity': level['quantity'],
                            'company_id': request.env.company.id,
                            })                   
                    else:                      
                        vals = {
                            "name": level['warehouseName'],
                            "code": level['warehouseName'][:5].upper().replace(" ", ""),  # short code
                            "linnexternal_id": level['locationId'],
                        }
                        warehouse=request.env['stock.warehouse'].create(vals)
                        location = warehouse.lot_stock_id
                        request.env['stock.quant'].sudo().create({
                            'product_id': product.id,
                            'location_id': location.id,
                            'quantity': level['quantity'],
                            'company_id': request.env.company.id,
                            })
                return {
                            'type': 'ir.actions.client',
                            'tag': 'display_notification',
                            'params': {
                                'title': _('Success'),
                                'message': _("Congrats! Your product has been successfully synced."),
                                'type': 'success',
                                'sticky': False,
                                'next': {'type': 'ir.actions.client', 'tag': 'reload'},  # 👈 this reloads after notification
                            }
                        }


            except Exception as e:
                _logger.error(f"Syncing the product failed: {e}")
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Error'),
                        'message': _("Product Sync Failed! Please check your connection or try again."),
                        'type': 'danger',   # ❌ 'o_success' → 'danger' or 'warning'
                        'sticky': True,     # optional: keep the notification visible until closed
                    }
                }

        except Exception as e:
            _logger.error(f"Syncing the product failed: {e}")
            return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Error'),
                        'message': _("Product Sync Failed! Please check your connection or try again."),
                        'type': 'danger',   # ❌ 'o_success' → 'danger' or 'warning'
                        'sticky': True,     # optional: keep the notification visible until closed
                    }
                }