import re
import logging
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)
class MechanicVehicle(models.Model):
    _name = "mechanic.vehicle"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Vehículo"

    company_id = fields.Many2one(
        "res.company",
        string="Compañía",
        required=True,
        default=lambda self: self.env.company,
        index=True
    )
    active = fields.Boolean(string="Activo", default=True)
    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id
    )
    name = fields.Char(string="Placa", required=True)
    brand_id = fields.Many2one(
        "mechanic.brand",
        string="Marca",
        required=True,
    )
    model_id = fields.Many2one(
        "mechanic.brand.model",
        string="Modelo",
        required=True,
        domain="[('brand_id', '=', brand_id)]",
    )
    year = fields.Char(string="Año")
    owner_id = fields.Many2one("res.partner", string="Propietario")
    partner_id = fields.Many2one(
        'res.partner',
        string='Cliente',
        required=True,
        index=True
    )
    partner_vat = fields.Char(related="partner_id.vat")
    mechanic_id = fields.Many2one("res.users", string="Mecánico")
    cylinder_capacity = fields.Char(string="Cilindraje")
    color = fields.Char(string="Color")
    engine_number = fields.Char(string="N° Motor")
    chassis_number = fields.Char(string="N° Chasis")
    key_code = fields.Char(string="Clave")
    image_1920 = fields.Image(string="Imagen")

    workorder_ids = fields.One2many("mechanic.workorder", "vehicle_id", string="Órdenes de Trabajo")
    workorder_count = fields.Integer(string="Órdenes de Trabajo", compute="_compute_counts")

    sale_order_ids = fields.One2many("sale.order", "vehicle_id", string="Proformas")
    sale_order_count = fields.Integer(string="Proformas", compute="_compute_counts")

    maintenance_count = fields.Integer(
        compute="_compute_maintenance_count"
    )

    ticket_ids = fields.One2many(
        "helpdesk.ticket",
        "vehicle_id",
        string="Tickets",
    )
    ticket_count = fields.Integer(
        compute="_compute_ticket_count",
        string="Tickets",
    )

    total_due_amount = fields.Monetary(
        string="Total Adeudado",
        compute="_compute_total_due_amount",
        currency_field="currency_id",
        store=True,
    )
    due_state = fields.Selection(
        selection=[
            ('paid', 'Al día'),
            ('debt', 'Con deuda'),
        ],
        string="Estado de Deuda",
        compute="_compute_debt_state",
        store=True,
        tracking=True,
    )

    has_portal_user = fields.Boolean(
        string="Tiene usuario portal",
        compute="_compute_has_portal_user",
        store=False
    )

    def _compute_has_portal_user(self):
        User = self.env['res.users']
        for rec in self:
            rec.has_portal_user = bool(
                User.search([
                    ('partner_id', '=', rec.partner_id.id),
                    ('share', '=', True)
                ], limit=1)
            )

    @api.depends('total_due_amount')
    def _compute_debt_state(self):
        for vehicle in self:
            vehicle.due_state = 'debt' if vehicle.total_due_amount > 0 else 'paid'

    @api.depends(
        'workorder_ids.amount_order_due',
    )
    def _compute_total_due_amount(self):
        for vehicle in self:

            orders_due = vehicle.workorder_ids._compute_amount_order_due()
            vehicle.total_due_amount = orders_due

    def _compute_maintenance_count(self):
        for rec in self:
            rec.maintenance_count = self.env[
                'mechanic.vehicle.maintenance'
            ].search_count([('vehicle_id', '=', rec.id)])

    @api.depends("workorder_ids", "sale_order_ids")
    def _compute_counts(self):
        for rec in self:
            rec.workorder_count = len(rec.workorder_ids)
            rec.sale_order_count = len(rec.sale_order_ids)
            rec.ticket_count = len(rec.ticket_ids)

    # ==========================
    # NORMALIZAR AUTOMÁTICAMENTE
    # ==========================
    @api.onchange('name')
    def _onchange_name_normalize_plate(self):
        if self.name:
            normalized = self._normalize_plate(self.name)
            if not self._is_valid_plate(normalized):
                    raise ValidationError(
                        "La placa debe tener al menos 2 letras y 2 números."
                    )
            self.name = normalized

    # ==========================
    # FUNCION NORMALIZAR
    # ==========================
    def _normalize_plate(self, plate):
        plate = plate.upper()
        plate = plate.replace(" ", "")
        
        # Dejar solo letras y números
        plate = re.sub(r'[^A-Z0-9]', '', plate)

        # Separar letras y números
        letters = ''.join(re.findall(r'[A-Z]+', plate))
        numbers = ''.join(re.findall(r'[0-9]+', plate))

        if not letters or not numbers:
            return plate

        return f"{letters}-{numbers}"

    # ==========================
    # VALIDACION MINIMA
    # ==========================
    def _is_valid_plate(self, plate):
        parts = plate.split('-')
        if len(parts) != 2:
            return False

        letters, numbers = parts
        if len(letters) < 2:
            return False

        if len(numbers) < 2:
            return False
        
        return True

    def action_open_workorders(self):
        self.ensure_one()
        return {
            "name": "Órdenes de Trabajo",
            "type": "ir.actions.act_window",
            "res_model": "mechanic.workorder",
            "view_mode": "list,form",
            "domain": [("vehicle_id", "=", self.id)],
            "context": {"default_vehicle_id": self.id},
        }

    def action_open_proformas(self):
        self.ensure_one()
        return {
            "name": "Proformas",
            "type": "ir.actions.act_window",
            "res_model": "sale.order",
            "view_mode": "list,form",
            "domain": [("vehicle_id", "=", self.id)],
            "context": {"default_vehicle_id": self.id},
        }

    def action_open_tickets(self):
        self.ensure_one()
        return {
            "name": "Tickets",
            "type": "ir.actions.act_window",
            "res_model": "helpdesk.ticket",
            "view_mode": "list,form",
            "domain": [("vehicle_id", "=", self.id)],
            "context": {
                "default_vehicle_id": self.id,
            },
        }

    def action_open_maintenance(self):
        self.ensure_one()
        return {
            'name': 'Mantenimientos por Kilometraje',
            'type': 'ir.actions.act_window',
            'res_model': 'mechanic.vehicle.maintenance',
            'view_mode': 'list,form',
            'domain': [('vehicle_id', '=', self.id)],
            'context': {'default_vehicle_id': self.id},
        }

    def action_open_vehicle_account_state(self):
        self.ensure_one()

        move_ids = self.workorder_ids.mapped('move_ids').ids

        return {
            'name': 'Estado de Cuenta del Vehículo',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [
                ('id', 'in', move_ids),
                ('state', '=', 'posted'),
            ],
            'context': {
                'search_default_unpaid': 1,
            }
        }

    # Botón para crear Orden de Trabajo
    def action_create_workorder(self):
        self.ensure_one()
        return {
            "name": "Nueva Orden de Trabajo",
            "type": "ir.actions.act_window",
            "res_model": "mechanic.workorder.create.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_vehicle_id": self.id,
            },
        }

    def action_create_workorder_fast(self):
        return {
            "name": "Orden Instantánea",
            "type": "ir.actions.act_window",
            "res_model": "mechanic.instant.order.wizard",
            "view_mode": "form",
            "target": "new",
        }

    # Botón para crear Proforma (Sale Order)
    def action_create_sale_order(self):
        self.ensure_one()
        sale_order = self.env["sale.order"].create({
            "partner_id": self.partner_id.id,
            "vehicle_id": self.id,
            "user_id": self.mechanic_id.id if self.mechanic_id else self.env.uid,
        })
        return {
            "name": "Proforma",
            "type": "ir.actions.act_window",
            "res_model": "sale.order",
            "view_mode": "form",
            "res_id": sale_order.id,
            "target": "current",
        }

    def action_reset_password_whatsapp(self):
        self.ensure_one()

        partner = self.partner_id
        if not partner:
            raise UserError(_("El vehículo no tiene cliente asignado."))

        # Verificar si tiene usuario
        user = self.env['res.users'].search([
            ('partner_id', '=', partner.id)
        ], limit=1)

        # Preparar signup (crea token si no existe)
        if user:
            signup_type = "reset"
            message_title = "Restablecer acceso"
        else:
            signup_type = "signup"
            message_title = "Acceso al portal"

        partner.signup_prepare(signup_type=signup_type)

        signup_url = partner._get_signup_url()
        if not signup_url:
            raise UserError(_("No se pudo generar el enlace de acceso."))

        # Mensaje WhatsApp
        lines = []
        lines.append(f"Hola {partner.name}")
        if signup_type == "reset":
            lines.append(
                f"Le compartimos la información para que pueda reestablecer su contraseña."
            )
        else:
            lines.append(
                f"Le compartimos el acceso a nuestra aplicación para que pueda revisar la información de su vehículo y órdenes de trabajo."
            )
        lines.append(f"")
        lines.append(f"🚗 Vehículo: {self.name}")
        lines.append(f"👉 Enlace: {signup_url}")
        lines.append(f"")
        lines.append(f"Si tiene alguna duda, no dude en ponerse en contacto.")
        message = "\n".join(lines)

        return self.env["whatsapp.message"].action_open_whatsapp_url(partner, message)