# -*- coding: utf-8 -*-
import logging
import odoo
from odoo import http, _
from odoo.exceptions import UserError
from odoo.http import request
import base64
from io import BytesIO
from PIL import Image
import time

import requests

_logger = logging.getLogger(__name__)

class LinnDashboardController(http.Controller):


    
    @http.route('/my/api/get_product_category_details', type='json', auth='user')
    def product_categories_details(self):

        ir_config = request.env["ir.config_parameter"].sudo()
        lw_token = ir_config.get_param("lw_token")
        lw_customer_id = ir_config.get_param("lw_customer_id")
        rishvi_base_api_url = ir_config.get_param("rishvi_base_api_url")
        rishvi_app = ir_config.get_param("rishvi_app")
        
        url = f"{rishvi_base_api_url}/Inventory/categories"
        params = {"appName": rishvi_app, "appToken": lw_token}

       
        

        headers = {
            "accept": "*/*"
        }
        
        try:
        # Make the GET request
            response = requests.get(url, headers=headers, params=params,timeout=5)
            if response.status_code==200:
                data=response.json()
                categories=data
                productCategory = request.env['product.category']
                for category in categories:
                    category_obj = productCategory.search([('linnworks_category_id', '=', category['categoryId'])],limit=1)
                    category_id=category['categoryId']
                    category_name=category['categoryName']
                    if not category_obj:
                        category_obj = productCategory.create({'linnworks_category_id': category_id,'name':category_name})
                return {'status': 'ok'}
        except Exception as e:
            _logger.error(f"The issue has been ocuured while counting response")
            raise UserError(_("Failed to Adress Linnworks order: %s") % e)
    

    @http.route('/my/api/get_inventory_count', type='json', auth='user')
    def get_inventory_count(self):
        count_rishvi = request.env['product.product'].search_count([])
        count_linn=0
        ir_config = request.env["ir.config_parameter"].sudo()
        lw_token = ir_config.get_param("lw_token")
        lw_customer_id = ir_config.get_param("lw_customer_id")
        rishvi_base_api_url = ir_config.get_param("rishvi_base_api_url")
        rishvi_app = ir_config.get_param("rishvi_app")
        
        url = f"{rishvi_base_api_url}/Inventory/inventory-count"
        params = {"appName": rishvi_app, "appToken": lw_token}

       

        headers = {
            "accept": "*/*"
        }
        try:
        # Make the GET request
            response = requests.get(url, headers=headers, params=params,timeout=10)
            if response.status_code==200:
                count_linn=int(response.json()['inventoryCount'])
            return {'count_rishvi': count_rishvi,'count_linn':count_linn}
        except Exception as e:
            _logger.error(f"The issue has been ocuured while counting response")
            raise UserError(_("Failed to Adress Linnworks order: %s") % e)

    

    @http.route('/my/api/sku_add', type='json', auth='user')
    def add_sku_item(self, **kwargs):
        _logger.info("Inside the Add Sku")
        sku=kwargs['sku']
        ir_config = request.env["ir.config_parameter"].sudo()
        lw_token = ir_config.get_param("lw_token")
        lw_customer_id = ir_config.get_param("lw_customer_id")
        rishvi_base_api_url = ir_config.get_param("rishvi_base_api_url")
        rishvi_app = ir_config.get_param("rishvi_app")

        url = f"{rishvi_base_api_url}/Inventory/inventory-item-by-sku/{sku}"
        params = {"appName": rishvi_app, "appToken": lw_token}



        headers = {
            "accept": "*/*"
        }
        try:
        # Make the GET request
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
                message=""
                if not product:
                    existing_barcode_product = Product.search([('barcode', '=', barcode)], limit=1) if barcode else None
                    create_vals = {'name': name,
                                   'default_code': sku,
                                   'type': 'consu',
                                   'is_storable': True,
                                   'available_in_pos': True,
                                   'categ_id': category.id if category else False,
                                   'image_1920': image,
                                   'list_price': retail_price,
                                   'barcode':barcode,
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
                                   'linn_description': description,
                                   'list_price': retail_price})
                    message="Updated"
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
                       
                return {'status': 'ok','name':name,'sku':sku}
            except Exception as e:
                _logger.error(f"Linnworks Address Udation Failed: {e}  response {response.json()}")
                raise UserError(_("Failed to Adress Linnworks order: %s") % e)
        except Exception as e:
            _logger.error(f"The issue has been ocuured while counting response {e}")
            raise UserError(_("Failed to Adress Linnworks order: %s") % e)
    

    @http.route('/my/api/linn_item_add', type='json', auth='user')
    def add_linn_item(self, **kwargs):
        # Example logic: find product by linn_id or take other action
        linnworks_id=kwargs['linn_id']
        ir_config = request.env["ir.config_parameter"].sudo()
        lw_token = ir_config.get_param("lw_token")
        lw_customer_id = ir_config.get_param("lw_customer_id")
        rishvi_base_api_url = ir_config.get_param("rishvi_base_api_url")
        rishvi_app = ir_config.get_param("rishvi_app")
        

        url = f"{rishvi_base_api_url}/Inventory/inventory-item/{linnworks_id}"
        params = {"appName": rishvi_app, "appToken": lw_token}


        headers = {
            "accept": "*/*"
        }
        try:
        # Make the GET request
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
                                   'available_in_pos': True,
                                   'categ_id': category.id if category else False,
                                   'image_1920': image,
                                   'list_price': retail_price,
                                   'barcode':barcode,
                                   'linn_description': description,
                                   'linnworks_item_id':itemid,}
                    if barcode and not existing_barcode_product:
                        create_vals['barcode'] = barcode
                    elif existing_barcode_product:
                        _logger.warning(f"Barcode {barcode} already exists for product (ID: {existing_barcode_product.id}). Skipping barcode assignment for new product with SKU {sku}.")
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
                       
                return {'status': 'ok','name':name,'sku':sku}
            except Exception as e:
                _logger.error(f"Linnworks Address Udation Failed: {e}  response {response.json()}")
                raise UserError(_("Failed to Adress Linnworks order: %s") % e)
        except Exception as e:
            _logger.error(f"The issue has been ocuured while counting response {e}")
            raise UserError(_("Failed to Adress Linnworks order: %s") % e)

    @http.route('/my/api/sync_all_inventory', type='json', auth='user')
    def sync_all_inventory(self, **kwargs):
        current_page = kwargs.get('i')
        start_time = time.time()

        try:
            # === Load configuration ===
            icp = request.env["ir.config_parameter"].sudo()
            lw_token = icp.get_param("lw_token")
            rishvi_base_api_url = icp.get_param("rishvi_base_api_url")
            rishvi_app = icp.get_param("rishvi_app")

            url = f"{rishvi_base_api_url}/Inventory/inventory"
            params = {"page": current_page, "limit": 30, "appName": rishvi_app, "appToken": lw_token}
            headers = {"accept": "*/*"}

            # === Retry logic ===
            MAX_RETRIES = 3
            for attempt in range(1, MAX_RETRIES + 1):
                try:
                    response = requests.post(url, headers=headers, params=params, timeout=10)
                    response.raise_for_status()
                    break
                except Exception as e:
                    if attempt < MAX_RETRIES:
                        time.sleep(3)
                    else:
                        raise UserError(_("Failed to fetch page %s after multiple retries: %s") % (current_page, e))

            if response.status_code != 200:
                raise UserError(_("Unexpected status code %s from API") % response.status_code)

            response_time = response.elapsed.total_seconds()
            product_data = response.json()

            # === Models (sudo where needed) ===
            Template = request.env['product.template'].sudo()
            Product = request.env['product.product'].sudo()
            Category = request.env['product.category'].sudo()
            pos_category = request.env['pos.category'].sudo()
            Warehouse = request.env['stock.warehouse'].sudo()
            StockQuant = request.env['stock.quant'].sudo()

            # === Cache data ===
            # Map linnworks_item_id (on template) -> (template, product_variant)
            tmpls = Template.search([])
            existing_templates = {t.linnworks_item_id: t for t in tmpls if t.linnworks_item_id}
            existing_variants_by_itemid = {t.linnworks_item_id: t for t in tmpls if t.linnworks_item_id}
            existing_categories = {c.linnworks_category_id: c for c in Category.search([])}
            existing_pos_categories = {(c.name).strip(): c for c in pos_category.search([])}
            existing_barcodes = set(Template.search([('barcode', '!=', False)]).mapped('barcode'))
           

            # Batch holders
            new_templates_vals = []
            rows_for_stock = []  # list of dicts: {'itemid':..., 'sku':..., 'levels':[...]}
            updated_count = 0

            # === Pass 1: upsert templates, collect stock rows ===
            for idx, prod in enumerate(product_data, start=1):
                with request.env.cr.savepoint():
                    try:
                        sku = prod.get('sku')
                        itemid = prod.get('linnworksId')
                        name = prod.get('name')
                        barcode = (prod.get('barcode') or '').strip()
                        category_id = prod.get('categoryId')
                        category_name = (prod.get('categoryName') or 'All').strip()
                        price = prod.get('price') or 0.0
                        description = prod.get('description') or ''
                        sku_levels = prod.get('stockLevels', []) or []
                        image_url = prod.get('imageUrl')


                        # Image
                        # image_b64 = False
                        # if image_url:
                        #     try:
                        #         resp = requests.get(image_url, timeout=5)
                        #         if resp.status_code == 200 and resp.content:
                        #             image_b64 = base64.b64encode(resp.content).decode()
                        #     except Exception as e:
                        #         _logger.warning("⚠️ Image download failed for SKU %s: %s", sku, e)

                        # Category
                        category = existing_categories.get(category_id)
                        if not category:
                            vals = {'name': category_name}
                            if category_id:
                                vals['linnworks_category_id'] = category_id
                            category = Category.create(vals)
                            existing_categories[category_id] = category

                        ###for pos category
                        pos_category_obj = existing_pos_categories.get(category_name) or False
                        if not bool(pos_category_obj):
                            vals = {'name': category_name}
                            pos_category_obj = pos_category.create(vals)
                            existing_pos_categories[category_name] = pos_category_obj

                        # Barcode rules
                        barcode_to_use = barcode
                        if barcode and barcode in existing_barcodes:
                          
                            barcode_to_use = ''
                        if barcode_to_use:
                            existing_barcodes.add(barcode_to_use)

                        tmpl_vals = {
                            'name': name,
                            'default_code': sku,
                            'type': 'consu',         # storable
                            'categ_id': category.id,
                            'is_storable':True,
                            'available_in_pos': True,
                            'pos_categ_ids': [(4, pos_category_obj.id)],
                            'list_price': price,
                            'barcode': barcode_to_use or False,
                            'image_url':image_url,
                            # 'image_1920': image_b64 or False,
                            'linn_description': description,
                            'linnworks_item_id': itemid,
                        }
                        tmpl = existing_templates.get(itemid)
                        if tmpl:
                            tmpl.write(tmpl_vals)
                            updated_count += 1
                           
                        else:
                            new_templates_vals.append(tmpl_vals)

                        # Collect stock rows (deal later, once variants exist)
                        if sku_levels:
                            rows_for_stock.append({'itemid': itemid, 'sku': sku, 'levels': sku_levels, 'category': category_name})
                    except Exception as e:
                        _logger.error("🚨 [Page %s] Template pass failed for SKU %s: %s", current_page, sku, e)
                        # savepoint prevents whole batch rollback; continue to next
                        continue

            # === Create new templates, build fresh variant map ===
            created_templates = Template.create(new_templates_vals) if new_templates_vals else Template.browse()

            # Merge caches
            for t in created_templates:
                existing_variants_by_itemid[t.linnworks_item_id] = t

            # === Pass 2: stock updates (inventory mode) ===
            def _ensure_warehouse(loc_id, wh_name):
                """Find or create a warehouse; return (warehouse, lot_stock_location)."""
                code_base = (wh_name[:5] or "").upper().replace(" ", "")
                code = code_base
                wh = Warehouse.search([
                    "|", ("linnexternal_id", "=", loc_id),
                        ("name", "=", wh_name)
                ], limit=1)
                if not wh:
                    wh = Warehouse.create({
                        "name": wh_name,
                        "code": code,
                        "linnexternal_id": loc_id,
                    })
                    _logger.info("🏭 Created new warehouse '%s' (loc_id=%s)", wh_name, loc_id)
                else:
                    _logger.info("📦 Using existing warehouse '%s' (ID %s)", wh_name, wh.id)
                return wh, wh.lot_stock_id

            inv_quant = StockQuant
            applied = 0
            for row in rows_for_stock:
                itemid = row['itemid']
                sku = row['sku']
                levels = row['levels']

                product_variant = existing_variants_by_itemid.get(itemid)
                if not product_variant:
                    _logger.error("🚫 No product variant resolved for SKU %s (itemid=%s); skipping stock rows", sku, itemid)
                    continue

                for level in levels:
                    with request.env.cr.savepoint():
                        try:
                            loc_id = level.get("locationId")
                            qty = level.get("quantity", 0)
                            wh_name = (level.get("warehouseName") or "Default").strip()

                            warehouse, location = _ensure_warehouse(loc_id, wh_name)
                           

                            # Find/create quant in inventory mode; set absolute qty
                            quant = inv_quant.search([
                                ("product_id", "=", product_variant.id),
                                ("location_id", "=", location.id),
                            ], limit=1)
                            if quant:
                                quant.write({'quantity': qty})
                                quant.action_apply_inventory()
                            else:
                                quant = inv_quant.create({
                                    "product_id": product_variant.id,
                                    "location_id": location.id,
                                    "inventory_quantity": qty,
                                    "company_id": request.env.company.id,
                                })
                                quant.action_apply_inventory()

                            applied += 1
                            _logger.info("✅ Set on-hand for %s @ %s to %s", sku, wh_name, qty)
                        except Exception as e:
                            _logger.error("❌ Inventory apply failed for %s @ %s: %s", sku, wh_name, e)
                            continue  # savepoint keeps going

            total_time = round(time.time() - start_time, 2)
            _logger.info(
                "✅ [Inventory Sync] Page %s done in %.2fs — updated %d templates, created %d templates, applied %d stock rows",
                current_page, total_time, updated_count, len(created_templates), applied
            )
            return {'status': 'ok', 'time': total_time, 'updated_templates': updated_count,
                    'created_templates': len(created_templates), 'stock_updates': applied}

        except Exception as e:
            _logger.exception("💥 [Inventory Sync] Fatal error on page %s: %s", current_page, e)
            request.env.cr.rollback()
            raise UserError(_("Inventory sync failed for page %s: %s") % (current_page, e))


        


        
    @http.route('/my/api/get_warehouse_details', type='json', auth='user')
    def get_warehouse_details(self):
        
        ir_config = request.env["ir.config_parameter"].sudo()
        lw_token = ir_config.get_param("lw_token")
        lw_customer_id = ir_config.get_param("lw_customer_id")
        rishvi_base_api_url = ir_config.get_param("rishvi_base_api_url")
        rishvi_app = ir_config.get_param("rishvi_app")

        

        url = f'{rishvi_base_api_url}/Inventory/warehouses'
        params = {"appName": rishvi_app, "appToken": lw_token}



        headers = {
            "accept": "application/json",
            "content-type": "application/json"
        }

        try:
            print("➡️ Sending GET request to Linnworks Warehouse API...")
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            linn_warehouse_list=response.json()
            if not isinstance(linn_warehouse_list, list):
                return {"error": "Invalid API response format"}

            Warehouse = request.env["stock.warehouse"].sudo()
            created, updated = [], []

            for wh in linn_warehouse_list:
                linnexternal_id = wh.get("stockLocationId")
                name = wh.get("locationName") or "Unnamed"
                is_fulfillment = wh.get("isFulfillmentCenter", False)
                available = wh.get("available", False)

                # Look for an existing record
                existing = Warehouse.search([
                    "|",
                    ("linnexternal_id", "=", linnexternal_id),
                    ("name", "=", name)
                ], limit=1)

                vals = {
                    "name": name,
                    "code": name[:5].upper().replace(" ", ""),  # short code
                    "linnexternal_id": linnexternal_id,
                    "linn_is_fulfillment": is_fulfillment,
                    "linn_available": available,
                }
                if existing:
                    existing.write(vals)
                    updated.append(name)
                else:
                    Warehouse.create(vals)
                    created.append(name)
            return {
                "status": "success",
                "created": created,
                "updated": updated,
                "total_synced": len(linn_warehouse_list),
            }
        except Exception as e:
            _logger.error(f"Linnworks Address Udation Failed: {e}  response {response.json()}")
            raise UserError(_("Failed to Adress Linnworks order: %s") % e)
        
        
