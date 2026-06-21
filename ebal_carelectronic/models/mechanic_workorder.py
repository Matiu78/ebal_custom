import base64
import logging
from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)
class MechanicWorkorder(models.Model):
    _inherit = "mechanic.workorder"
    
    def action_send_quotation_whatsapp(self):
        self.ensure_one()

        partner = self.partner_id
        phone = partner.mobile or partner.phone
        if not phone:
            raise UserError("El cliente no tiene número de teléfono.")

        phone = phone.replace("+", "").replace(" ", "")

        currency = self.currency_id.symbol or "$"

        attachment = self._generate_public_quotation_pdf()

        # Generar PDF publico
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        pdf_url = f"{base_url}/web/content/{attachment.id}"
        workorder_url = f"{base_url}/my/workorders/{self.id}"

        lines = []
        lines.append(f"Hola {partner.name} 👋")
        lines.append("")
        lines.append("Le enviamos el detalle de su orden de trabajo, cualquier detalle que desee modificar quedamos atentos:")
        lines.append("")
        lines.append(f"📄 Orden: {self.name}")
        lines.append(f"🚗 Vehículo: {self.vehicle_id.name}")
        lines.append(f"📅 Fecha: {self.date_in}")
        lines.append("")
        lines.append("🛠️ Detalle:")

        for line in self.line_ids:
            lines.append(
                f"- {line.product_id.name} ({line.quantity}): {currency}{line.total:.2f}"
            )

        lines.append("")
        lines.append(f"💰 Total: {currency}{self.amount_order_lines}")
        lines.append("")
        lines.append("¿Está de acuerdo por favor? ✅")
        lines.append("Quedamos atentos a su confirmación, para realizar el trabajo.")
        lines.append("")
        lines.append("")
        lines.append(f"📄 Proforma (PDF): {pdf_url}")
        lines.append(f"📱 Ver Orden de Trabajo en app: {workorder_url}")
        message = "\n".join(lines)

        return self.env["whatsapp.message"].action_open_whatsapp_url(partner, message)

    def action_send_finished_whatsapp(self):
        self.ensure_one()

        partner = self.partner_id
        phone = partner.mobile or partner.phone
        if not phone:
            raise UserError("El cliente no tiene número de teléfono registrado.")

        # Normalizar teléfono
        phone = phone.replace("+", "").replace(" ", "")

        currency = self.currency_id.symbol or "$"

        # Fecha finalización
        finish_date = self.date_out or fields.Date.context_today(self)

        # =========================
        # DETALLE DE TRABAJOS
        # =========================
        detail_lines = []
        for line in self.line_ids:
            detail_lines.append(
                f"• {line.product_id.name} ({line.quantity}) — {currency}{line.total:.2f}"
            )

        detail_text = "\n".join(detail_lines) if detail_lines else "Sin detalles registrados."

        # =========================
        # MENSAJE
        # =========================
        lines = []

        lines.append(f"Hola {partner.name} 👋")
        lines.append("")
        lines.append("Nos complace informarle que los trabajos realizados en su vehículo han sido FINALIZADOS exitosamente ✅")
        lines.append("")
        lines.append(f"🚗 Vehículo: {self.vehicle_id.name}")
        lines.append(f"📄 Orden de trabajo: {self.name}")
        lines.append(f"📅 Fecha de finalización: {finish_date}")
        lines.append("")
        lines.append("🛠️ Trabajos realizados:")
        lines.append(detail_text)
        lines.append("")
        # Total orden diferente a monto en deuda
        if self.amount_order_lines != self.amount_order_due:
            lines.append(f"🧾 Total orden: {currency}{self.amount_order_lines:.2f}")
        # Total orden menos deuda
        total_amount_payment = self.amount_order_lines - self.amount_order_due
        if total_amount_payment > 0:
            lines.append(f"💵 Abonos: {currency}{total_amount_payment:.2f}")
        # Monto en deuda
        lines.append(f"💰 Saldo a pagar: {currency}{self.amount_order_due:.2f}")
        lines.append("")
        lines.append("Su vehículo se encuentra listo para entrega en nuestras instalaciones.")
        lines.append("")
        lines.append("Gracias por confiar en mecánica DIEGO VELEZ 🙌")
        lines.append("Quedamos atentos a su visita ✅")
        message = "\n".join(lines)

        # Abrir WhatsApp con mensaje prellenado
        return self.env["whatsapp.message"].action_open_whatsapp_url(partner, message)
    
    def action_open_whatsapp_files_wizard(self):
        self.ensure_one()

        return {
            "name": "Enviar archivos por WhatsApp",
            "type": "ir.actions.act_window",
            "res_model": "send.whatsapp.attachments.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_workorder_id": self.id,
            },
        }