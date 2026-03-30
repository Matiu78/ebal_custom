from odoo import models, fields

class MechanicBrand(models.Model):
    _name = "mechanic.brand"
    _description = "Marca de Vehículo"

    name = fields.Char(string="Marca", required=True)
    model_ids = fields.One2many(
        "mechanic.brand.model",
        "brand_id",
        string="Modelos",
    )

class MechanicBrandModel(models.Model):
    _name = "mechanic.brand.model"
    _description = "Modelo de Vehículo"

    name = fields.Char(string="Modelo", required=True)
    brand_id = fields.Many2one(
        "mechanic.brand",
        string="Marca",
        required=True,
        ondelete="cascade",
    )
