from odoo import models, fields

class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    vehicle_id = fields.Many2one(
        "mechanic.vehicle",
        string="Vehículo",
        index=True,
        tracking=True,
    )

    workorder_id = fields.Many2one(
        "mechanic.workorder",
        string="Orden de Trabajo",
        index=True,
    )
