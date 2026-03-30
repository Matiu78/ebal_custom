from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = "sale.order"

    vehicle_id = fields.Many2one("mechanic.vehicle", string="Vehículo")
    workorder_id = fields.Many2one("mechanic.workorder", string="Orden de Trabajo", readonly=True)

    def action_create_workorder(self):
        for order in self:
            # Si ya tiene una orden de trabajo, no creamos otra
            if order.workorder_id:
                continue

            workorder = self.env["mechanic.workorder"].create({
                "vehicle_id": order.vehicle_id.id,
                "mechanic_id": order.user_id.id,
                "line_ids": [
                    (0, 0, {
                        "product_id": line.product_id.id,
                        "quantity": line.product_uom_qty
                    })
                    for line in order.order_line
                ],
                "origin": order.name,
            })

            # Guardar la relación en el pedido
            order.workorder_id = workorder.id

        return True
