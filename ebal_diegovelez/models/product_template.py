from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = "product.template"

    track_by_mileage = fields.Boolean(
        string="Registrar por kilometraje",
        help="Si está activo, este producto se registrará en el historial del vehículo"
    )

    maintenance_type = fields.Selection(
        [
            ('fluid', 'Líquido'),
            ('part', 'Accesorio / Repuesto'),
        ],
        string="Tipo de mantenimiento",
    )

    mileage_durability = fields.Integer(string="Durabilidad KMs")
