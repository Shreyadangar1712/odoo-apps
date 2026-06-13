import base64
import logging
import requests
import json
from odoo import http, _
from datetime import datetime, timedelta
from odoo import fields
from odoo.http import request

_logger = logging.getLogger(__name__)


class AuthenticationXero(http.Controller):

    @http.route('/authenticate_code', type="http", auth="public", website=True)
    def authenticate_code(self, **kwargs):

        authorization_code = kwargs.get('code')

        if authorization_code:
            token_endpoint = 'https://identity.xero.com/connect/token'

            company = (
                http.request.env['res.users']
                .search([('id', '=', http.request.uid)], limit=1)
                .company_id
            )

            client_id = company.xero_client_id
            client_secret = company.xero_client_secret
            redirect_uri = company.xero_redirect_url 

            credentials = f"{client_id}:{client_secret}"
            encoded_credentials = base64.b64encode(
                credentials.encode("utf-8")
            ).decode("utf-8")

            token_headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Authorization': f"Basic {encoded_credentials}"
            }

            token_payload = {
                'code': authorization_code,
                'redirect_uri': redirect_uri,
                'grant_type': 'authorization_code'
            }

            _logger.info("CLIENT ID: %s", client_id)
            _logger.info("COMPANY: %s", company.name)

            token_response = requests.post(
                token_endpoint,
                data=token_payload,
                headers=token_headers,
                verify=False
            )

            if token_response:
                token_data = token_response.json()

                if token_data:
                    company.write({
                        'xero_oauth_token': token_data.get('access_token'),
                        'refresh_token_xero': token_data.get('refresh_token'),
                    })

                connection_headers = {
                    'Authorization': f"Bearer {company.xero_oauth_token}",
                    'Content-Type': 'application/json'
                }

                tenant_response = requests.get(
                    'https://api.xero.com/connections',
                    headers=connection_headers
                )

                tenant_data = tenant_response.json()

                if tenant_data:
                    for tenant in tenant_data:
                        if tenant.get('tenantId'):
                            company.xero_tenant_id = tenant.get('tenantId')
                            company.xero_tenant_name = tenant.get('tenantName')

                    _logger.info(_("Authorization successful!"))

                    country_name = company.import_organization()

                    company.write({
                        'xero_country_name': country_name
                    })

        return "Authentication successful. You can now close this window."
    

     #Authentication cron

    @http.route('/my/api/authentication/toggle_cron', type='json', auth='user')
    def toggle_authentication_cron(self, value=False):
        """
        Toggle Rishvi authentication cron ON/OFF
        """
        try:
            cron = request.env.ref(
                'rishvi_xero_odoo_connector.ir_cron_xero_authentication_refresh_token'
            ).sudo()

            cron.write({
                'active': bool(value)
            })

            return {
                "success": True,
                "active": cron.active,
                "message": "Auto sync enabled" if cron.active else "Auto sync disabled"
            }

        except Exception as e:
            _logger.exception("❌ Failed to toggle cron")
            return {
                "success": False,
                "message": str(e)
            }
        

    @http.route('/my/api/authentication/get_cron_status', type='json', auth='user')
    def get_xero_authentication_cron_status(self):
        """
        Get Rishvi authentication Get cron active status
        """
        try:
            cron = request.env.ref(
                'rishvi_xero_odoo_connector.ir_cron_xero_authentication_refresh_token'
            ).sudo()
            _logger.info(f"🔍 Cron active status: {cron.active}")
 
            return {
                "success": True,
                "active": cron.active
            }
 
        except Exception as e:
            _logger.exception("❌ Failed to get cron status")
            return {
                "success": False,
                "message": str(e)
            }
        

    @http.route('/get/authentication/cron/next_execution', type='json', auth='user')
    def get_authentication_next_execution(self):
        cron = request.env.ref(
            'rishvi_xero_odoo_connector.ir_cron_xero_authentication_refresh_token'
        ).sudo()

        if cron.nextcall:
        # Convert UTC → User timezone
            nextcall = fields.Datetime.context_timestamp(cron, cron.nextcall)

            # Format as MM/DD/YYYY
            formatted = nextcall.strftime('%m/%d/%Y %H:%M:%S')

            return {
                'success': True,
                'next_execution': formatted
            }

        return {
            'success': False,
            'next_execution': None
        }
    


    # export purchase orders to xero cron 
    @http.route('/my/api/export/po/toggle_cron', type='json', auth='user')
    def toggle_invoice_weekly_sync_cron(self, value=False):
        
        try:
            cron = request.env.ref(
                'rishvi_xero_odoo_connector.ir_cron_xero_purchase_order'
            ).sudo()

            cron.write({
                'active': bool(value)
            })

            return {
                "success": True,
                "active": cron.active,
                "message": "Auto sync enabled" if cron.active else "Auto sync disabled"
            }

        except Exception as e:
            _logger.exception("❌ Failed to toggle cron")
            return {
                "success": False,
                "message": str(e)
            }
        

    @http.route('/my/api/export/po/get_cron_status', type='json', auth='user')
    def get_export_po_cron_status(self):
        
        try:
            cron = request.env.ref(
                'rishvi_xero_odoo_connector.ir_cron_xero_purchase_order'
            ).sudo()
            _logger.info(f"🔍 Cron active status: {cron.active}")
 
            return {
                "success": True,
                "active": cron.active
            }
 
        except Exception as e:
            _logger.exception("❌ Failed to get cron status")
            return {
                "success": False,
                "message": str(e)
            }
        

    @http.route('/get/export/po/cron/next_execution', type='json', auth='user')
    def get_export_po_cron_next_execution(self):
        cron = request.env.ref(
            'rishvi_xero_odoo_connector.ir_cron_xero_purchase_order'
        ).sudo()

        if cron.nextcall:
        # Convert UTC → User timezone
            nextcall = fields.Datetime.context_timestamp(cron, cron.nextcall)

            # Format as MM/DD/YYYY
            formatted = nextcall.strftime('%m/%d/%Y %H:%M:%S')

            return {
                'success': True,
                'next_execution': formatted
            }

        return {
            'success': False,
            'next_execution': None
        }
    

    #Invoice/Journal export to xero cron
    @http.route('/my/api/invoice/export/toggle_cron', type='json', auth='user')
    def toggle_invoice_export_cron_toggle(self, value=False):
        
        try:
            cron = request.env.ref(
                'rishvi_xero_odoo_connector.ir_cron_xero_Invoice_order'
            ).sudo()

            cron.write({
                'active': bool(value)
            })

            return {
                "success": True,
                "active": cron.active,
                "message": "Auto sync enabled" if cron.active else "Auto sync disabled"
            }

        except Exception as e:
            _logger.exception("❌ Failed to toggle cron")
            return {
                "success": False,
                "message": str(e)
            }
        

    @http.route('/my/api/invoices/export/get_cron_status', type='json', auth='user')
    def get_invoice_export_cron_status(self):
        
        try:
            cron = request.env.ref(
                'rishvi_xero_odoo_connector.ir_cron_xero_Invoice_order'
            ).sudo()
            _logger.info(f"🔍 Cron active status: {cron.active}")
 
            return {
                "success": True,
                "active": cron.active
            }
 
        except Exception as e:
            _logger.exception("❌ Failed to get cron status")
            return {
                "success": False,
                "message": str(e)
            }
        

    @http.route('/get/invoice/export/cron/next_execution', type='json', auth='user')
    def get_cron_invoice_export_next_execution(self):
        cron = request.env.ref(
            'rishvi_xero_odoo_connector.ir_cron_xero_Invoice_order'
        ).sudo()

        if cron.nextcall:
        # Convert UTC → User timezone
            nextcall = fields.Datetime.context_timestamp(cron, cron.nextcall)

            # Format as MM/DD/YYYY
            formatted = nextcall.strftime('%m/%d/%Y %H:%M:%S')

            return {
                'success': True,
                'next_execution': formatted
            }

        return {
            'success': False,
            'next_execution': None
        }
    

    #import payments from xero cron
    
    @http.route('/my/api/import/payments/toggle_cron', type='json', auth='user')
    def toggle_import_payments_cron(self, value=False):
        
        try:
            cron = request.env.ref(
                'rishvi_xero_odoo_connector.ir_cron_xero_payement_import'
            ).sudo()

            cron.write({
                'active': bool(value)
            })

            return {
                "success": True,
                "active": cron.active,
                "message": "Auto sync enabled" if cron.active else "Auto sync disabled"
            }

        except Exception as e:
            _logger.exception("❌ Failed to toggle cron")
            return {
                "success": False,
                "message": str(e)
            }
        

    @http.route('/my/api/import/payments/get_cron_status', type='json', auth='user')
    def get_import_payments_cron_status(self):
        
        try:
            cron = request.env.ref(
                'rishvi_xero_odoo_connector.ir_cron_xero_payement_import'
            ).sudo()
            _logger.info(f"🔍 Cron active status: {cron.active}")
 
            return {
                "success": True,
                "active": cron.active
            }
 
        except Exception as e:
            _logger.exception("❌ Failed to get cron status")
            return {
                "success": False,
                "message": str(e)
            }
        

    @http.route('/get/import/payments/cron/next_execution', type='json', auth='user')
    def get_import_payments_cron_next_execution(self):
        cron = request.env.ref(
            'rishvi_xero_odoo_connector.ir_cron_xero_payement_import'
        ).sudo()

        if cron.nextcall:
        # Convert UTC → User timezone
            nextcall = fields.Datetime.context_timestamp(cron, cron.nextcall)

            # Format as MM/DD/YYYY
            formatted = nextcall.strftime('%m/%d/%Y %H:%M:%S')

            return {
                'success': True,
                'next_execution': formatted
            }

        return {
            'success': False,
            'next_execution': None
        }
    

    #import invoices from xero cron 
    
    @http.route('/my/api/import/invoices/toggle_cron', type='json', auth='user')
    def toggle_import_invoices_sync_cron(self, value=False):
        
        try:
            cron = request.env.ref(
                'rishvi_xero_odoo_connector.ir_cron_xero_invoice_import'
            ).sudo()

            cron.write({
                'active': bool(value)
            })

            return {
                "success": True,
                "active": cron.active,
                "message": "Auto sync enabled" if cron.active else "Auto sync disabled"
            }

        except Exception as e:
            _logger.exception("❌ Failed to toggle cron")
            return {
                "success": False,
                "message": str(e)
            }
        

    @http.route('/my/api/import/invoices/get_cron_status', type='json', auth='user')
    def get_import_invoices_cron_status(self):
       
        try:
            cron = request.env.ref(
                'rishvi_xero_odoo_connector.ir_cron_xero_invoice_import'
            ).sudo()
            _logger.info(f"🔍 Cron active status: {cron.active}")
 
            return {
                "success": True,
                "active": cron.active
            }
 
        except Exception as e:
            _logger.exception("❌ Failed to get cron status")
            return {
                "success": False,
                "message": str(e)
            }
        

    @http.route('/get/import/invoices/cron/next_execution', type='json', auth='user')
    def get_import_invoices_next_execution_weekly(self):
        cron = request.env.ref(
            'rishvi_xero_odoo_connector.ir_cron_xero_invoice_import'
        ).sudo()

        if cron.nextcall:
        # Convert UTC → User timezone
            nextcall = fields.Datetime.context_timestamp(cron, cron.nextcall)

            # Format as MM/DD/YYYY
            formatted = nextcall.strftime('%m/%d/%Y %H:%M:%S')

            return {
                'success': True,
                'next_execution': formatted
            }

        return {
            'success': False,
            'next_execution': None
        }


#import manual journals from xero cron

    
    @http.route('/my/api/import/manual/jounals/toggle_cron', type='json', auth='user')
    def toggle_import_manual_journals_sync_cron(self, value=False):
       
        try:
            cron = request.env.ref(
                'rishvi_xero_odoo_connector.ir_cron_xero_manual_journal_import'
            ).sudo()

            cron.write({
                'active': bool(value)
            })

            return {
                "success": True,
                "active": cron.active,
                "message": "Auto sync enabled" if cron.active else "Auto sync disabled"
            }

        except Exception as e:
            _logger.exception("❌ Failed to toggle cron")
            return {
                "success": False,
                "message": str(e)
            }
        

    @http.route('/my/api/import/manual/journals/get_cron_status', type='json', auth='user')
    def get_import_manual_journals_cron_status(self):
        
        try:
            cron = request.env.ref(
                'rishvi_xero_odoo_connector.ir_cron_xero_manual_journal_import'
            ).sudo()
            _logger.info(f"🔍 Cron active status: {cron.active}")
 
            return {
                "success": True,
                "active": cron.active
            }
 
        except Exception as e:
            _logger.exception("❌ Failed to get cron status")
            return {
                "success": False,
                "message": str(e)
            }
        

    @http.route('/get/import/manual/journals/cron/next_execution', type='json', auth='user')
    def get_import_manual_journals_next_execution(self):
        cron = request.env.ref(
            'rishvi_xero_odoo_connector.ir_cron_xero_manual_journal_import'
        ).sudo()

        if cron.nextcall:
        # Convert UTC → User timezone
            nextcall = fields.Datetime.context_timestamp(cron, cron.nextcall)

            # Format as MM/DD/YYYY
            formatted = nextcall.strftime('%m/%d/%Y %H:%M:%S')

            return {
                'success': True,
                'next_execution': formatted
            }

        return {
            'success': False,
            'next_execution': None
        }
    



#IMport purchase orders from xero cron



    
    @http.route('/my/api/import/purchase/orders/toggle_cron', type='json', auth='user')
    def toggle_import_purchase_orders_cron(self, value=False):
       
        try:
            cron = request.env.ref(
                'rishvi_xero_odoo_connector.ir_cron_xero_purchase_order_import'
            ).sudo()

            cron.write({
                'active': bool(value)
            })

            return {
                "success": True,
                "active": cron.active,
                "message": "Auto sync enabled" if cron.active else "Auto sync disabled"
            }

        except Exception as e:
            _logger.exception("❌ Failed to toggle cron")
            return {
                "success": False,
                "message": str(e)
            }
        

    @http.route('/my/api/import/purchase/orders/get_cron_status', type='json', auth='user')
    def get_import_purchase_orders_cron_status(self):
       
        try:
            cron = request.env.ref(
                'rishvi_xero_odoo_connector.ir_cron_xero_purchase_order_import'
            ).sudo()
            _logger.info(f"🔍 Cron active status: {cron.active}")
 
            return {
                "success": True,
                "active": cron.active
            }
 
        except Exception as e:
            _logger.exception("❌ Failed to get cron status")
            return {
                "success": False,
                "message": str(e)
            }
        

    @http.route('/get/import/purchase/orders/next_execution', type='json', auth='user')
    def get_import_po_next_execution(self):
        cron = request.env.ref(
            'rishvi_xero_odoo_connector.ir_cron_xero_purchase_order_import'
        ).sudo()

        if cron.nextcall:
        # Convert UTC → User timezone
            nextcall = fields.Datetime.context_timestamp(cron, cron.nextcall)

            # Format as MM/DD/YYYY
            formatted = nextcall.strftime('%m/%d/%Y %H:%M:%S')

            return {
                'success': True,
                'next_execution': formatted
            }

        return {
            'success': False,
            'next_execution': None
        }








#IMport sale  orders from xero cron



    
    @http.route('/my/api/import/sale/orders/toggle_cron', type='json', auth='user')
    def toggle_import_sale_orders_cron(self, value=False):
       
        try:
            cron = request.env.ref(
                'rishvi_xero_odoo_connector.ir_cron_xero_sale_order_import'
            ).sudo()

            cron.write({
                'active': bool(value)
            })

            return {
                "success": True,
                "active": cron.active,
                "message": "Auto sync enabled" if cron.active else "Auto sync disabled"
            }

        except Exception as e:
            _logger.exception("❌ Failed to toggle cron")
            return {
                "success": False,
                "message": str(e)
            }
        

    @http.route('/my/api/import/sales/orders/get_cron_status', type='json', auth='user')
    def get_import_sale_orders_cron_status(self):
       
        try:
            cron = request.env.ref(
                'rishvi_xero_odoo_connector.ir_cron_xero_sale_order_import'
            ).sudo()
            _logger.info(f"🔍 Cron active status: {cron.active}")
 
            return {
                "success": True,
                "active": cron.active
            }
 
        except Exception as e:
            _logger.exception("❌ Failed to get cron status")
            return {
                "success": False,
                "message": str(e)
            }
        

    @http.route('/get/import/sales/orders/next_execution', type='json', auth='user')
    def get_import_so_next_execution(self):
        cron = request.env.ref(
            'rishvi_xero_odoo_connector.ir_cron_xero_sale_order_import'
        ).sudo()

        if cron.nextcall:
        # Convert UTC → User timezone
            nextcall = fields.Datetime.context_timestamp(cron, cron.nextcall)

            # Format as MM/DD/YYYY
            formatted = nextcall.strftime('%m/%d/%Y %H:%M:%S')

            return {
                'success': True,
                'next_execution': formatted
            }

        return {
            'success': False,
            'next_execution': None
        }





#payments export to xero cron



    
    @http.route('/my/api/export/payments/toggle_cron', type='json', auth='user')
    def toggle_export_payments_cron(self, value=False):
       
        try:
            cron = request.env.ref(
                'rishvi_xero_odoo_connector.ir_cron_xero_payment_export'
            ).sudo()

            cron.write({
                'active': bool(value)
            })

            return {
                "success": True,
                "active": cron.active,
                "message": "Auto sync enabled" if cron.active else "Auto sync disabled"
            }

        except Exception as e:
            _logger.exception("❌ Failed to toggle cron")
            return {
                "success": False,
                "message": str(e)
            }
        

    @http.route('/my/api/payments/export/get_cron_status', type='json', auth='user')
    def get_export_payments_cron_status(self):
       
        try:
            cron = request.env.ref(
                'rishvi_xero_odoo_connector.ir_cron_xero_payment_export'
            ).sudo()
            _logger.info(f"🔍 Cron active status: {cron.active}")
 
            return {
                "success": True,
                "active": cron.active
            }
 
        except Exception as e:
            _logger.exception("❌ Failed to get cron status")
            return {
                "success": False,
                "message": str(e)
            }
        

    @http.route('/get/payments/export/next_execution', type='json', auth='user')
    def get_export_payments_next_execution(self):
        cron = request.env.ref(
            'rishvi_xero_odoo_connector.ir_cron_xero_payment_export'
        ).sudo()

        if cron.nextcall:
        # Convert UTC → User timezone
            nextcall = fields.Datetime.context_timestamp(cron, cron.nextcall)

            # Format as MM/DD/YYYY
            formatted = nextcall.strftime('%m/%d/%Y %H:%M:%S')

            return {
                'success': True,
                'next_execution': formatted
            }

        return {
            'success': False,
            'next_execution': None
        }













