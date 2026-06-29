from odoo import models, fields


class StreamRunDetails(models.Model):
    _name = "stream.run.details"
    _description = "Run Information Details"

    sale_order_id = fields.Many2one(
        "sale.order",
        string="Sales Order",
        required=True,
        ondelete="cascade",
    )

    # Run Information
    stream_run_id = fields.Char(string="Run ID")
    description = fields.Char(string="Description")
    group_sequence = fields.Integer(string="Group Sequence")

    # Vehicle
    vehicle = fields.Char(string="Vehicle")
    vehicle_name = fields.Char(string="Vehicle Name")
    vehicle_type = fields.Char(string="Vehicle Type")

    # Driver
    driver = fields.Char(string="Driver")
    driver_name = fields.Char(string="Driver Name")

    # Status
    dispatched = fields.Boolean(string="Dispatched")
    departed = fields.Boolean(string="Departed")
    completed = fields.Boolean(string="Completed")

    # Start
    start_actual_datetime = fields.Datetime(
        string="Start Actual Datetime"
    )
    start_planned_datetime = fields.Datetime(
        string="Start Planned Datetime"
    )
    start_postcode = fields.Char(string="Start Postcode")
    start_lat = fields.Float(string="Start Latitude")
    start_long = fields.Float(string="Start Longitude")

    # End
    end_actual_datetime = fields.Datetime(
        string="End Actual Datetime"
    )
    end_planned_datetime = fields.Datetime(
        string="End Planned Datetime"
    )
    end_postcode = fields.Char(string="End Postcode")
    end_lat = fields.Float(string="End Latitude")
    end_long = fields.Float(string="End Longitude")

    _sql_constraints = [
        (
            "unique_sale_order_run",
            "unique(sale_order_id)",
            "A Sales Order can have only one Run."
        )
    ]