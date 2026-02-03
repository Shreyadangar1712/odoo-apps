/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useEffect } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks"; 
import { rpc } from "@web/core/network/rpc";

class LinnDashboard extends Component {
  setup() {
        this.skuValue = "";
        this.inventoryCountLinn = 0;
        this.inventoryCountRishvi = 0;
        this.barcodeValue = "";
        this.linnIdValue = "";
        this.syncProgress = 0;      // percentage
        this.syncing = false;
        this.warehouseDetails = [];
        this.accpectedTime = 0;
        this.pagesCount = 0;
        this.currentPageSyncing = 1;
        this.loadInventoryCount();

  }


    async toggleInventorySync(ev) {
      const enabled = ev.target.checked;
      
      try {
            console.log(enabled)
            await rpc("/inventory/sync/toggle", { enable: enabled });
            this.env.services.notification.add(
                enabled ? "Inventory Sync Enabled ✅" : "Inventory Sync Disabled ❌",
                { type: "success" }
            );
      } catch (error) {
            console.log(error)
            this.env.services.notification.add("Error updating sync setting", { type: "danger" });
        }
    }
    async loadInventoryCount() {
        try {
            // Make your RPC call
            const response_inventory_count = await rpc("/my/api/get_inventory_count", {});
            const inventory_count = response_inventory_count.count_linn || 0;
            const pagesCount = Math.floor(inventory_count / 30) + 1;

            console.log(`📦 Total Pages Count: ${pagesCount}`);
            // Optionally store in the component state if needed
          this.pagesCount = pagesCount;
          this.render()
          return
        } catch (error) {
            //console.error("❌ Failed to load inventory count:", error);
            this.env.services.notification.add(
                "Failed to load inventory count. Please try again.",
                { type: "danger", sticky: true }
            );
        }
    }    

    async getAllInventory() {
        try {
            this.env.services.notification.add("We are Counting your product relax and have a cup coffee.", { type: "warning" });
            async function callWithRetry(url, params = {}, maxRetries = 3, delayMs = 1000) {
                for (let attempt = 1; attempt <= maxRetries; attempt++) {
                  try {
                    const response = await rpc(url, params);  // your Odoo RPC call
                    if (response) return response;            // success → exit loop
                  } catch (err) {
                    //console.warn(`Attempt ${attempt} failed:`, err);
                    if (attempt < maxRetries) {
                     // console.log(`Retrying in ${delayMs / 1000}s...`);
                      await new Promise(r => setTimeout(r, delayMs));  // wait before retry
                    } else {
                    //console.error("All retry attempts failed.");
                    this.env.services.notification.add(
                        "Sorry! Please try again after some time.",
                        {
                          type: "warning",
                          sticky: true, // ✅ makes the notification stay visible until dismissed
                        }
                      );
                    }
                  }
                }
              }
            const response = await callWithRetry("/my/api/get_inventory_count", { }, 3, 1000);
            this.inventoryCountLinn = response.count_rishvi || 0;
            this.inventoryCountRishvi = response.count_linn || 0;
            // Force UI refresh (because plain vars are NOT reactive)
            this.render();
        } catch (error) {
           // console.error("Error fetching inventory:", error);
        }
    }

    async addBySku() {
        const sku = document.getElementById("linnIdInputSku").value;
        console.log("Current SKU:", sku);

        if (!sku) {
            this.env.services.notification.add("Please enter a SKU value.", { type: "warning" });
            return;
        }

        try {
          //  console.log("Sending SKU via RPC:", sku);

            // ✅ Correct Odoo RPC usage
            const response = await rpc("/my/api/sku_add", { sku });

            console.log("RPC Response:", response);
            this.env.services.notification.add(`SKU ${sku} added successfully!`, { type: "success" });

            if (response?.message) {
               // console.log("Backend message:", response.message);
            }

        } catch (error) {
            console.error("RPC Error:", error);
            this.env.services.notification.add("Failed to add SKU.", { type: "danger" });
        }
    }

    
    // ✅ New Barcode RPC
    async addByBarcode() {
        const barcode = this.barcodeValue;
        //console.log("Current Barcode:", barcode);

        if (!barcode) {
            this.env.services.notification.add("Please enter a Barcode value.", { type: "warning" });
            return;
        }

        try {
            console.log("Sending Barcode via RPC:", barcode);
            // 🔹 Call backend endpoint for barcodes
            const response = await rpc("/my/api/barcode_add", { barcode });

            //console.log("RPC Response:", response);
            this.env.services.notification.add(`Barcode ${barcode} added successfully!`, { type: "success" });

            if (response?.message) {
                //console.log("Backend message:", response.message);
            }
        } catch (error) {
            //console.error("RPC Error:", error);
            this.env.services.notification.add("Failed to add Barcode.", { type: "danger" });
        }
    }

    

    /** ✅ Add by Linn Item ID **/
    async addByLinnId() {
        const linn_id = document.getElementById("linnIdInput").value;
        //console.log("Current Linn Item ID:", linn_id);

        if (!linn_id) {
            this.env.services.notification.add("Please enter a Linn Item ID.", { type: "warning" });
            return;
        }

        try {
            // console.log("Sending Linn Item ID via RPC:", linn_id);
            const response = await rpc("/my/api/linn_item_add", { linn_id });

            console.log("RPC Response:", response);
            const sku=response.sku
            const product_name = response.name
            this.env.services.notification.add(
                `Linn Item ID ${linn_id} (${sku} - ${product_name}) added successfully!`,
                { type: "success", sticky: true, }
              );

            if (response?.message) {
                // console.log("Backend message:", response.message);
            }
        } catch (error) {
            console.error("RPC Error:", error);
            this.env.services.notification.add("Failed to add Linn Item ID.", { type: "danger",sticky: true, });
        }
    }

    


    async syncAllInventory() {
        if (this.syncing) {
            this.env.services.notification.add("Sync already in progress.", { type: "warning" });
            return;
      }
      if (this.pagesCount ===0) {
          this.env.services.notification.add("Please Reload the page.", { type: "warning" });
          return;
      }
      const start = Number(document.getElementById('startPage').value);
      const end = Number(document.getElementById('endPage').value);

      if (end < start) {
          this.env.services.notification.add("End page must be greater than start page.", { type: "warning" });
          return;
      }
      if (!start || !end) {
        this.env.services.notification.add("Please select both Start Page and End Page.", { type: "warning" });
        return;
      }
      if (start === 0 || end === 0) {
        this.env.services.notification.add("Start Page and End Page must be greater than zero.", { type: "warning" });
        return;
      }
      
      this.syncProgress = 0;
      this.syncing = true;
        this.render();

        try {
          this.env.services.notification.add("We’re syncing your products — please wait and relax with a cup of coffee.", { type: "warning", sticky: true });

          let currentPageCount=1
          for (let i = start; i <= end; i += 1) {
            // console.log(type(i))
            // continue
            if (end < start) {
              this.env.services.notification.add("End page must be greater than start page.", { type: "warning" });
                  return;
            } 
            try {
              this.currentPageSyncing = i
              this.render()
              const response = await rpc("/my/api/sync_all_inventory", { i });
              var responseTime = response.time;
                
              let totalpages=(end -start) +1
              var leftPagesCount = totalpages - currentPageCount;
              // console.log(`Sync Complete for page ${i} Response Time is ${response.time}`);
                
              this.syncProgress = Math.floor((currentPageCount * 100) / totalpages);
              // this.syncProgress = 50;
              
             
              // console.log(`Sync Progresss ${this.syncProgress} and left pages ${leftPagesCount}`);
              this.accpectedTime = Math.floor(responseTime * leftPagesCount);
              currentPageCount +=1
              this.render();
              await new Promise(r => setTimeout(r, 1000)); // wait 1 second
            }
            catch (error)
            {
              continue;
            }
            
            }

            this.env.services.notification.add("Inventory sync completed!", { type: "success", sticky: true, });
        } catch (error) {
            console.error("RPC Error:", error);
            this.env.services.notification.add("Failed to sync inventory.", { type: "danger", sticky: true, });
        } finally {
            this.syncing = false;
            this.render();
        }
    }

    async getWarehouseDetails() {
        try {
            async function callWithRetry(url, params = {}, maxRetries = 3, delayMs = 1000) {
                for (let attempt = 1; attempt <= maxRetries; attempt++) {
                  try {
                    const response = await rpc(url, params);  // your Odoo RPC call
                    if (response) return response;            // success → exit loop
                  } catch (err) {
                    console.warn(`Attempt ${attempt} failed:`, err);
                    if (attempt < maxRetries) {
                      console.log(`Retrying in ${delayMs / 1000}s...`);
                      await new Promise(r => setTimeout(r, delayMs)); 
                    } else {
                        console.error("All retry attempts failed.");
                        this.env.services.notification.add(
                            "Sorry! Please try again after some time.",
                            {
                              type: "warning",
                              sticky: true, 
                            }
                          );
                          
                    }
                  }
                }
              }
            const response = await callWithRetry("/my/api/get_warehouse_details", {}, 3, 1000);
            this.warehouseDetails = response.warehouses || [];
            this.env.services.notification.add("Warehouse details fetched!", { type: "success", sticky: true, });
        } catch (error) {
            console.error("Error fetching warehouse details:", error);
            this.env.services.notification.add("Failed to load warehouse details.", { type: "danger", sticky: true, });
        }
    }
  
    async getProductCaregories() {
      try {
          async function callWithRetry(url, params = {}, maxRetries = 3, delayMs = 1000) {
              for (let attempt = 1; attempt <= maxRetries; attempt++) {
                try {
                  const response = await rpc(url, params);  // your Odoo RPC call
                  if (response) return response;            // success → exit loop
                } catch (err) {
                  console.warn(`Attempt ${attempt} failed:`, err);
                  if (attempt < maxRetries) {
                    console.log(`Retrying in ${delayMs / 1000}s...`);
                    await new Promise(r => setTimeout(r, delayMs));  // wait before retry
                  } else {
                      console.error("All retry attempts failed.");
                      this.env.services.notification.add(
                          "Sorry! Please try again after some time.",
                          {
                            type: "warning",
                            sticky: true, // ✅ makes the notification stay visible until dismissed
                          }
                        );
                        
                  }
                }
              }
            }
          const response = await callWithRetry("/my/api/get_product_category_details", {}, 3, 1000);
          this.env.services.notification.add("Product Categories details fetched!", { type: "success", sticky: true, });
      } catch (error) {
          console.error("Error fetching Product Categories:", error);
          this.env.services.notification.add("Failed to load Product Categories.", { type: "danger", sticky: true, });
      }
  }
    
}

LinnDashboard.template = "linn_inventory.LinnDashboardTemplate";

registry.category("actions").add("product_syncer_dashboard", LinnDashboard);
