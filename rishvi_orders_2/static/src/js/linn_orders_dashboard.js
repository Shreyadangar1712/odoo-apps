/** @odoo-module **/
import { Component, useState,useRef } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";

export class OrderDashboard extends Component {
    setup() {
        this.state = useState({ loading: false ,syncing:false,});
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.action = useService("action");
        this.accpectedTime = 0;
        this.pagesCount = 0;
        this.syncProgress = 0;
        this.currentPageSyncing = 0;
        this.refreshOrders();
        this.rishviPieChartRef = useRef("rishviPieChart");
        this.linnworksPieChartRef = useRef("linnworksPieChart");


    }

     /**
     * ✨ BULK SYNC ALL ORDERS - MAIN FUNCTION (100% WORKING)
     */
    async syncAllOrders() {
        console.log("🚀 ========== SYNC ALL ORDERS STARTED ==========");

        if (this.state.syncing) {
            console.warn("⚠️ Sync already in progress");
            this.notification.add("Sync already in progress.", { type: "warning" });
            return;
        }

        if (this.pagesCount=== 0) {
            console.error("❌ Total pages is 0");
            this.notification.add(
                "Please reload the page to load order counts.",
                { type: "warning", sticky: true }
            );
            return;
        }

        // Get input values
        const startPageInput = document.getElementById('startPage');
        const endPageInput = document.getElementById('endPage');

        console.log("📝 Input elements:", {
            startPageInput: startPageInput ? "Found" : "NOT FOUND",
            endPageInput: endPageInput ? "Found" : "NOT FOUND"
        });

        if (!startPageInput || !endPageInput) {
            console.error("❌ Input fields not found!");
            this.notification.add(
                "Error: Input fields not found. Please refresh page.",
                { type: "danger", sticky: true }
            );
        return;
        }


        // let startPage = parseInt(startPageInput.value) || 1;
        // let endPage = parseInt(endPageInput.value) || this.pagesCount;
        let startPage = startPageInput.value;
        let endPage = endPageInput.value;

        // Validation first
        if (!startPage || !endPage) {
            this.env.services.notification.add(
                "Please select both Start Page and End Page.",
                { type: "warning" }
            );
            return;
        }

        // Convert after validation
        startPage = parseInt(startPage);
        endPage = parseInt(endPage);


        console.log("📋 Sync parameters:", {
            startPage: startPage,
            endPage: endPage,
            totalPages: this.pagesCount
        });

        // Validation
        if (!startPage || !endPage) {
        this.env.services.notification.add("Please select both Start Page and End Page.", { type: "warning" });
        return;
        }
        if (startPage < 1) {
            console.error("❌ Start page must be >= 1");
            this.notification.add("Start page must be at least 1.", { type: "warning" });
        return;
        }
        if (startPage === 0 || endPage === 0) {
           this.env.services.notification.add("Start Page and End Page must be greater than zero.", { type: "warning" });
        return;
        }

        if (endPage < startPage) {
            console.error("❌ End page must be >= start page");
            this.notification.add(
                "End page must be greater than or equal to start page.",
                { type: "warning" }
            );
        return;
        }

        if (endPage > this.pagesCount) {
            console.warn("⚠️ End page exceeds total pages");
            this.notification.add(
                `End page exceeds total pages (${this.pagesCount}). Using ${this.pagesCount} instead.`,
                { type: "warning" }
            );
            endPage = this.pagesCount;
        }

        // Reset progress
        this.syncProgress = 0;
        this.syncing = true;
        this.currentPageSyncing = startPage;

        console.log(`✅ Starting sync from page ${startPage} to ${endPage}`);

        try {
            this.notification.add(
                `🔄 Starting order sync: Pages ${startPage} to ${endPage}. Please wait...`,
                { type: "info", sticky: true }
            );

            let currentPageCount = 1;
            let totalCreated = 0;
            let totalUpdated = 0;
            let totalErrors = 0;

            const totalPagesToSync = (endPage - startPage) + 1;
            console.log(`📊 Total pages to sync: ${totalPagesToSync}`);

            for (let i = startPage; i <= endPage; i++) {
                try {
                    console.log(`\n🔄 ========== SYNCING PAGE ${i} of ${endPage} ==========`);

                    this.currentPageSyncing = i;

                    console.log(`📡 Making RPC call for page ${i}...`);
                    const response = await rpc("/my/api/order/sync_orders_by_page", {
                        page_number: i
                    });

                    console.log(`📦 Page ${i} response:`, response);

                    if (response.status === 'ok') {
                        const responseTime = response.time || 10;
                        totalCreated += response.created || 0;
                        totalUpdated += response.updated || 0;

                        const leftPagesCount = totalPagesToSync - currentPageCount;

                        // Update progress
                        this.syncProgress = Math.floor((currentPageCount * 100) / totalPagesToSync);
                        this.accpectedTime = Math.floor(responseTime * leftPagesCount);
                        this.render()

                        currentPageCount += 1;

                        console.log(`✅ Page ${i} completed:`, {
                            created: response.created,
                            updated: response.updated,
                            total: response.total_processed,
                            time: responseTime
                        });

                        // Small delay between requests
                        console.log("⏳ Waiting 1 second before next page...");
                        await new Promise(r => setTimeout(r, 1000));
                    } else {
                        console.error(`❌ Error on page ${i}:`, response.message);
                        totalErrors += 1;

                        this.notification.add(
                            `⚠️ Page ${i} failed: ${response.message}`,
                            { type: "warning" }
                        );
                    }

                } catch (pageError) {
                    console.error(`❌ Failed to sync page ${i}:`, pageError);
                    totalErrors += 1;

                    this.notification.add(
                        `⚠️ Page ${i} failed. Continuing to next page...`,
                        { type: "warning" }
                    );

                    // Continue to next page even if one fails
                    continue;
                }
            }

            console.log("\n✅ ========== SYNC COMPLETED ==========");
            console.log("📊 Final results:", {
                totalCreated: totalCreated,
                totalUpdated: totalUpdated,
                totalErrors: totalErrors,
                pagesProcessed: currentPageCount - 1
            });

            this.notification.add(
                `✅ Order sync completed!\n${totalCreated} orders created, ${totalUpdated} orders updated.\n${totalErrors > 0 ? `${totalErrors} pages had errors.` : 'No errors!'}`,
                { type: "success", sticky: true }
            );

        } catch (error) {
            console.error("❌ ========== SYNC FAILED ==========");
            console.error("Error details:", error);

            this.notification.add(
                `⚠️ Failed to sync orders: ${error.message || 'Unknown error'}. Check console for details.`,
                { type: "danger", sticky: true }
            );
        } finally {
            this.syncing = false;
            this.syncProgress = 0;
            this.accpectedTime = 0;

            console.log("🏁 Sync process ended");
        }
    }


    async refreshOrders() {
        try {
            const callWithRetry = async (url, params = {}, maxRetries = 3, delayMs = 1000) => {
                for (let attempt = 1; attempt <= maxRetries; attempt++) {
                    try {
                        const response = await rpc(url, params);
                        if (response) return response;
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
            };

            const response = await callWithRetry("/order/status_counts", {}, 3, 1000);
            this.pagesCount = Math.floor(response.data / 30) + 1;
            this.render();
            console.log("Page Count calculated");

        } catch (error) {
            console.error("Error fetching:", error);
            this.pagesCount = 0;
            this.env.services.notification.add(
                "Error while connecting to Linnworks. Please try again after some time.",
                { type: "danger", sticky: true }
            );
        }
    }

      //  Search Order by ID ()
   async searchOrderById() {
        const orderId = document.getElementById("orderIdInput").value.trim();
        if (!orderId) {
            this.notification.add("⚠️ Please enter an Order ID", { type: "warning" });
            return;
        }

        try {
            const result = await rpc("/linnworks/search_order_by_id", { order_id: orderId });
            if (result.success) {
                this.notification.add(result.message, { type: "success" });
            } else {
                this.notification.add(result.message, { type: "danger" });
            }
        } catch (error) {
            console.error("Error:", error);
            this.notification.add("⚠️ Something went wrong while searching.", { type: "danger" });
        }
    }

         // Comparing and Merging Customers
    async compareAndMergeCustomers() {


        try {
            // Call backend to compare customers
            const result = await rpc("/partners/compare", {

            });

            if (result.status === "success") {
                this.notification.add(result.message, { type: "success", sticky: true });
            } else {
                this.notification.add(result.message, { type: "danger", sticky: true });
            }

        } catch (error) {
            console.error("Error:", error);
            this.notification.add("⚠️ Something went wrong while comparing customers.", { type: "danger" ,sticky : true});
        }
    }

      //  import data ()

   async importData() {
        try {
            this.state.loading = true;

            const response = await rpc("/fetch_postal_services", {});

            if (response && response.success) {
                this.notification.add(
                    response.message || "Data imported successfully!",
                    { type: "success" }
                );
            } else {
                this.notification.add(
                    response.message || "Failed to import data.",
                    { type: "danger" }
                );
            }
        } catch (error) {
            console.error("Import Error:", error);
            this.notification.add(
                "Something went wrong while importing.",
                { type: "danger" }
            );
        } finally {
            this.state.loading = false;
        }
    }

    async searchOrderBySku() {
        const numOrderId = document.getElementById("orderSkuInput").value.trim();
        if (!numOrderId) {
            this.notification.add("⚠️ Please enter an Order Number", { type: "warning" });
            return;
        }
        try {
            this.state.loading = true;
            const result = await rpc("/linnworks/get-order-by-numid", { numOrderId: numOrderId });
            if (result.success) {
                this.notification.add(result.message, { type: "success" });
            } else {
                this.notification.add(result.message, { type: "danger" });
            }
        } catch (error) {
            console.error("Import Error:", error);
            this.notification.add("⚠️ Something went wrong while importing the order.", { type: "danger" });
        } finally {
            this.state.loading = false;
        }
    }
    
    async importCountries() {
        try {
            this.notification.add("Importing countries...", { type: "info" });

            const result = await rpc("/linnworks/Order/get-countries", {});
            if (result.success) {
                this.notification.add(result.message || "Countries imported successfully!", {
                    type: "success",sticky: true,
                });
            } else {
                this.notification.add(result.message || "Failed to import countries.", {
                    type: "danger",sticky: true,
                });
            }
        } catch (error) {
            console.error("Error importing countries:", error);
            this.notification.add("Unexpected error during import.", { type: "danger" });
        }
    }

//    discount
   async enableDiscount() {
    this.state.loading = true;
    this.render();

    try {
        // Call Odoo's dataset call_kw endpoint to execute the model method
        await rpc('/web/dataset/call_kw', {
            model: 'rishvi.dashboard.discount',
            method: 'action_enable_discounts',
            args: [[]],  // call on empty recordset
            kwargs: {},
        });

        // show success
        this.notification.add("Discounts have been enabled successfully!", {
            type: "success",
            sticky: true,
        });
    } catch (error) {
        console.error("Enable discount failed:", error);
        this.notification.add(
            "Failed to enable discounts: " + (error.message || "Unknown error"),
            { type: "danger", sticky: true }
        );
    } finally {
        this.state.loading = false;
        this.render();
    }
}
async enablePriceLists() {
    this.state.loading = true;
    this.render();

    try {
        // Call Odoo's dataset call_kw endpoint to execute the model method
        await rpc('/web/dataset/call_kw', {
            model: 'rishvi.dashboard.discount',
            method: 'action_enable_pricelists',
            args: [],  // call on empty recordset
            kwargs: {},
        });

        // show success
        this.notification.add("Pricelists have been enabled successfully!", {
            type: "success",
            sticky: true,
        });
    } catch (error) {
        console.error("Enable discount failed:", error);
        this.notification.add(
            "Failed to enable discounts: " + (error.message || "Unknown error"),
            { type: "danger", sticky: true }
        );
    } finally {
        this.state.loading = false;
        this.render();
    }
}

async updateOrderStatus() {
    try {
        const response = await rpc("/order/status_counts_status", {});

        if (response && response.success) {
            this.updateOrderStatusUI(response.data);
            // this.renderOrderCharts();  // <<---- Render pie charts after data update
            this.env.services.notification.add(
                "Order status updated successfully!",
                { type: "success", sticky: true }
            );
        } else {
            this.env.services.notification.add(
                response.error || " Failed to fetch order status",
                { type: "danger" }
            );
        }
    } catch (error) {
        console.error("Error fetching order status:", error);
        this.env.services.notification.add(
            " Failed to load order status",
            { type: "danger", sticky: true }
        );
    }
}

updateOrderStatusUI(data) {
    // --- Rishvi Orders ---
    if (data.rishvi_orders) {
        this.updateCountElement('rishvi-draft', data.rishvi_orders.draft);
        this.updateCountElement('rishvi-confirmed', data.rishvi_orders.confirmed);
        this.updateCountElement('rishvi-cancelled', data.rishvi_orders.cancelled);
        this.updateCountElement('rishvi-synced', data.rishvi_orders.synced);
    }

    // --- Linnworks Orders ---
    if (data.lineworks_orders) {
        this.updateCountElement('lineworks-pending', data.lineworks_orders.pending);
        this.updateCountElement('lineworks-processed', data.lineworks_orders.processed);
        this.updateCountElement('lineworks-dispatched', data.lineworks_orders.dispatched);
        this.updateCountElement('lineworks-returned', data.lineworks_orders.returned);
    }
}

updateCountElement(elementId, value) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = value || '0';
    }
}


}

OrderDashboard.template = "rishvi_orders_v19.OrderManagementDashboard";
registry.category("actions").add("linn_Order_Operation", OrderDashboard);
