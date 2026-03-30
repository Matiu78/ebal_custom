from odoo import models, fields, api
from odoo.exceptions import UserError

class MechanicVehicleMaintenance(models.Model):
    _name = "mechanic.vehicle.maintenance"
    _description = "Historial de Mantenimiento del Vehículo"
    _order = "mileage desc, date desc"
    _rec_name = "product_id"

    vehicle_id = fields.Many2one(
        "mechanic.vehicle",
        string="Vehículo",
        required=True,
        index=True
    )

    product_id = fields.Many2one(
        "product.product",
        string="Producto",
        required=True
    )

    workorder_id = fields.Many2one(
        "mechanic.workorder",
        string="Orden de Trabajo",
        readonly=True
    )

    mileage = fields.Integer(
        string="Kilometraje",
        required=True
    )

    next_mileage = fields.Integer(
        string="Proximo Kilometraje",
        required=True
    )

    date = fields.Date(
        string="Fecha",
        default=fields.Date.context_today
    )

    maintenance_type = fields.Selection(
        related="product_id.product_tmpl_id.maintenance_type",
        store=True
    )

    active = fields.Boolean(default=True)
