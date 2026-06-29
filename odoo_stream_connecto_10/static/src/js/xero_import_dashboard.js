/** @odoo-module **/
import { Component, useState,useRef } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";
import { onWillStart } from "@odoo/owl";
import { session } from "@web/session";
import { Many2XAutocomplete } from "@web/views/fields/relational_utils";



export class OrderDashboard extends Component {
 

    static template = "your_module.XeroDashboard";

    static components = {
        Many2XAutocomplete,
    };

    setup() {
        console.log("SESSION:", JSON.stringify(session));
    this.state = useState({ loading: false, syncing:false, activeCategory: "accounting",
        inventoryTracking: false,
        showCustomerAutomationPopup: false,
        showlogsAutumationPopup:false,
        showAutomationTypePopup: false,
        showAutomationPopup: false,
        autoUpdateInvoices: false,
        nextExecutionTime: null,
        autoSyncInvoices: false ,
        autoUpdateInvoiceWeekly:false, 
        autoUpdateInvoiceMonthly:false,
        autoSyncInvoicesWeekly:false,
        autoSyncCustomerInvoices:false,
        autoSyncInvoicesMonthly:false,
        nextExecutionTimeWeekly: null,
        nextExecutionTimeMonthly: null,
        autoUpdateCustomerInvoices:false,
        nextExecutionTimeCustomerDaily : null,
        nextExecutionTimeCustomerWeekly:null,
        autoSyncCustomerInvoicesWeekly:false,
        autoUpdateCustomerInvoicesWeekly:false,
        nextExecutionTimeCustomerMonthly:null,
        nextExecutionTimeofLogs:null,
        autoUpdateCustomerInvoicesMonthly:null,
        autoSyncCustomerInvoicesMonthly:null,
        nextExecutionTimeofAuthentication:null,
        nextExecutionTimeofPoExport:null,
        nextExecutionTimeofInvoiceExport:null,
        nextExecutionTimeofPaymentsImport:null,
        nextExecutionTimeofInvoicesImport:null,
        nextExecutionTimeofManualJournalsImport:null,
        nextExecutionTimeofPoImport:null,
        nextExecutionTimeofSoImport:null,
        nextExecutionTimeofPaymentExport:null,
        autoImportManualJournals:false,
        autoImportManualJournalsSync:false,
        autoAuthenticateSync:false,
        autoAuthenticate:false,
        autoExportPo:false,
        syncExportPo:false,
        autoExportInvoices:false,
        autoInvoicesExportSync:false,
        autoImportPayments:false,
        syncImportPayments:false,
        autoImportInvoices:false,
        autoImportInvoicesSync:false,
        autoImportPo:false,
        autoImportPoSync:false,
        autoCleanlogs:false,
        autoSyncCLearLogs:null,
        autoImportSo:false,
        autoExportPayments:false,
        autoExportPaymentsSync:false,
        autoImportSoSync:false,
        autoAuthenticate:false,
        xero_client_id: '',
    xero_client_secret: '',
    xero_redirect_url: '',
    xeroConnected: false,

    
    });
   
    this.orm = useService("orm");
    this.notification = useService("notification");
    this.xero_client_id     = useRef('xero_client_id');
this.xero_client_secret = useRef('xero_client_secret');
this.xero_redirect_url = useRef('xero_redirect_url');

this.state = useState({
            default_account_value: "",
            default_account_selection: [],

            manual_journal_value: "",
            manual_journal_selection: [],

            overpayment_journal_value: "",
            overpayment_journal_selection: [],

            prepayment_journal_value: "",
            prepayment_journal_selection: [],

            skip_payment_journal_value: "",
            skip_payment_journal_selection: [],

            default_prod_po_value: "",
            default_prod_po_selection: [],

            default_prod_so_value: "",
            default_prod_so_selection: [],
        });

console.log(" SESSION:", session);

this.companyId =
    session.user_context?.allowed_company_ids?.[0] ||
    session.user_companies?.current_company ||
    1;

console.log("🏢 COMPANY ID:", this.companyId);

    console.log("🏢 COMPANY ID:", this.companyId);
   
    onWillStart(async () => {
        await this.loadCompanyData();
    });
    
    this.action = useService("action");

    this.ui = useService("ui");

    onWillStart(async () => {
        await this.loadInventoryTracking();  
    });
    onWillStart(async () => {
        await this.loadXeroStatus();
    });

    this.toggleInventoryTracking = this.toggleInventoryTracking.bind(this);
   






    // Bind methods
    this.saleorderDateRef = useRef("saleorder_date");
    this.lastSoPageRef = useRef("last_so_page");
    this.purchaseorder_date = useRef("purchaseorder_date");
    this.last_po_page = useRef("last_po_page");
    this.creditnote_date = useRef("creditnote_date");
    this.last_credit_note_page = useRef("last_credit_note_page");
    this.payments_date = useRef("payments_date");
    this.prepayments_date = useRef("prepayments_date");
    this.overpayments_date = useRef("overpayments_date");
    this.manualjournal_date = useRef("manualjournal_date");
    this.last_manualjournal_page = useRef("last_manualjournal_page");
    this.last_spendreceive_page = useRef("last_spendreceive_page");
    this.invoice_date = useRef("invoice_date");
    this.last_invoice_page = useRef("last_invoice_page");
    this.setCategory = this.setCategory.bind(this);
    
    this.fetchNextExecution();
    this.fetchNextExecutionWeekly();
    this.fetchNextExecutionMonthly();
    this.fetchNextExecutionDailyByCustomer();
    this.fetchNextExecutionWeeklyByCustomer();
    this.fetchNextExecutionMonthlyByCustomer();
    this.fetchNextExecutionOfLogs();
    this.fetchNextExecutionOfAuthentication();
    this.fetchNextExecutionOfPoExport();
    this.fetchNextExecutionOfInvoiceExport();
    this.fetchNextExecutionOfPaymentsImport();
    this.fetchNextExecutionOfInvoicesImport();
    this.fetchNextExecutionOfManualJournalImport();
    this.fetchNextExecutionOfPoImport();
    this.fetchNextExecutionOfSoImport();
    this.fetchNextExecutionOfPaymentExport();
    this.fetchAutomationStatus();

    

    // this.toggleInventoryTracking = this.toggleInventoryTracking.bind(this);


    // this.loadInventoryTracking();

    
}

   setCategory(category) {
    this.state.activeCategory = category;
    
}

async clearthelogs() {  
    this.state.showlogsAutomationPopup = true;

    const result_logs_cron_status = await rpc("/my/api/clean/xero/get_cron_status", {});
        if (result_logs_cron_status && result_logs_cron_status.success) {
            this.state.autoCleanlogs = result_logs_cron_status.active;
            
        }
}
async loadCompanyData() {

    const company = await this.orm.read(
        'res.company',
        [this.companyId],
        [
            'xero_client_id',
            'xero_client_secret',
            'xero_redirect_url',
            'default_account',
            'overpayment_journal',
            'prepayment_journal',
            'manual_journal',
            'default_prod_po',
            'default_prod_so',
            'skip_payment_journal',
        ]
    );

    if (company.length) {

        this.state.xero_client_id =
            company[0].xero_client_id || '';

        this.state.xero_client_secret =
            company[0].xero_client_secret || '';

        this.state.xero_redirect_url =
            company[0].xero_redirect_url || '';
        this.state.default_account = company[0].default_account || false;
        this.state.overpayment_journal = company[0].overpayment_journal || false;
        this.state.prepayment_journal = company[0].prepayment_journal|| false;
        this.state.manual_journal = company[0].manual_journal || false;
        this.state.default_prod_po = company[0].default_prod_po || false;
        this.state.default_prod_so = company[0].default_prod_so || false;
        this.state.skip_payment_journal = company[0].skip_payment_journal || false;
    }
}
async saveCompanyConfig() {
    try {
        await this.orm.call(
            'res.company',
            'write',
            [
                [this.companyId],
                {
                    default_account: this.state.default_account?.[0] || false,
                    overpayment_journal: this.state.overpayment_journal?.[0] || false,
                    prepayment_journal: this.state.prepayment_journal?.[0] || false,
                    manual_journal: this.state.manual_journal?.[0] || false,
                    default_prod_po: this.state.default_prod_po?.[0] || false,
                    default_prod_so: this.state.default_prod_so?.[0] || false,
                    skip_payment_journal: this.state.skip_payment_journal?.[0] || false,
                }
            ]
        );
        this.notification.add("Configuration saved successfully ✅", { type: "success" });
    } catch (error) {
        this.notification.add("Failed to save configuration", { type: "danger" });
    }
}
async searchRecords(model, query) {
    return await this.orm.call(model, 'name_search', [], {
        name: query,
        limit: 10,
    });
}
async onDefaultAccountInput(e) {
    const results = await this.orm.call('account.account', 'name_search', [], { name: e.target.value, limit: 10 });
    this.state.default_account_id = results[0] || false;
}

async onManualJournalInput(e) {
    const results = await this.orm.call('account.journal', 'name_search', [], { name: e.target.value, limit: 10 });
    this.state.manual_journal = results[0] || false;
}

async onOverpaymentJournalInput(e) {
    const results = await this.orm.call('account.journal', 'name_search', [], { name: e.target.value, limit: 10 });
    this.state.overpayment_journal_id = results[0] || false;
}

async onPrepaymentJournalInput(e) {
    const results = await this.orm.call('account.journal', 'name_search', [], { name: e.target.value, limit: 10 });
    this.state.prepayment_journal_id = results[0] || false;
}

async onSkipPaymentJournalInput(e) {
    const results = await this.orm.call('account.journal', 'name_search', [], { name: e.target.value, limit: 10 });
    this.state.skip_payment_journal_id = results[0] || false;
}

async onDefaultPOProductInput(e) {
    const results = await this.orm.call('product.product', 'name_search', [], { name: e.target.value, limit: 10 });
    this.state.default_prod_po = results[0] || false;
}

async onDefaultSOProductInput(e) {
    const results = await this.orm.call('product.product', 'name_search', [], { name: e.target.value, limit: 10 });
    this.state.default_prod_so = results[0] || false;
}

async setCategory(category) {
    this.state.activeCategory = category;
    
    if (category === 'authentication') {
        await this.fetchAutomationStatus();
    }
}

async fetchAutomationStatus() {

    const result_cron_status = await rpc("/my/api/authentication/get_cron_status", {});
        if (result_cron_status && result_cron_status.success) {
            this.state.autoAuthenticate = result_cron_status.active;
            
        }

    const result_cron_status_purchase_export = await rpc("/my/api/export/po/get_cron_status", {});
        if (result_cron_status_purchase_export && result_cron_status_purchase_export.success) {
            this.state.autoExportPo = result_cron_status_purchase_export.active;
            
        }

    const result_cron_status_invoices_export = await rpc("/my/api/invoices/export/get_cron_status", {});
        if (result_cron_status_invoices_export && result_cron_status_invoices_export.success) {
            this.state.autoExportInvoices = result_cron_status_invoices_export.active;
            
        }
    const result_cron_status_import_payments = await rpc("/my/api/import/payments/get_cron_status", {});
        if (result_cron_status_import_payments && result_cron_status_import_payments.success) {
            this.state.autoImportPayments = result_cron_status_import_payments.active;
            
        }

    const result_cron_status_import_invoices = await rpc("/my/api/import/invoices/get_cron_status", {});
        if (result_cron_status_import_invoices && result_cron_status_import_invoices.success) {
            this.state.autoImportInvoices = result_cron_status_import_invoices.active;
            
        }

    const result_cron_status_import_manual_journals = await rpc("/my/api/import/manual/journals/get_cron_status", {});
        if (result_cron_status_import_manual_journals && result_cron_status_import_manual_journals.success) {
            this.state.autoImportManualJournals = result_cron_status_import_manual_journals.active;
            
        }

    const result_cron_status_import_purchase_orders = await rpc("/my/api/import/purchase/orders/get_cron_status", {});
        if (result_cron_status_import_purchase_orders && result_cron_status_import_purchase_orders.success) {
            this.state.autoImportPo = result_cron_status_import_purchase_orders.active;
            
        }

    const result_cron_status_import_sale_orders = await rpc("/my/api/import/sales/orders/get_cron_status", {});
        if (result_cron_status_import_sale_orders && result_cron_status_import_sale_orders.success) {
            this.state.autoImportSo = result_cron_status_import_sale_orders.active;
            
        }
    
    const result_cron_status_export_payments = await rpc("/my/api/payments/export/get_cron_status", {});
        if (result_cron_status_export_payments && result_cron_status_export_payments.success) {
            this.state.autoExportPayments = result_cron_status_export_payments.active;
            
        }
  
}


async enableAutomation() {
    // this.state.showAutomationPopup = true;
     this.state.showAutomationTypePopup = true;
    //source
    const result_cron_status = await rpc("/my/api/invoices/get_cron_status", {});
        if (result_cron_status && result_cron_status.success) {
            this.state.autoUpdateInvoices = result_cron_status.active;
            
        }

    const result_cron_status_weekly = await rpc("/my/api/invoices/weekly/get_cron_status", {});
        if (result_cron_status_weekly && result_cron_status_weekly.success) {
            this.state.autoUpdateInvoicesWeekly = result_cron_status_weekly.active;
            
        }

    const result_cron_status_monthly = await rpc("/my/api/invoices/monthly/get_cron_status", {});
        if (result_cron_status_monthly && result_cron_status_monthly.success) {
            this.state.autoUpdateInvoicesMonthly = result_cron_status_monthly.active;
            
        }

    const result_cron_status_customer_daily = await rpc("/my/api/invoices/customer/daily/get_cron_status", {});
        if (result_cron_status_customer_daily && result_cron_status_customer_daily.success) {
            this.state.autoUpdateCustomerInvoices = result_cron_status_customer_daily.active;
            
        }

    const result_cron_status_customer_weekly = await rpc("/my/api/invoices/customer/weekly/get_cron_status", {});
        if (result_cron_status_customer_weekly && result_cron_status_customer_weekly.success) {
            this.state.autoUpdateCustomerInvoicesWeekly = result_cron_status_customer_weekly.active;
            
        }

    const result_cron_status_customer_monthly = await rpc("/my/api/invoices/customer/monthly/get_cron_status", {});
        if (result_cron_status_customer_monthly && result_cron_status_customer_monthly.success) {
            this.state.autoUpdateCustomerInvoicesMonthly = result_cron_status_customer_monthly.active;
            
        }
}
openSourceAutomation() {
    this.state.showAutomationTypePopup = false;
    this.state.showAutomationPopup = true;
}

openCustomerAutomation() {
    this.state.showAutomationTypePopup = false;
    this.state.showCustomerAutomationPopup = true;
}

closeAutomationTypePopup() {
    this.state.showAutomationTypePopup = false;
}
closeClearLogsPopup() {
    this.state.showlogsAutomationPopup = false;
}

closeAutomationPopup() {
    this.state.showAutomationPopup = false;
}

closeCustomerAutomationPopup() {
    this.state.showCustomerAutomationPopup = false;
}

//back 
openSourceAutomation() {
    this.state.showAutomationTypePopup = false;
    this.state.showAutomationPopup = true;
}

openCustomerAutomation() {
    this.state.showAutomationTypePopup = false;
    this.state.showCustomerAutomationPopup = true;
}

backToAutomationType() {
    this.state.showAutomationPopup = false;
    this.state.showCustomerAutomationPopup = false;
    this.state.showAutomationTypePopup = true;
}

//auto clean logs 
async toggleAutoCleanLogs() {
    const oldValue = this.state.autoCleanlogs;
    this.state.autoCleanlogs = !oldValue;

    try {
        const result = await rpc("/my/api/clean/xero/logs/toggle_cron", { value: this.state.autoCleanlogs });

        if (!result.success) {
            this.state.autoCleanlogs = oldValue;
            this.notification.add(result.message, { type: "danger" });
        } else {
            this.notification.add(result.message, { type: "success" });
        }
    } catch (err) {
        console.error(err);
        this.notification.add("⚠️ Failed to toggle auto-sync.", { type: "danger" });
    }
}
async syncClearLogsNow() {
    try {
        this.ui.block();

        const result = await rpc("/web/dataset/call_kw", {
            model: "log.cleanup",
            method: "delete_all_xero_logs_now",
            args: [],
            kwargs: {},
        });

        this.state.autoSyncCLearLogs = true;

      
        if (result?.warnings?.length) {
            this.env.services.notification.add(
                result.warnings.join("\n"),
                { type: "warning", sticky: false }
            );
        }

     
        this.env.services.notification.add(
            "Xero Logs Cleaned Successfully ✅",
            { type: "success" }
        );

    } catch (error) {

    
        this.env.services.notification.add(
            "Technical error occurred while syncing invoices ⚠️",
            { type: "danger", sticky: false }
        );

        console.error("Invoice Sync Error:", error);

    } finally {
        this.ui.unblock();
    }
}
async fetchNextExecutionOfLogs() {
    try {
        const result = await rpc("/get/clean/xero/logs/cron/next_execution", {});

        if (result.success) {
            this.state.nextExecutionTimeofLogs = result.next_execution;
        } else {
            this.state.nextExecutionTimeofLogs = "N/A";
        }

    } catch (error) {
        console.error("Error fetching cron time:", error);
        this.state.nextExecutionTimeofLogs = "N/A";
    }
}

// INVOICE SYNC CRON ON DAILY BASIS
async toggleAutoUpdateInvoices() {
    const oldValue = this.state.autoUpdateInvoices;
    this.state.autoUpdateInvoices = !oldValue;

    try {
        const result = await rpc("/my/api/invoices/toggle_cron", { value: this.state.autoUpdateInvoices });

        if (!result.success) {
            this.state.autoUpdateInvoices = oldValue;
            this.notification.add(result.message, { type: "danger" });
        } else {
            this.notification.add(result.message, { type: "success" });
        }
    } catch (err) {
        console.error(err);
        this.notification.add("⚠️ Failed to toggle auto-sync.", { type: "danger" });
    }
}
async syncInvoicesNow() {
    try {
        this.ui.block();

        const result = await rpc("/web/dataset/call_kw", {
            model: "sync.invoice.cron",
            method: "sync_daily_invoices",
            args: [[]],
            kwargs: {},
        });

        this.state.autoSyncInvoices = true;

      
        if (result?.warnings?.length) {
            this.env.services.notification.add(
                result.warnings.join("\n"),
                { type: "warning", sticky: false }
            );
        }

     
        this.env.services.notification.add(
            "Invoices Sync Completed Successfully ✅",
            { type: "success" }
        );

    } catch (error) {

    
        this.env.services.notification.add(
            "Technical error occurred while syncing invoices ⚠️",
            { type: "danger", sticky: false }
        );

        console.error("Invoice Sync Error:", error);

    } finally {
        this.ui.unblock();
    }
}
async fetchNextExecution() {
    try {
        const result = await rpc("/get/invoice/daily/cron/next_execution", {});

        if (result.success) {
            this.state.nextExecutionTime = result.next_execution;
        } else {
            this.state.nextExecutionTime = "N/A";
        }

    } catch (error) {
        console.error("Error fetching cron time:", error);
        this.state.nextExecutionTime = "N/A";
    }
}

// INVOICE SYNC CRON ON WEEKLY BASIS
async toggleAutoUpdateInvoicesWeekly() {
    const oldValue = this.state.autoUpdateInvoicesWeekly;
    this.state.autoUpdateInvoicesWeekly = !oldValue;

    try {
        const result = await rpc("/my/api/invoices/weekly/toggle_cron", { value: this.state.autoUpdateInvoicesWeekly });

        if (!result.success) {
            this.state.autoUpdateInvoicesWeekly = oldValue;
            this.notification.add(result.message, { type: "danger" });
        } else {
            this.notification.add(result.message, { type: "success" });
        }
    } catch (err) {
        console.error(err);
        this.notification.add("⚠️ Failed to toggle auto-sync.", { type: "danger" });
    }
}
async syncInvoicesNowWeekly(){
    try {
        this.ui.block();

        const result = await rpc("/web/dataset/call_kw", {
            model: "sync.invoice.cron",   // must match model_sync_inventory_cron
            method: "sync_weekly_invoices",
            args: [[]],
            kwargs: {},
        });
        this.state.autoSyncInvoicesWeekly = true;

        if (result?.warnings?.length) {
            this.env.services.notification.add(
                result.warnings.join("\n"),
                { type: "warning", sticky:false }
            );
        }

        // Success message
        this.env.services.notification.add(
            "Invoices Sync Completed Successfully ✅",
            { type: "success" }
        );

    } catch (error) {

        // Only technical errors come here
        this.env.services.notification.add(
            "Technical error occurred while syncing invoices ⚠️",
            { type: "danger", sticky: false}
        );

        console.error("Invoice Sync Error:", error);

    } finally {
        this.ui.unblock();
    }
}
async fetchNextExecutionWeekly() {
    try {
        const result = await rpc("/get/invoice/weekly/cron/next_execution", {});

        if (result.success) {
            this.state.nextExecutionTimeWeekly = result.next_execution;
        } else {
            this.state.nextExecutionTimeWeekly = "N/A";
        }

    } catch (error) {
        console.error("Error fetching cron time:", error);
        this.state.nextExecutionTimeWeekly = "N/A";
    }
}
// INVOICE SYNC CRON ON MONTHLY BASIS
async toggleAutoUpdateInvoicesMonthly() {
    const oldValue = this.state.autoUpdateInvoicesMonthly;
    this.state.autoUpdateInvoicesMonthly = !oldValue;

    try {
        const result = await rpc("/my/api/invoices/monthly/toggle_cron", { value: this.state.autoUpdateInvoicesMonthly });

        if (!result.success) {
            this.state.autoUpdateInvoicesMonthly = oldValue;
            this.notification.add(result.message, { type: "danger" });
        } else {
            this.notification.add(result.message, { type: "success" });
        }
    } catch (err) {
        console.error(err);
        this.notification.add("⚠️ Failed to toggle auto-sync.", { type: "danger" });
    }
}
async syncInvoicesNowMonthly(){
    try {
        this.ui.block();

        const result = await rpc("/web/dataset/call_kw", {
            model: "sync.invoice.cron",   // must match model_sync_inventory_cron
            method: "sync_monthly_invoices",
            args: [[]],
            kwargs: {},
        });
        this.state.autoSyncInvoicesMonthly = true;

        if (result?.warnings?.length) {
            this.env.services.notification.add(
                result.warnings.join("\n"),
                { type: "warning", sticky: false }
            );
        }

        // Success message
        this.env.services.notification.add(
            "Invoices Sync Completed Successfully ✅",
            { type: "success" }
        );

    } catch (error) {

        // Only technical errors come here
        this.env.services.notification.add(
            "Technical error occurred while syncing invoices ⚠️",
            { type: "danger", sticky: false}
        );

        console.error("Invoice Sync Error:", error);

    } finally {
        this.ui.unblock();
    }
}
async fetchNextExecutionMonthly() {
    try {
        const result = await rpc("/get/invoice/monthly/cron/next_execution", {});

        if (result.success) {
            this.state.nextExecutionTimeMonthly = result.next_execution;
        } else {
            this.state.nextExecutionTimeMonthly = "N/A";
        }

    } catch (error) {
        console.error("Error fetching cron time:", error);
        this.state.nextExecutionTimeMonthly= "N/A";
    }
}
//merging posting invoices on customer basis
//Daily
async toggleAutoUpdateCustomerInvoices() {
    const oldValue = this.state.autoUpdateCustomerInvoices;
    this.state.autoUpdateCustomerInvoices = !oldValue;

    try {
        const result = await rpc("/my/api/invoices/by/customer/daily/toggle_cron", { value: this.state.autoUpdateCustomerInvoices });

        if (!result.success) {
            this.state.autoUpdateCustomerInvoices = oldValue;
            this.notification.add(result.message, { type: "danger" });
        } else {
            this.notification.add(result.message, { type: "success" });
        }
    } catch (err) {
        console.error(err);
        this.notification.add("⚠️ Failed to toggle auto-sync.", { type: "danger" });
    }
}
async syncInvoicesNowDailyByCustomers() {
    try {
        this.ui.block();

        const result = await rpc("/web/dataset/call_kw", {
            model: "sync.invoice.cron",
            method: "sync_daily_invoices_customer_wise",
            args: [[]],
            kwargs: {},
        });

        this.state.autoSyncCustomerInvoices = true;

      
        if (result?.warnings?.length) {
            this.env.services.notification.add(
                result.warnings.join("\n"),
                { type: "warning", sticky: false }
            );
        }

     
        this.env.services.notification.add(
            "Invoices Sync Completed Successfully ✅",
            { type: "success" }
        );

    } catch (error) {

    
        this.env.services.notification.add(
            "Technical error occurred while syncing invoices ⚠️",
            { type: "danger", sticky: false }
        );

        console.error("Invoice Sync Error:", error);

    } finally {
        this.ui.unblock();
    }
}
async fetchNextExecutionDailyByCustomer() {
    try {
        const result = await rpc("/get/invoice/customer/daily/cron/next_execution", {});

        if (result.success) {
            this.state.nextExecutionTimeCustomerDaily = result.next_execution;
        } else {
            this.state.nextExecutionTimeCustomerDaily = "N/A";
        }

    } catch (error) {
        console.error("Error fetching cron time:", error);
        this.state.nextExecutionTimeCustomerDaily = "N/A";
    }
}
//merging posting invoices on customer basis
//Weekly
async toggleAutoUpdateCustomerInvoicesWeekly() {
    const oldValue = this.state.autoUpdateCustomerInvoicesWeekly;
    this.state.autoUpdateCustomerInvoicesWeekly = !oldValue;

    try {
        const result = await rpc("/my/api/invoices/by/customer/weekly/toggle_cron", { value: this.state.autoUpdateCustomerInvoicesWeekly });

        if (!result.success) {
            this.state.autoUpdateCustomerInvoicesWeekly = oldValue;
            this.notification.add(result.message, { type: "danger" });
        } else {
            this.notification.add(result.message, { type: "success" });
        }
    } catch (err) {
        console.error(err);
        this.notification.add("⚠️ Failed to toggle auto-sync.", { type: "danger" });
    }
}
async syncInvoicesNowWeeklyByCustomers() {
    try {
        this.ui.block();

        const result = await rpc("/web/dataset/call_kw", {
            model: "sync.invoice.cron",
            method: "sync_weekly_customer_invoices",
            args: [[]],
            kwargs: {},
        });

        this.state.autoSyncCustomerInvoicesWeekly = true;

      
        if (result?.warnings?.length) {
            this.env.services.notification.add(
                result.warnings.join("\n"),
                { type: "warning", sticky: false }
            );
        }

     
        this.env.services.notification.add(
            "Invoices Sync Completed Successfully ✅",
            { type: "success" }
        );

    } catch (error) {

    
        this.env.services.notification.add(
            "Technical error occurred while syncing invoices ⚠️",
            { type: "danger", sticky: false }
        );

        console.error("Invoice Sync Error:", error);

    } finally {
        this.ui.unblock();
    }
}
async fetchNextExecutionWeeklyByCustomer() {
    try {
        const result = await rpc("/get/invoice/customer/weekly/cron/next_execution", {});

        if (result.success) {
            this.state.nextExecutionTimeCustomerWeekly = result.next_execution;
        } else {
            this.state.nextExecutionTimeCustomerWeekly = "N/A";
        }

    } catch (error) {
        console.error("Error fetching cron time:", error);
        this.state.nextExecutionTimeCustomerWeekly = "N/A";
    }
}
//merging posting invoices on customer basis
//Monthly
async toggleAutoUpdateCustomerInvoicesMonthly() {
    const oldValue = this.state.autoUpdateCustomerInvoicesMonthly;
    this.state.autoUpdateCustomerInvoicesMonthly = !oldValue;

    try {
        const result = await rpc("/my/api/invoices/by/customer/monthly/toggle_cron", { value: this.state.autoUpdateCustomerInvoicesMonthly });

        if (!result.success) {
            this.state.autoUpdateCustomerInvoicesMonthly = oldValue;
            this.notification.add(result.message, { type: "danger" });
        } else {
            this.notification.add(result.message, { type: "success" });
        }
    } catch (err) {
        console.error(err);
        this.notification.add("⚠️ Failed to toggle auto-sync.", { type: "danger" });
    }
}
async syncInvoicesNowMonthlyByCustomers() {
    try {
        this.ui.block();

        const result = await rpc("/web/dataset/call_kw", {
            model: "sync.invoice.cron",
            method: "sync_monthly_customer_invoices",
            args: [[]],
            kwargs: {},
        });

        this.state.autoSyncCustomerInvoicesMonthly = true;

      
        if (result?.warnings?.length) {
            this.env.services.notification.add(
                result.warnings.join("\n"),
                { type: "warning", sticky: false}
            );
        }

     
        this.env.services.notification.add(
            "Invoices Sync Completed Successfully ✅",
            { type: "success" }
        );

    } catch (error) {

    
        this.env.services.notification.add(
            "Technical error occurred while syncing invoices ⚠️",
            { type: "danger", sticky:false }
        );

        console.error("Invoice Sync Error:", error);

    } finally {
        this.ui.unblock();
    }
}
async fetchNextExecutionMonthlyByCustomer() {
    try {
        const result = await rpc("/get/invoice/customer/monthly/cron/next_execution", {});

        if (result.success) {
            this.state.nextExecutionTimeCustomerMonthly = result.next_execution;
        } else {
            this.state.nextExecutionTimeCustomerMonthly = "N/A";
        }

    } catch (error) {
        console.error("Error fetching cron time:", error);
        this.state.nextExecutionTimeCustomerMonthly = "N/A";
    }
}
//end
async loadInventoryTracking() {
    try {
        const result = await rpc("/my/api/inventory/get_tracking_status", {});

        if (result && result.success) {
            this.state.inventoryTracking = result.active;
        }
    } catch (error) {
        console.error("Error fetching tracking status", error);
    }
}

    
async toggleInventoryTracking(ev) {
    ev.stopPropagation();
    ev.preventDefault();

    // const companyId = this.company.currentCompany.id;
    // const companyId = session.company_id;
    const companyId = session.user_companies.current_company;

    const action = await this.orm.call(
        "res.company",
        "open_xero_inventory_confirm_wizard",
        [companyId]
    );

    this.action.doAction(action, {
        onClose: async () => {
            await this.loadInventoryTracking(); // refresh actual value
        },
    });
}


//map taxes
async autoMapTaxes() {
    try {
        const result = await this.orm.call(
            'xero.tax.mapping',
            'action_auto_map_taxes',
            [],
            {}
        );

        // action_auto_map_taxes returns a display_notification action
        if (result && result.type === 'ir.actions.client') {
            this.action.doAction(result);
        }

    } catch (error) {
        this.notification.add(
            error.message || 'An error occurred while mapping taxes.',
            { type: 'danger', sticky: false, title: 'Auto Tax Mapping Failed' ,sticky: false}
        );
    }
}



    

 // BUTTON CLICK HANDLER
    async importAccounts() {
    try {
        const response = await rpc("/web/dataset/call_kw", {
            model: "res.company",   
            method: "import_accounts",               
            args : [{}],
            kwargs: {},                          
        });

        if (response) {
            this.env.services.notification.add(
                "Accounts imported successfully!",
                { type: "success", sticky: false }
            );
        } else {
            this.env.services.notification.add(
                "Failed to import accounts",
                { type: "danger", sticky: false }
            );
        }

    } catch (error) {

        let errorMessage = "Error occurred while triggering Accounts sync";

        if (error?.data?.message) {
            errorMessage = error.data.message;
        }

        this.env.services.notification.add(
            errorMessage,
            { type: "warning", sticky: false }
        );
    } finally {
        this.ui.unblock();
    }
}

    // Import Taxes
    async importTaxes(){
        try {
        const response = await rpc("/web/dataset/call_kw", {
            model: "res.company",  
            method: "import_tax",                
            args : [[]],
            kwargs: {},                            
        });

        if (response) {
            this.env.services.notification.add(
                "Taxes imported successfully!",
                { type: "success", sticky: false }
            );
        } else {
            this.env.services.notification.add(
                "Failed to import Taxes",
                { type: "danger", sticky: false }
            );
        }

    } catch (error) {

        let errorMessage = "Error occurred while importing taxes";

        if (error?.data?.message) {
            errorMessage = error.data.message;
        }

        this.env.services.notification.add(
            errorMessage,
            { type: "warning", sticky: false }
        );
    }
}
    //Import inventory
    async importInventory(){
        try {
        const response = await rpc("/web/dataset/call_kw", {
            model: "res.company",  
            method: "import_inventory",               
            args : [[]],
            kwargs: {},                               // no keyword args
        });

        if (response) {
            this.env.services.notification.add(
                "Inventory imported successfully!",
                { type: "success", sticky: false }
            );
        } else {
            this.env.services.notification.add(
                "Failed to import Inventory",
                { type: "danger", sticky: false }
            );
        }

    } catch (error) {
        this.env.services.notification.add(
            "Error occurred while importing Inventory",
            { type: "danger", sticky: false }
        );
    }
    }

async loadXeroStatus() {
    const result = await this.orm.read(
        "res.company",
        [this.companyId],
        ["xero_connected"]
    );

    this.state.xeroConnected = result[0].xero_connected;
}
async onClickRefreshToken() {
    try {
        console.log("Refreshing Xero token...");

        // const companyId = this.env.company.id;

        const result = await this.orm.call(
            "res.company",
            "refresh_token",
            [[this.companyId]]
        );

        console.log("Refresh response:", result);
        await this.loadXeroStatus();

        this.notification.add("Xero token refreshed successfully ✅", {
            type: "success",
        });

    } catch (error) {
        console.error("Refresh token failed:", error);

        this.notification.add("Xero token refresh failed ❌", {
            type: "danger",
        });
    }
}
async connectToXero(ev) {
    ev.preventDefault();
    ev.stopPropagation();

    try {
        const clientId = this.state.xero_client_id?.trim();
        const clientSecret = this.state.xero_client_secret?.trim();
        const redirectUrl = this.state.xero_redirect_url?.trim();


        //alert(`ID: ${clientId}\nSECRET: ${clientSecret}\nREDIRECT: ${redirectUrl}`);


        await this.orm.call(
            'res.company',
            'write',
            [
                [this.companyId],
                {
                    xero_client_id: clientId,
                    xero_client_secret: clientSecret,
                    xero_redirect_url: redirectUrl,
                }
            ]
        );

        const action = await rpc("/web/dataset/call_kw", {
            model: 'res.company',
            method: 'login',
            args: [[this.companyId]],
            kwargs: {},
        });

        //alert("ACTION: " + JSON.stringify(action));  // check what comes back

        if (action?.type === 'ir.actions.act_url') {
            // Odoo URL action — open it directly
            window.open(action.url, action.target === 'self' ? '_self' : '_blank');
        } else if (action?.url) {
            // Plain dict with url key
            window.open(action.url, '_self');
        } else {
            alert("No URL found in action: " + JSON.stringify(action));
        }

    } catch (error) {
        console.error("XERO ERROR:", error);
        this.notification.add(
            error?.data?.message || error?.message || "Authentication failed",
            { type: "danger" }
        );
    }
}

// async toggleInventoryTracking(ev) {
//     ev.stopPropagation();
//     ev.preventDefault();

//     const companyId = this.getCompanyId();  // ✅ use helper

//     const action = await this.orm.call(
//         "res.company",
//         "open_xero_inventory_confirm_wizard",
//         [companyId]
//     );

//     this.action.doAction(action, {
//         onClose: async () => {
//             await this.loadInventoryTracking();
//         },
//     });
// }
    //Import Products
     async importProducts(){
        try {
        const response = await rpc("/web/dataset/call_kw", {
            model: "res.company",   // <-- CHANGE THIS to your model name
            method: "import_products",                // Python method
            args : [[]],
            kwargs: {},                               // no keyword args
        });

        if (response) {
            this.env.services.notification.add(
                "Inventory imported successfully!",
                { type: "success", sticky: false }
            );
        } else {
            this.env.services.notification.add(
                "Failed to import Inventory",
                { type: "danger", sticky: false }
            );
        }

    } catch (error) {
        this.env.services.notification.add(
            "Error occurred while importing Inventory",
            { type: "danger", sticky: false }
        );
    }
    }

    // Import Contact Groups
    async importContactGroups(){
        try {
        const response = await rpc("/web/dataset/call_kw", {
            model: "res.company",   // <-- CHANGE THIS to your model name
            method: "import_contact_groups",                // Python method
            args : [[]],
            kwargs: {},                               // no keyword args
        });

        if (response) {
            this.env.services.notification.add(
                "Contact Groups imported successfully!",
                { type: "success", sticky: false }
            );
        } else {
            this.env.services.notification.add(
                "Failed to import Contact Groups",
                { type: "danger", sticky: false }
            );
        }

    } catch (error) {
        this.env.services.notification.add(
            "Error occurred while importing Contact Groups",
            { type: "danger", sticky: false }
        );
    }
    }
    // Import Contacts
    async importContacts(){
        try {
        const response = await rpc("/web/dataset/call_kw", {
            model: "res.company",   // <-- CHANGE THIS to your model name
            method: "import_customers",                // Python method
            args : [[]],
            kwargs: {},                               // no keyword args
        });

        if (response) {
            this.env.services.notification.add(
                "Contacts imported successfully!",
                { type: "success", sticky: false }
            );
        } else {
            this.env.services.notification.add(
                "Failed to import Contacts",
                { type: "danger", sticky: false }
            );
        }

    } catch (error) {
        this.env.services.notification.add(
            "Error occurred while importing Contacts",
            { type: "danger", sticky: false }
        );
    }
    }




    async  importSaleOrders(){
        try {

        const fromDate = this.saleorderDateRef.el?.value; // <-- updated



        if (!fromDate) {
            this.env.services.notification.add(
                "Please select Import Purchase orders From date",
                { type: "warning" }
            );
            return;
        }
     
        const response = await rpc("/web/dataset/call_kw", {
            model: "res.company",   
            method: "import_sale_order",              
            args : [[]],
            kwargs: {},                               
        });

        if (response) {
            this.env.services.notification.add(
                "Import Invoices from Xero",
                { type: "success", sticky: false }
            );
        } else {
            this.env.services.notification.add(
                "Failed to import Invoices from Xero",
                { type: "danger", sticky: false}
            );
        }

    } catch (error) {
        this.env.services.notification.add(
            "Error occurred while importing Invoices",
            { type: "danger", sticky: false}
        );
    }
    }

    async importPurchaseOrder() {
    try {
        const fromDate = this.purchaseorder_date.el?.value;

        if (!fromDate) {
            this.env.services.notification.add(
                "Please select Import Purchase orders From date",
                { type: "warning" }
            );
            return;
        }

        const response = await rpc("/web/dataset/call_kw", {
            model: "res.company",
            method: "import_purchase_order",
            args: [[]],
            kwargs: { date_from: fromDate },  // <-- pass date here
        });

        if (response) {
            this.env.services.notification.add(
                "Purchase Orders imported successfully",
                { type: "success", sticky: false }
            );
        } else {
            this.env.services.notification.add(
                "Failed to import Purchase Orders from Xero",
                { type: "danger", sticky: false }
            );
        }

    } catch (error) {
        this.env.services.notification.add(
            "Error occurred while importing Purchase Orders",
            { type: "danger", sticky: false }
        );
    }
}



//     async importPurchaseOrder() {
//     try {
//         const fromDate = this.purchaseorder_date.el?.value;
//         const lastPoPage = this.last_po_page.el?.value;

//         if (!fromDate) {
//             this.env.services.notification.add(
//                 "Please select Import Purchase Order From date",
//                 { type: "warning" }
//             );
//             return;
//         }
//         // if (!lastPoPage) {
//         //     this.env.services.notification.add(
//         //         "Please enter Last Imported PO Page",
//         //         { type: "warning" }
//         //     );
//         //     return;
//         // }

//         // Fetch company ID
//         const company = await rpc("/web/dataset/call_kw", {
//             model: "res.company",
//             method: "search_read",
//             args: [[['id', '!=', false]]],
//             kwargs: { fields: ['id'], limit: 1 },
//         });
//         if (!company || !company[0]) {
//             this.env.services.notification.add(
//                 "Could not fetch current company",
//                 { type: "danger", sticky: false }
//             );
//             return;
//         }
//         const companyId = company[0].id;

//         // Write values to company
//         await rpc("/web/dataset/call_kw", {
//             model: "res.company",
//             method: "write",
//             args: [[companyId], {
//                 x_purchaseorder_date: fromDate,
//                 xero_last_imported_po_page: parseInt(lastPoPage),
//             }],
//             kwargs: {},
//         });

//         // Call Python import method
//         const response = await rpc("/web/dataset/call_kw", {
//             model: "res.company",
//             method: "import_purchase_order",
//             args: [[]],
//             kwargs: {},
//         });

//         if (response) {
//             this.env.services.notification.add(
//                 "Purchase Orders imported successfully!",
//                 { type: "success", sticky: false }
//             );
//         } else {
//             this.env.services.notification.add(
//                 "Failed to import Purchase Orders",
//                 { type: "danger", sticky: false}
//             );
//         }

//     } catch (error) {
//         this.env.services.notification.add(
//             "Error occurred while importing Purchase Orders",
//             { type: "danger", sticky: false }
//         );
//     }
// }
// async importPurchaseOrder() {
//     try {
//         const fromDate = this.purchaseorder_date.el?.value;

//         if (!fromDate) {
//             this.env.services.notification.add(
//                 "Please select Import Purchase Orders From Date",
//                 { type: "warning" }
//             );
//             return;
//         }

//         // Get company
//         const company = await rpc("/web/dataset/call_kw", {
//             model: "res.company",
//             method: "search_read",
//             args: [[["id", "!=", false]]],
//             kwargs: {
//                 fields: ["id"],
//                 limit: 1,
//             },
//         });

//         if (!company || !company.length) {
//             this.env.services.notification.add(
//                 "Could not fetch company",
//                 { type: "danger" }
//             );
//             return;
//         }

//         const companyId = company[0].id;

//         // Save selected date
//         await rpc("/web/dataset/call_kw", {
//             model: "res.company",
//             method: "write",
//             args: [[companyId], {
//                 x_purchaseorder_date: fromDate,
//             }],
//             kwargs: {},
//         });

//         console.log("Selected PO Date:", fromDate);

//         // Import Purchase Orders
//         const response = await rpc("/web/dataset/call_kw", {
//             model: "res.company",
//             method: "import_purchase_order",
//             args: [[companyId]],
//             kwargs: {},
//         });

//         console.log("PO Import Response:", response);

//         this.env.services.notification.add(
//             "Purchase Orders imported successfully ✅",
//             {
//                 type: "success",
//                 sticky: false,
//             }
//         );

//     } catch (error) {
//         console.error("PO Import Error:", error);

//         this.env.services.notification.add(
//             error?.message || "Error occurred while importing Purchase Orders",
//             {
//                 type: "danger",
//                 sticky: false,
//             }
//         );
//     }
// }

 //IMPORT Credit Notes
    async importCreditNotes(){
        try {
        const fromDate = this.creditnote_date.el?.value;
        const lastCreditNotePage = this.last_credit_note_page.el?.value;


        if (!fromDate) {
            this.env.services.notification.add(
                "Please select Import Credit Note From date",
                { type: "warning" }
            );
            return;
        }
        //  if (!lastCreditNotePage) {
        //     this.env.services.notification.add(
        //         "Please enter Last Imported Credit Note Page",
        //         { type: "warning" }
        //     );
        //     return;
        // }
        const response = await rpc("/web/dataset/call_kw", {
            model: "res.company",   
            method: "import_credit_notes",              
            args : [[]],
            kwargs: {},                               
        });

        if (response) {
            this.env.services.notification.add(
                "Credit Notes imported successfully!",
                { type: "success", sticky: false }
            );
        } else {
            this.env.services.notification.add(
                "Failed to import Credit Notes",
                { type: "danger", sticky: false }
            );
        }

    } catch (error) {
        this.env.services.notification.add(
            "Error occurred while importing Credit Notes",
            { type: "danger", sticky: false }
        );
    }
    }
    //IMPORT Payments
    async importPayments(){
        try {
        const fromDate = this.payments_date.el?.value;



        if (!fromDate) {
            this.env.services.notification.add(
                "Please select Import Payments From date",
                { type: "warning" }
            );
            return;
        }
     
        const response = await rpc("/web/dataset/call_kw", {
            model: "res.company",   
            method: "import_payments",              
            args : [[]],
            kwargs: {},                               
        });

        if (response) {
            this.env.services.notification.add(
                "Payments imported successfully!",
                { type: "success", sticky: false }
            );
        } else {
            this.env.services.notification.add(
                "Failed to import Payments",
                { type: "danger", sticky: false }
            );
        }

    } catch (error) {
        this.env.services.notification.add(
            "Error occurred while importing Payments",
            { type: "danger", sticky: false }
        );
    }
    }
        //IMPORT Pre Payments
    async importPrePayments(){
    try {
        const fromDate = this.prepayments_date.el?.value; // <-- updated
        if (!fromDate) {
            this.env.services.notification.add(
                "Please select Import Pre Payments From date",
                { type: "warning" }
            );
            return;
        }
        const response = await rpc("/web/dataset/call_kw", {
            model: "res.company",   
            method: "import_prepayments",              
            args : [[]],
            kwargs: {},                               
        });

        if (response) {
            this.env.services.notification.add(
                "Pre Payments imported successfully!",
                { type: "success", sticky: false }
            );
        } else {
            this.env.services.notification.add(
                "Failed to import Pre Payments",
                { type: "danger", sticky: false }
            );
        }

    } catch (error) {
        this.env.services.notification.add(
            "Error occurred while importing Pre Payments",
            { type: "danger", sticky: false }
        );
    }
}

     //IMPORT Over Payments
    async importOverPayments(){
        try {
        // const fromDate = this.prepayments_date.el?.value; // <-- updated


        // if (!fromDate) {
        //     this.env.services.notification.add(
        //         "Please select Import Over Payments From date",
        //         { type: "warning" }
        //     );
        //     return;
        // }
        const response = await rpc("/web/dataset/call_kw", {
            model: "res.company",   
            method: "import_overpayments",              
            args : [[]],
            kwargs: {},                               
        });

        if (response) {
            this.env.services.notification.add(
                " Over Payments imported successfully!",
                { type: "success", sticky: false }
            );
        } else {
            this.env.services.notification.add(
                "Failed to import  Over Payments",
                { type: "danger", sticky: false }
            );
        }

    } catch (error) {
        this.env.services.notification.add(
            "Error occurred while importing Over Payments",
            { type: "danger", sticky: false }
        );
    }
    }
     //IMPORT Manual Journal
    async importManualJournal(){
        try {
        const fromDate = this.manualjournal_date.el?.value; // <-- updated
        const lastManualJournalPage = this.last_manualjournal_page.el?.value;


        if (!fromDate) {
            this.env.services.notification.add(
                "Please select Import Manual Journal From date",
                { type: "warning" }
            );
            return;
        }
        //  if (!lastManualJournalPage) {
        //     this.env.services.notification.add(
        //         "Please enter Last Imported Manual Journal Page",
        //         { type: "warning" }
        //     );
        //     return;
        // }
        const response = await rpc("/web/dataset/call_kw", {
            model: "res.company",   
            method: "import_manual_journals",              
            args : [[]],
            kwargs: {},                               
        });

        if (response) {
            this.env.services.notification.add(
                " Manual Journals imported successfully!",
                { type: "success", sticky: false }
            );
        } else {
            this.env.services.notification.add(
                "Failed to import Manual Journals",
                { type: "danger", sticky: false }
            );
        }

    } catch (error) {
        this.env.services.notification.add(
            "Error occurred while importing Manual Journals",
            { type: "danger", sticky: false }
        );
    }
    }
     //IMPORT Spend/Receive Money
    async importSpendMoney(){
        try {
        const lastSpendReceivePage = this.last_spendreceive_page.el?.value;
        // const lastCreditNotePage = this.last_credit_note_page.el?.value;


        //  if (!lastSpendReceivePage) {
        //     this.env.services.notification.add(
        //         "Please enter Last Imported Spend/Receive Money Page",
        //         { type: "warning" }
        //     );
        //     return;
        // }
        const response = await rpc("/web/dataset/call_kw", {
            model: "res.company",   
            method: "import_spnd_mny",              
            args : [[]],
            kwargs: {},                               
        });

        if (response) {
            this.env.services.notification.add(
                " Spend/Receive Money imported successfully!",
                { type: "success", sticky: false }
            );
        } else {
            this.env.services.notification.add(
                "Failed to import Spend/Receive Money",
                { type: "danger", sticky: false}
            );
        }

    } catch (error) {
        this.env.services.notification.add(
            "Error occurred while importing  Spend/Receive Money",
            { type: "danger", sticky: false }
        );
    }
    }
     //IMPORT All Spend/Receive Money
    async importAllSpendMoney(){
        try {
        const response = await rpc("/web/dataset/call_kw", {
            model: "res.company",   
            method: "spnd_rcv_main_function_all",              
            args : [[]],
            kwargs: {},                               
        });

        if (response) {
            this.env.services.notification.add(
                " All Spend/Receive Money imported successfully!",
                { type: "success", sticky: false }
            );
        } else {
            this.env.services.notification.add(
                "Failed to import  All Spend/Receive Money",
                { type: "danger", sticky: false }
            );
        }

    } catch (error) {
        this.env.services.notification.add(
            "Error occurred while importing All Spend/Receive Money",
            { type: "danger", sticky: false }
        );
    }
    }
    async enableTrackInventory(){
        try {
        const response = await rpc("/web/dataset/call_kw", {
            model: "res.company",   
            method: "spnd_rcv_main_function_all",              
            args : [[]],
            kwargs: {},                               
        });

        if (response) {
            this.env.services.notification.add(
                " Enable track Inventory successfully!",
                { type: "success", sticky: false }
            );
        } else {
            this.env.services.notification.add(
                "Failed to enable track Inventory",
                { type: "danger", sticky: false }
            );
        }

    } catch (error) {
        this.env.services.notification.add(
            "Error occurred while importing All Spend/Receive Money",
            { type: "danger", sticky: false }
        );
    }
    }
     //IMPORT All Spend/Receive Money
    async importFailedSpendMoney(){
        try {
        const response = await rpc("/web/dataset/call_kw", {
            model: "res.company",   
            method: "spnd_rcv_main_function_failed",              
            args : [[]],
            kwargs: {},                               
        });

        if (response) {
            this.env.services.notification.add(
                "Failed Spend/Receive Money imported successfully!",
                { type: "success", sticky: false }
            );
        } else {
            this.env.services.notification.add(
                "Failed to import  Failed Spend/Receive Money",
                { type: "danger", sticky: false }
            );
        }

    } catch (error) {
        this.env.services.notification.add(
            "Error occurred while importing Failed Spend/Receive Money",
            { type: "danger", sticky: false }
        );
    }
    }
async viewFailedSpendMoney() {
    try {
        const action = await rpc("/web/dataset/call_kw", {
            model: "res.company",
            method: "view_spnd_rcv_main_function_failed",
            args: [[]],
            kwargs: {},
        });

        if (!action || action.type !== "ir.actions.act_window") {
            this.env.services.notification.add(
                "No failed Spend/Receive Money records found",
                { type: "warning" }
            );
            return;
        }

        await this.env.services.action.doAction(action);

    } catch (error) {
        console.error("viewFailedSpendMoney error:", error);  // <-- add this
        this.env.services.notification.add(
            `Failed: ${error.message || error}`,  // <-- show real error
            { type: "danger", sticky: false }
        );
    }
}


    //View All Spend/Receive Money
    async  importInvoices(){
        try {

        const fromDate = this.invoice_date.el?.value; // <-- updated
        const lastInvoicePage = this.last_invoice_page.el?.value ;



        if (!fromDate) {
            this.env.services.notification.add(
                "Please select Import Invoice From date",
                { type: "warning" }
            );
            return;
        }
        //  if (!lastInvoicePage) {
        //     this.env.services.notification.add(
        //         "Please enter Last Imported Invoice Page",
        //         { type: "warning" }
        //     );
        //     return;
        // }
        const response = await rpc("/web/dataset/call_kw", {
            model: "res.company",   
            method: "import_invoice",              
            args : [[]],
            kwargs: {},                               
        });

        if (response) {
            this.env.services.notification.add(
                "Import Invoices from Xero",
                { type: "success", sticky: false }
            );
        } else {
            this.env.services.notification.add(
                "Failed to import Invoices from Xero",
                { type: "danger", sticky: false}
            );
        }

    } catch (error) {
        this.env.services.notification.add(
            "Error occurred while importing Invoices",
            { type: "danger", sticky: false}
        );
    }
    }


    // Export Tracking Categories

    async exportProducts(){
        try {
        const response = await rpc("/web/dataset/call_kw", {
            model: "product.product",   // <-- CHANGE THIS to your model name
            method: "create_product_in_xero",                // Python method
            args : [],
            kwargs: {},                               // no keyword args
        });

      if (response !== false) {
            this.env.services.notification.add(
                "Products Exported successfully!",
                { type: "success", sticky: false }
            );
        } else {
            this.env.services.notification.add(
                "Failed to export Products",
                { type: "danger", sticky: false }
            );
        }

    } catch (error) {
        this.env.services.notification.add(
            "Error occurred while exporting Products",
            { type: "danger", sticky: false }
        );
    }
    }
    //Export Contacts

    async exportContacts(){
        try {
        const response = await rpc("/web/dataset/call_kw", {
            model: "res.partner",   
            method: "create_customer_in_xero",              
            args : [],
            kwargs: {},                              
        });

      if (response !== false) {
            this.env.services.notification.add(
                "Contacts exported successfully!",
                { type: "success", sticky: false }
            );
        } else {
            this.env.services.notification.add(
                "Failed to export Contacts",
                { type: "danger", sticky: false }
            );
        }

    } catch (error) {
        this.env.services.notification.add(
            "Error occurred while exporting Contacts",
            { type: "danger", sticky: false }
        );
    }
    }


    //authentication cron toggle
    async toggleAuthenticationXero() {
    const oldValue = this.state.autoAuthenticate;
    this.state.autoAuthenticate = !oldValue;

    try {
        const result = await rpc("/my/api/authentication/toggle_cron", { value: this.state.autoAuthenticate });

        if (!result.success) {
            this.state.autoAuthenticate = oldValue;
            this.notification.add(result.message, { type: "danger" });
        } else {
            this.notification.add(result.message, { type: "success" });
        }
    } catch (err) {
        console.error(err);
        this.notification.add("⚠️ Failed to toggle auto-sync.", { type: "danger" });
    }
}
async syncAuthentication() {
    try {
        this.ui.block();

        const result = await rpc("/web/dataset/call_kw", {
            model: "res.company",
            method: "refresh_token_cron",
            args: [[]],
            kwargs: {},
        });

        this.state.autoAuthenticateSync = true;

      
        if (result?.warnings?.length) {
            this.env.services.notification.add(
                result.warnings.join("\n"),
                { type: "warning", sticky: false }
            );
        }

     
        this.env.services.notification.add(
            "Token Refreshed Successfully ✅",
            { type: "success" }
        );

    } catch (error) {

    
        this.env.services.notification.add(
            "Technical error occurred while syncing invoices ⚠️",
            { type: "danger", sticky: false }
        );

        console.error("Invoice Sync Error:", error);

    } finally {
        this.ui.unblock();
    }
}
async fetchNextExecutionOfAuthentication() {
    try {
        const result = await rpc("/get/authentication/cron/next_execution", {});

        if (result.success) {
            this.state.nextExecutionTimeofAuthentication = result.next_execution;
        } else {
            this.state.nextExecutionTimeofAuthentication = "N/A";
        }

    } catch (error) {
        console.error("Error fetching cron time:", error);
        this.state.nextExecutionTimeofAuthentication = "N/A";
    }
}
//export purchase orders cron toggle
    async toggleExportPurchaseOrders() {
    const oldValue = this.state.autoExportPo;
    this.state.autoExportPo = !oldValue;

    try {
        const result = await rpc("/my/api/export/po/toggle_cron", { value: this.state.autoExportPo });

        if (!result.success) {
            this.state.autoAuthenticate = oldValue;
            this.notification.add(result.message, { type: "danger" });
        } else {
            this.notification.add(result.message, { type: "success" });
        }
    } catch (err) {
        console.error(err);
        this.notification.add("⚠️ Failed to toggle auto-sync.", { type: "danger" });
    }
}
async syncExportPo() {
    try {
        this.ui.block();

        const result = await rpc("/web/dataset/call_kw", {
            model: "purchase.order",
            method: "exportPurchaseOrder_cron",
            args: [],
            kwargs: {},
        });

        this.state.autoPoExportSync = true;

      
        if (result?.warnings?.length) {
            this.env.services.notification.add(
                result.warnings.join("\n"),
                { type: "warning", sticky: false }
            );
        }

     
        this.env.services.notification.add(
            "Purchase orders exported to xero Successfully ✅",
            { type: "success" }
        );

    } catch (error) {

    
        this.env.services.notification.add(
            "Technical error occurred while exporting Purchase Orders ⚠️",
            { type: "danger", sticky: false }
        );

        console.error("Purchase order Sync Error:", error);

    } finally {
        this.ui.unblock();
    }
}
async fetchNextExecutionOfPoExport() {
    try {
        const result = await rpc("/get/export/po/cron/next_execution", {});

        if (result.success) {
            this.state.nextExecutionTimeofPoExport = result.next_execution;
        } else {
            this.state.nextExecutionTimeofPoExport = "N/A";
        }

    } catch (error) {
        console.error("Error fetching cron time:", error);
        this.state.nextExecutionTimeofPoExport = "N/A";
    }
}
//export invoices cron 
    async toggleExportInvoices() {
    const oldValue = this.state.autoExportInvoices;
    this.state.autoExportInvoices = !oldValue;

    try {
        const result = await rpc("/my/api/invoice/export/toggle_cron", { value: this.state.autoExportInvoices });

        if (!result.success) {
            this.state.autoExportInvoices = oldValue;
            this.notification.add(result.message, { type: "danger" });
        } else {
            this.notification.add(result.message, { type: "success" });
        }
    } catch (err) {
        console.error(err);
        this.notification.add("⚠️ Failed to toggle auto-sync.", { type: "danger" });
    }
}
async syncExportInvoices() {
    try {
        this.ui.block();

        const result = await rpc("/web/dataset/call_kw", {
            model: "account.move",
            method: "exportInvoice_cron",
            args: [],
            kwargs: {},
        });

        this.state.autoInvoicesExportSync = true;

      
        if (result?.warnings?.length) {
            this.env.services.notification.add(
                result.warnings.join("\n"),
                { type: "warning", sticky: false }
            );
        }

     
        this.env.services.notification.add(
            "Invoices exported to xero Successfully ✅",
            { type: "success" }
        );

    } catch (error) {

    
        this.env.services.notification.add(
            "Technical error occurred while exporting Invoices ⚠️",
            { type: "danger", sticky: false }
        );

        console.error("Invoices  Sync Error:", error);

    } finally {
        this.ui.unblock();
    }
}
async fetchNextExecutionOfInvoiceExport() {
    try {
        const result = await rpc("/get/invoice/export/cron/next_execution", {});

        if (result.success) {
            this.state.nextExecutionTimeofInvoiceExport = result.next_execution;
        } else {
            this.state.nextExecutionTimeofInvoiceExport = "N/A";
        }

    } catch (error) {
        console.error("Error fetching cron time:", error);
        this.state.nextExecutionTimeofInvoiceExport = "N/A";
    }
}

//import payments  cron 
    async toggleImportPayments() {
    const oldValue = this.state.autoImportPayments;
    this.state.autoImportPayments = !oldValue;

    try {
        const result = await rpc("/my/api/invoice/export/toggle_cron", { value: this.state.autoImportPayments });

        if (!result.success) {
            this.state.autoExportInvoices = oldValue;
            this.notification.add(result.message, { type: "danger" });
        } else {
            this.notification.add(result.message, { type: "success" });
        }
    } catch (err) {
        console.error(err);
        this.notification.add("⚠️ Failed to toggle auto-sync.", { type: "danger" });
    }
}
async syncImportPayments() {
    try {
        this.ui.block();

        const result = await rpc("/web/dataset/call_kw", {
            model: "res.company",
            method: "import_payments_cron",
            args: [],
            kwargs: {},
        });

        this.state.autoImportPaymentsSync = true;

      
        if (result?.warnings?.length) {
            this.env.services.notification.add(
                result.warnings.join("\n"),
                { type: "warning", sticky: false }
            );
        }

     
        this.env.services.notification.add(
            "Payments imported Successfully ✅",
            { type: "success" }
        );

    } catch (error) {

    
        this.env.services.notification.add(
            "Technical error occurred while importing Invoices⚠️",
            { type: "danger", sticky: false }
        );

        console.error("Invoices  Sync Error:", error);

    } finally {
        this.ui.unblock();
    }
}
async fetchNextExecutionOfPaymentsImport() {
    try {
        const result = await rpc("/get/import/payments/cron/next_execution", {});

        if (result.success) {
            this.state.nextExecutionTimeofPaymentsImport = result.next_execution;
        } else {
            this.state.nextExecutionTimeofPaymentsImport = "N/A";
        }

    } catch (error) {
        console.error("Error fetching cron time:", error);
        this.state.nextExecutionTimeofPaymentsImport = "N/A";
    }
}

//import payments  cron 
    async toggleImportInvoices() {
    const oldValue = this.state.autoImportInvoices;
    this.state.autoImportInvoices = !oldValue;

    try {
        const result = await rpc("/my/api/import/invoices/toggle_cron", { value: this.state.autoImportInvoices });

        if (!result.success) {
            this.state.autoImportInvoices = oldValue;
            this.notification.add(result.message, { type: "danger" });
        } else {
            this.notification.add(result.message, { type: "success" });
        }
    } catch (err) {
        console.error(err);
        this.notification.add("⚠️ Failed to toggle auto-sync.", { type: "danger" });
    }
}
async syncImportInvoices() {
    try {
        this.ui.block();

        const result = await rpc("/web/dataset/call_kw", {
            model: "res.company",
            method: "import_invoice_cron",
            args: [],
            kwargs: {},
        });

        this.state.autoImportInvoicesSync = true;

      
        if (result?.warnings?.length) {
            this.env.services.notification.add(
                result.warnings.join("\n"),
                { type: "warning", sticky: false }
            );
        }

     
        this.env.services.notification.add(
            "Invoices imported from xero Successfully ✅",
            { type: "success" }
        );

    } catch (error) {

    
        this.env.services.notification.add(
            "Technical error occurred while importing Invoices ⚠️",
            { type: "danger", sticky: false }
        );

        console.error("Invoices  Sync Error:", error);

    } finally {
        this.ui.unblock();
    }
}
async fetchNextExecutionOfInvoicesImport() {
    try {
        const result = await rpc("/get/import/invoices/cron/next_execution", {});

        if (result.success) {
            this.state.nextExecutionTimeofInvoicesImport = result.next_execution;
        } else {
            this.state.nextExecutionTimeofInvoicesImport = "N/A";
        }

    } catch (error) {
        console.error("Error fetching cron time:", error);
        this.state.nextExecutionTimeofInvoicesImport = "N/A";
    }
}

//import manual journals  cron 
    async toggleImportManualJournal() {
    const oldValue = this.state.autoImportManualJournals;
    this.state.autoImportManualJournals = !oldValue;

    try {
        const result = await rpc("/my/api/import/manual/jounals/toggle_cron", { value: this.state.autoImportManualJournals });

        if (!result.success) {
            this.state.autoImportManualJournals = oldValue;
            this.notification.add(result.message, { type: "danger" });
        } else {
            this.notification.add(result.message, { type: "success" });
        }
    } catch (err) {
        console.error(err);
        this.notification.add("⚠️ Failed to toggle auto-sync.", { type: "danger" });
    }
}
async syncImportManualJournals() {
    try {
        this.ui.block();

        const result = await rpc("/web/dataset/call_kw", {
            model: "res.company",
            method: "import_manual_journal_cron",
            args: [],
            kwargs: {},
        });

        this.state.autoImportManualJournalsSync = true;

      
        if (result?.warnings?.length) {
            this.env.services.notification.add(
                result.warnings.join("\n"),
                { type: "warning", sticky: false }
            );
        }

     
        this.env.services.notification.add(
            "Manual Journals imported from xero Successfully ✅",
            { type: "success" }
        );

    } catch (error) {

    
        this.env.services.notification.add(
            "Technical error occurred while importing Manual Journals ⚠️",
            { type: "danger", sticky: false }
        );

        console.error("Manual Journals  Sync Error:", error);

    } finally {
        this.ui.unblock();
    }
}
async fetchNextExecutionOfManualJournalImport() {
    try {
        const result = await rpc("/get/import/manual/journals/cron/next_execution", {});

        if (result.success) {
            this.state.nextExecutionTimeofManualJournalsImport = result.next_execution;
        } else {
            this.state.nextExecutionTimeofManualJournalsImport = "N/A";
        }

    } catch (error) {
        console.error("Error fetching cron time:", error);
        this.state.nextExecutionTimeofManualJournalsImport = "N/A";
    }
}
//po import cron 

    async toggleImportPo() {
    const oldValue = this.state.autoImportPo;
    this.state.autoImportPo = !oldValue;

    try {
        const result = await rpc("/my/api/import/purchase/orders/toggle_cron", { value: this.state.autoImportPo });

        if (!result.success) {
            this.state.autoImportPo = oldValue;
            this.notification.add(result.message, { type: "danger" });
        } else {
            this.notification.add(result.message, { type: "success" });
        }
    } catch (err) {
        console.error(err);
        this.notification.add("⚠️ Failed to toggle auto-sync.", { type: "danger" });
    }
}
async syncImportPo() {
    try {
        this.ui.block();

        const result = await rpc("/web/dataset/call_kw", {
            model: "res.company",
            method: "import_purchase_order_cron",
            args: [],
            kwargs: {},
        });

        this.state.autoImportPoSync = true;

      
        if (result?.warnings?.length) {
            this.env.services.notification.add(
                result.warnings.join("\n"),
                { type: "warning", sticky: false }
            );
        }

     
        this.env.services.notification.add(
            "Manual Journals imported from xero Successfully ✅",
            { type: "success" }
        );

    } catch (error) {

    
        this.env.services.notification.add(
            "Technical error occurred while importing Manual Journals ⚠️",
            { type: "danger", sticky: false }
        );

        console.error("Manual Journals  Sync Error:", error);

    } finally {
        this.ui.unblock();
    }
}
async fetchNextExecutionOfPoImport() {
    try {
        const result = await rpc("/get/import/purchase/orders/next_execution", {});

        if (result.success) {
            this.state.nextExecutionTimeofPoImport = result.next_execution;
        } else {
            this.state.nextExecutionTimeofPoImport = "N/A";
        }

    } catch (error) {
        console.error("Error fetching cron time:", error);
        this.state.nextExecutionTimeofPoImport = "N/A";
    }
}
//so import cron 

    async toggleImportSo() {
    const oldValue = this.state.autoImportSo;
    this.state.autoImportSo = !oldValue;

    try {
        const result = await rpc("/my/api/import/sale/orders/toggle_cron", { value: this.state.autoImportSo });

        if (!result.success) {
            this.state.autoImportSo = oldValue;
            this.notification.add(result.message, { type: "danger" });
        } else {
            this.notification.add(result.message, { type: "success" });
        }
    } catch (err) {
        console.error(err);
        this.notification.add("⚠️ Failed to toggle auto-sync.", { type: "danger" });
    }
}
async syncImportSo() {
    try {
        // this.ui.block();

        const result = await rpc("/web/dataset/call_kw", {
            model: "res.company",
            method: "import_sale_order_cron",
            args: [],
            kwargs: {},
        });

        this.state.autoImportSoSync = true;

      
        if (result?.warnings?.length) {
            this.env.services.notification.add(
                result.warnings.join("\n"),
                { type: "warning", sticky: false }
            );
        }

     
        this.env.services.notification.add(
            "Sale Orders imported from xero Successfully ✅",
            { type: "success" }
        );

    } catch (error) {

    
        this.env.services.notification.add(
            "Technical error occurred while importing Sale Orders ⚠️",
            { type: "danger", sticky: false }
        );

        console.error("Sale order  Sync Error:", error);

    } finally {
        // this.ui.unblock();
    }
}
async fetchNextExecutionOfSoImport() {
    try {
        const result = await rpc("/get/import/sales/orders/next_execution", {});

        if (result.success) {
            this.state.nextExecutionTimeofSoImport = result.next_execution;
        } else {
            this.state.nextExecutionTimeofSoImport = "N/A";
        }

    } catch (error) {
        console.error("Error fetching cron time:", error);
        this.state.nextExecutionTimeofSoImport = "N/A";
    }
}

//payment export cron 

    async toggleExportPayments() {
    const oldValue = this.state.autoExportPayments;
    this.state.autoExportPayments = !oldValue;

    try {
        const result = await rpc("/my/api/export/payments/toggle_cron", { value: this.state.autoExportPayments });

        if (!result.success) {
            this.state.autoExportPayments = oldValue;
            this.notification.add(result.message, { type: "danger" });
        } else {
            this.notification.add(result.message, { type: "success" });
        }
    } catch (err) {
        console.error(err);
        this.notification.add("⚠️ Failed to toggle auto-sync.", { type: "danger" });
    }
}
async syncExportPayments() {
    try {
        this.ui.block();

        const result = await rpc("/web/dataset/call_kw", {
            model: "account.payment",
            method: "exportPayment_cron",
            args: [],
            kwargs: {},
        });

        this.state.autoExportPaymentsSync = true;

      
        if (result?.warnings?.length) {
            this.env.services.notification.add(
                result.warnings.join("\n"),
                { type: "warning", sticky: false }
            );
        }

     
        this.env.services.notification.add(
            "Payments Exported to  Xero Successfully ✅",
            { type: "success" }
        );

    } catch (error) {

    
        this.env.services.notification.add(
            "Technical error occurred while importing Sale Orders ⚠️",
            { type: "danger", sticky: false }
        );

        console.error("Payments Sync Error:", error);

    } finally {
        this.ui.unblock();
    }
}
async fetchNextExecutionOfPaymentExport() {
    try {
        const result = await rpc("/get/payments/export/next_execution", {});

        if (result.success) {
            this.state.nextExecutionTimeofPaymentExport = result.next_execution;
        } else {
            this.state.nextExecutionTimeofPaymentExport = "N/A";
        }

    } catch (error) {
        console.error("Error fetching cron time:", error);
        this.state.nextExecutionTimeofPaymentExport = "N/A";
    }
}
}




OrderDashboard.template = "rishvi_xero_odoo_connector.XeroImportDashboard";
registry.category("actions").add("xero_import_dashboard", OrderDashboard);
