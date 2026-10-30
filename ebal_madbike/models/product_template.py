# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    gala_state = fields.Selection(
        [("in_stock", "Hay en Gala"), ("out_of_stock", "Agotado en Gala")],
        string="Disponibilidad en Gala", copy=False, readonly=True,
        help="Lo que dice la web de Gala Importaciones (INGCO/WADFOW) en la última sincronización.")
    gala_qty = fields.Integer(string="Stock en Gala", copy=False, readonly=True)
    gala_price = fields.Float(string="Precio web Gala", copy=False, readonly=True, digits=(16, 4))
    gala_synced_at = fields.Datetime(string="Última sincronización Gala", copy=False, readonly=True)
    ebal_availability = fields.Selection(
        [("available", "Disponible"), ("unavailable", "No disponible")],
        compute="_compute_ebal_availability",
        help="Disponible si hay stock propio o si Gala lo tiene. Vacío si el producto no está ligado a Gala.")

    @api.depends("gala_state", "qty_available")
    def _compute_ebal_availability(self):
        for tmpl in self:
            if not tmpl.gala_state:
                tmpl.ebal_availability = False
            elif tmpl.gala_state == "in_stock" or tmpl.qty_available > 0:
                tmpl.ebal_availability = "available"
            else:
                tmpl.ebal_availability = "unavailable"
