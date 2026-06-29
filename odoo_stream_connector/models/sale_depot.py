from odoo import models, fields


class StreamDepot(models.Model):
    _name = "stream.depot"
    _description = "Depot"

    # Depot
    external_id = fields.Char(
        string="Depot ID",
        required=True,
        index=True
    )

    name = fields.Char(
        string="Depot Name",
        required=True
    )

    # Address
    address1 = fields.Char()
    address2 = fields.Char()
    address3 = fields.Char()
    city = fields.Char(string="City")
    state = fields.Char(string="County")
    country = fields.Char()
    postcode = fields.Char()

    latitude = fields.Float()
    longitude = fields.Float()

    # Contact
    contact_name = fields.Char()
    phone = fields.Char()
    phone2 = fields.Char()
    mobile = fields.Char()
    email = fields.Char()

    # Stock
    stock_location_id = fields.Char(
        string="Stock Location ID"
    )

    stock_location_name = fields.Char()

 
class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    steam_delivery = fields.Many2one(
        "stream.depot.delivery.method",
        string="Stream Delivery Method"
    )
class StreamDepotDeliveryMethod(models.Model):
    _name = "stream.depot.delivery.method"
    _description = "Stream Depot Delivery Method"

    external_id = fields.Char(
        string="Delivery Method ID",
        required=True,
        index=True
    )
    steam_delivery = fields.Char(
        string="Delivery ID",
        required=True,
        index=True
    )

    name = fields.Char(
        string="Name",
        required=True
    )

    

    
    

    