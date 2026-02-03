from odoo import models, fields, api
from odoo import http, _
from odoo.exceptions import UserError
from odoo.http import request
import logging
import base64
from io import BytesIO
import time
import requests


_logger = logging.getLogger(__name__)

class SyncControllerCron(models.Model):
    _name = 'sync.controller.cron'
    _description = 'Scheduled Action to Call Controller'
    
    enable_inventory_sync = fields.Boolean(
        string="Enable Inventory Sync Cron",
        help="Turn on to enable automatic on-hand inventory synchronization."
    )

    @api.model
    def cron_call_controller_sync_onhand_inventory(self):
        """Scheduled Action to call external Odoo controller."""
        if not self.enable_inventory_sync:
            _logger.info("🟡 Inventory sync cron is disabled in UI — skipping run.")
            return
        ir_config = self.env["ir.config_parameter"].sudo()
        lw_token = ir_config.get_param("lw_token")
        lw_customer_id = ir_config.get_param("lw_customer_id")
        rishvi_base_api_url = ir_config.get_param("rishvi_base_api_url")
        rishvi_app = ir_config.get_param("rishvi_app")
        
        url = f"{rishvi_base_api_url}/Inventory/inventory-count"
       
        params = {
            "appName": rishvi_app,
            "appToken": lw_token
        }

        headers = {"accept": "*/*"}
        try:
        # Make the GET request
           response = requests.get(url, headers=headers, params=params,timeout=10)
           if response.status_code==200:
                count_linn=int(response.json()['inventoryCount'])
                pages=int(count_linn/100)+1
                for page in range(1, pages + 1):
                     try:
                         self.sync_all_inventory(page)
                     except Exception as e:
                         _logger.error(f"Error syncing inventory  on page {page}: {str(e)}")
                         continue
                  
        
        except Exception as e:
            _logger.error(f"The issue has been ocuured while counting response")
            raise UserError(_("Failed to Adress Linnworks order: %s") % e)

    
    def sync_all_inventory(self, page):
        current_page = page
        start_time = time.time()

        try:
            # === Load configuration ===
            icp = request.env["ir.config_parameter"].sudo()
            lw_token = icp.get_param("lw_token")
            rishvi_base_api_url = icp.get_param("rishvi_base_api_url")
            rishvi_app = icp.get_param("rishvi_app")

            url = f"{rishvi_base_api_url}/Inventory/inventory"
            params = {"appName": rishvi_app, "appToken": lw_token, "page": current_page, "limit": 100}
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
            existing_pos_categories = {c.name: c for c in pos_category.search([])}
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
                        if not pos_category_obj:
                            vals = {'name': category_name}
                            pos_category_obj = pos_category.create(vals)
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
                            'pos_categ_ids': [(4, pos_category_obj.id)],
                            'is_storable':True,
                            'available_in_pos': True,
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


        


        
    