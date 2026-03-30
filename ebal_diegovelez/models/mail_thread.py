from odoo import models

class MailThread(models.AbstractModel):
    _inherit = "mail.thread"

    def _compute_message_attachment_count(self):
        # primero llamar al compute original
        super()._compute_message_attachment_count()

        # filtrar solo los registros que sean órdenes de trabajo
        workorders = self.filtered(lambda r: r._name == "mechanic.workorder")
        if not workorders:
            return

        Attachment = self.env["ir.attachment"]
        Line = self.env["mechanic.workorder.attachment.line"]

        for workorder in workorders:
            # buscar los attachments relacionados
            attachments = Attachment.search([
                ("res_model", "=", "mechanic.workorder"),
                ("res_id", "=", workorder.id),
            ])

            # borrar líneas actuales
            workorder.attachment_line_ids.unlink()

            # recrear líneas
            for att in attachments:
                Line.create({
                    "workorder_id": workorder.id,
                    "attachment_id": att.id,
                })