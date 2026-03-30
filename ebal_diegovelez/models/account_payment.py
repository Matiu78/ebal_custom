from odoo import models, fields

class AccountPayment(models.Model):
    _inherit = "account.payment"

    workorder_id = fields.Many2one(
        "mechanic.workorder",
        string="Orden de trabajo",
        ondelete="set null"
    )

    def action_post(self):
        res = super().action_post()

        for payment in self:
            if payment.workorder_id:
                payment.workorder_id.amount_paid += payment.amount

        return res