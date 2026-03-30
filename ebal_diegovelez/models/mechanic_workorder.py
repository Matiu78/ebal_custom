import base64
import logging
from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)
class MechanicWorkorder(models.Model):
    _name = "mechanic.workorder"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Orden de trabajo"

    # Campos generales orden
    company_id = fields.Many2one(
        "res.company",
        string="Compañía",
        required=True,
        default=lambda self: self.env.company,
        index=True
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Moneda',
        default=lambda self: self.env.company.currency_id
    )
    active = fields.Boolean(
        string="Activo",
        default=True
    )
    state = fields.Selection(
        [("draft", "En proceso"), ("done", "Finalizado"), ("cancel", "Cancelado")],
        string="Estado",
        default="draft",
        tracking=True,
    )

    # Fechas orden
    date_in = fields.Date(
        string="Fecha de ingreso",
        default=fields.Date.context_today,
        tracking=True
    )
    date_out = fields.Date(string="Fecha de entrega")
    
    # Datos cliente/vehiculo
    name = fields.Char(string="Referencia", required=True)
    partner_id = fields.Many2one("res.partner", string="Cliente", related="vehicle_id.partner_id")
    vehicle_id = fields.Many2one("mechanic.vehicle", string="Vehículo", required=True)
    mechanic_id = fields.Many2one("res.users", string="Mecánico")
    plate = fields.Char(
        string="Placa",
        related="vehicle_id.name",
        store=True,
        readonly=True
    )
    brand = fields.Many2one(
        related="vehicle_id.brand_id",
        string="Marca",
        store=True
    )
    model = fields.Many2one(
        related="vehicle_id.model_id",
        string="Modelo",
        store=True
    )
    color = fields.Char(
        string="Color",
        related="vehicle_id.color",
        store=True,
        readonly=True
    )
    engine_number = fields.Char(
        string="N° Motor",
        related="vehicle_id.engine_number",
        store=True,
        readonly=True
    )
    chassis_number = fields.Char(
        string="N° Chasis",
        related="vehicle_id.chassis_number",
        store=True,
        readonly=True
    )
    key_code = fields.Char(
        string="Clave",
        related="vehicle_id.key_code",
        store=True,
        readonly=True
    )
    mileage = fields.Integer(
        string="Kilometraje del vehículo",
        required=True,
        tracking=True,
    )
    fuel_level = fields.Selection([
        ('e', 'E'),
        ('1/4', '1/4'),
        ('1/2', '1/2'),
        ('3/4', '3/4'),
        ('f', 'F'),
    ], string="Nivel de Combustible")
    
    problem_reported = fields.Text(
        string='Problemas Reportados'
    )
    possible_cause = fields.Text(
        string='Causa Posible'
    )
    solution = fields.Text(
        string='Solución'
    )
    observations = fields.Text(
        string="Observaciones detectadas",
        tracking=True,
    )
    
    # Inventario vehiculo
    chk_radio = fields.Boolean(string="Radio")
    chk_plumas = fields.Boolean(string="Plumas")
    chk_encendedor = fields.Boolean(string="Encendedor")
    chk_tapacubos = fields.Boolean(string="Tapacubos")
    chk_brazos = fields.Boolean(string="Brazos")
    chk_moquetas = fields.Boolean(string="Moquetas")
    chk_tapa_gasolina = fields.Boolean(string="Tapa Gasolina")
    chk_antena = fields.Boolean(string="Antena")
    chk_emblemas = fields.Boolean(string="Emblemas")
    chk_espejos = fields.Boolean(string="Espejos")
    chk_llave_ruedas = fields.Boolean(string="Llave de Ruedas")
    chk_gata = fields.Boolean(string="Gata")
    chk_lamparas_post = fields.Boolean(string="Lámparas Posteriores")
    chk_lamparas_front = fields.Boolean(string="Lámparas Frontales")
    chk_herramientas = fields.Boolean(string="Herramientas")
    chk_llanta_emergencia = fields.Boolean(string="Llanta de Emergencia")
    chk_direccionales = fields.Boolean(string="Direccionales")
    chk_gafas = fields.Boolean(string="Gafas")
    chk_cassettes = fields.Boolean(string="Cassettes")
    chk_cd = fields.Boolean(string="CD")

    # Creditos cliente
    payment_ids = fields.One2many(
        "account.payment",
        "workorder_id",
        string="Pagos"
    )
    amount_payments = fields.Monetary(
        string="Abonos",
        compute="_compute_amount_payments",
        currency_field="currency_id"
    )
    discount_ids = fields.One2many(
        "mechanic.workorder.discount",
        "workorder_id",
        string="Descuentos"
    )
    discount = fields.Monetary(
        string="Descuento",
        currency_field="currency_id"
    )
    amount_discounts = fields.Monetary(
        string="Descuentos",
        compute="_compute_amount_discounts",
        currency_field="currency_id"
    )

    # Deudas cliente
    move_ids = fields.Many2many(
        'account.move',
        'mechanic_workorder_account_move_rel',
        'workorder_id',
        'move_id',
        string='Facturas / Recibos',
        readonly=True,
    )
    moves_count = fields.Integer(
        string="Número Fácturas Recibos",
        compute="_compute_amount_moves_due",
        store=True,
    )
    amount_moves_due = fields.Monetary(
        string='Comprobantes',
        compute='_compute_amount_moves_due',
        currency_field="currency_id"
    )
    amount_order_lines = fields.Monetary(
        string="Total Orden",
        compute="_compute_amount_order_lines",
        store=True,
        currency_field="currency_id"
    )
    amount_order_lines_due = fields.Monetary(
        string="Total Deuda Líneas Orden",
        compute="_compute_amount_order_lines",
        store=True,
        currency_field="currency_id"
    )

    # Estado de cuenta
    amount_order_due = fields.Monetary(
        string="Deuda Total Orden",
        compute="_compute_amount_order_due",
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
    
    # Ganancia
    cost_total = fields.Monetary(
        string="Costo Total",
        compute="_compute_cost_margin",
        store=True,
        currency_field="currency_id"
    )
    margin = fields.Monetary(
        string="Ganancia",
        compute="_compute_cost_margin",
        store=True,
        currency_field="currency_id"
    )

    # Tickets
    ticket_ids = fields.One2many(
        "helpdesk.ticket",
        "workorder_id",
        string="Tickets",
    )
    ticket_count = fields.Integer(
        compute="_compute_ticket_count",
        string="Tickets",
    )

    # Detalles orden
    line_ids = fields.One2many("mechanic.workorder.line", "workorder_id", string="Detalles")
    has_lines_to_invoice = fields.Boolean(
        string="Tiene líneas para facturar",
        compute="_compute_has_lines_to_invoice",
        store=False
    )

    # Borrar
    amount_moves = fields.Monetary(
        string='Comprobantes',
        currency_field="currency_id"
    )
    amount_total = fields.Monetary(
        string="Total",
        store=True,
        currency_field="currency_id"
    )
    amount_paid = fields.Monetary(
        string="Abona",
        currency_field="currency_id"
    )
    total_order_amount = fields.Monetary(
        string="Total Orden",
        store=True,
        currency_field="currency_id"
    )
    total_due_amount = fields.Monetary(
        string="Total Adeudado",
        currency_field="currency_id",
    )
    amount_discount = fields.Monetary(
        string="Descuento",
        currency_field="currency_id"
    )

    def write(self, vals):
        # 1. Manejar date_out ANTES del write
        if vals.get('state') == 'done':
            for rec in self:
                if not rec.date_out and not vals.get('date_out'):
                    vals['date_out'] = fields.Date.context_today(self)

        # 2. Guardar primero
        res = super().write(vals)

        # 3. Aplicar descuento
        if 'discount' in vals:
            for rec in self:
                rec._apply_discount_to_lines()

        return res

    @api.depends('line_ids.is_invoiced')
    def _compute_has_lines_to_invoice(self):
        for rec in self:
            rec.has_lines_to_invoice = any(
                not l.is_invoiced for l in rec.line_ids
            )
    
    @api.depends(
        "line_ids.is_invoiced",
        "line_ids.total"
    )
    def _compute_amount_order_lines(self):
        for rec in self:
            rec.amount_order_lines = sum(line.total for line in rec.line_ids)
            rec.amount_order_lines_due = sum(
                line.total for line in rec.line_ids if not line.is_invoiced
            )

    # Obtener monto total lineas
    @api.depends(
        'line_ids.quantity',
        'line_ids.price_unit',
        'line_ids.product_id.standard_price',
    )
    def _compute_cost_margin(self):
        for rec in self:
            cost = 0.0
            revenue = 0.0

            for line in rec.line_ids:
                revenue += line.quantity * line.price_unit

                # Solo productos generan costo
                if line.product_id.type != 'service':
                    cost += line.quantity * (line.product_id.standard_price or 0.0)

            rec.cost_total = cost
            rec.margin = revenue - cost

    # Obtener numero de tickets
    def _compute_ticket_count(self):
        for rec in self:
            rec.ticket_count = len(rec.ticket_ids)

    # Calcular monto en abonos
    @api.depends("payment_ids.amount", "payment_ids.is_reconciled")
    def _compute_amount_payments(self):
        for rec in self:
            payments = rec.payment_ids.filtered(
                lambda p: p.state in ['in_process', 'paid'] and not p.is_reconciled
            )
            rec.amount_payments = sum(payments.mapped("amount"))

    # Calcular monto en facturas recibos
    @api.depends(
        'move_ids.amount_residual',
        'move_ids.payment_state',
        'move_ids.state',
    )
    def _compute_amount_moves_due(self):
        for rec in self:

            # TODAS las facturas (borrador + publicadas)
            all_moves = rec.move_ids.filtered(
                lambda m: m.move_type in ('out_invoice', 'out_receipt')
            )

            rec.moves_count = len(all_moves)

            # SOLO las que afectan deuda
            debt_moves = all_moves.filtered(
                lambda m: m.state == 'posted' and m.payment_state in ('not_paid', 'partial')
            )

            rec.amount_moves_due = sum(debt_moves.mapped('amount_residual'))

    # Calcular monto descuentos
    @api.depends("discount_ids.amount")
    def _compute_amount_discounts(self):
        for rec in self:
            rec.amount_discounts = sum(rec.discount_ids.mapped("amount"))

    # Calcular monto en deuda
    @api.depends(
        'amount_order_lines_due',
        'amount_moves_due',
        'amount_payments',
    )
    def _compute_amount_order_due(self):
        amount_orders_due = 0
        for rec in self:
            order_due = (
                rec.amount_moves_due + rec.amount_order_lines_due - rec.amount_payments
            )
            rec.amount_order_due = order_due
            amount_orders_due += order_due
        return amount_orders_due
    
    # Estado de deuda
    @api.depends('amount_order_due')
    def _compute_debt_state(self):
        for workorder in self:
            workorder.due_state = 'debt' if workorder.amount_order_due > 0 else 'paid'

    @api.onchange('discount', 'line_ids')
    def _onchange_discount(self):
        for rec in self:
            rec._apply_discount_to_lines()
    
    # Metodos ordenes de trabajo
    def _check_services_have_mechanics(self, lines):
        """
        No permitir facturar servicios sin mecánico asignado
        """
        service_without_mechanic = lines.filtered(
            lambda l: l.product_id.type == 'service' and not l.product_id.third_party_service and not l.mechanic_ids
        )

        if service_without_mechanic:
            products = ", ".join(
                service_without_mechanic.mapped('product_id.name')
            )

            raise UserError(
                f"Los siguientes servicios no tienen mecánico asignado:\n{products}"
            )

    def _get_lines_to_invoice(self):
        return self.line_ids.filtered(lambda l: not l.is_invoiced)
    
    def _split_invoice_and_receipt_lines(self, lines):
        invoice_lines = lines.filtered(lambda l: not l.product_id.product_tmpl_id.not_invoice)
        receipt_lines = lines.filtered(lambda l: l.product_id.product_tmpl_id.not_invoice)
        return invoice_lines, receipt_lines

    def _split_lines_by_type(self, lines):
        service_lines = lines.filtered(lambda l: l.product_id.type == 'service')
        product_lines = lines.filtered(lambda l: l.product_id.type != 'service')
        return service_lines, product_lines

    def _apply_discount_to_lines(self):
        for rec in self:
            lines = rec.line_ids.filtered(lambda l: not l.is_invoiced)

            if not lines:
                continue

            # Calcular total de las líneas sin descuento
            total = sum(l.quantity * l.price_unit for l in lines)
            workorder_discount = rec.discount
            total_with_discount = total - workorder_discount

            if total <= 0 or workorder_discount < 0:
                continue

            total_with_discount_prorrated = 0
            for line in lines:
                # Subtotal linea
                line_subtotal = line.quantity * line.price_unit
                # Calcular proporción de descuento para la línea
                proportion = line_subtotal / total
                # Calcular descuento para la linea
                line_discount = round(workorder_discount * proportion, 2)
                line.discount = line_discount
                # Sumar al total con descuento prorrateado
                applied_discount = round(line_subtotal - line_discount, 2)
                total_with_discount_prorrated = round(total_with_discount_prorrated + applied_discount, 2)

            # Ajustar diferencia de redondeo en la última línea
            difference = total_with_discount - total_with_discount_prorrated
            if abs(difference) > 0:
                lines[-1].discount -= difference
    
    def _register_discount_history(self, moves):
        for rec in self:
            if not rec.discount:
                continue

            self.env['mechanic.workorder.discount'].create({
                'workorder_id': rec.id,
                'amount': rec.discount,
                'currency_id': rec.currency_id.id,
                'date': fields.Datetime.now(),
                'description': f"Descuento aplicado en orden {rec.name}",
                'move_ids': [(6, 0, moves.ids)],
            })

            rec.discount = 0.0
    
    # Obtener diarios correspondientes a cada compañía
    def get_invoice_journal(self, company):
        journal = self.env['user.account.journal'].search(
            [('user_id', '=', self.env.user.id), ('company_id', '=', company.id)],
            limit=1
        ).invoice_journal_id
        if not journal:
            raise UserError(f"No se ha configurado un diario de factura para este usuario en la compañía {company.name}.")
        return journal

    def _create_invoice(self, lines, move_type, journal):
        invoice = self.env['account.move'].create({
            'invoice_date': fields.Date.context_today(self),
            'move_type': move_type,
            'partner_id': self.vehicle_id.partner_id.id,
            'journal_id': journal.id,
            'workorder_id': self.id,
            'vehicle_id': self.vehicle_id.id,
            'invoice_line_ids': [
                (0, 0, {
                    'product_id': l.product_id.id,
                    'quantity': l.quantity,
                    'price_unit': (l.price_unit * l.quantity - l.discount) / l.quantity if l.quantity else l.price_unit,
                    'mechanic_ids': [(6, 0, l.mechanic_ids.ids)],
                }) for l in lines
            ],
        })
        # Agregar metodo de pago ecuatoriano
        invoice.sudo().write({
            'l10n_ec_sri_payment_id': journal.l10n_ec_sri_payment_id.id,
        })
        # Publicar factura
        invoice.action_post()

        lines.write({'is_invoiced': True})
        self.move_ids = [(4, invoice.id)]
        return invoice

    def action_generate_invoice(self):
        self.ensure_one()

        move_ids = self.env["account.move"]

        # Obtener lineas para facturar
        lines = self._get_lines_to_invoice()
        if not lines:
            raise UserError("No hay líneas pendientes de facturar.")

        # Separar líneas
        invoice_lines, receipt_lines = self._split_invoice_and_receipt_lines(lines)
        if not invoice_lines and not receipt_lines:
            raise UserError("No hay líneas válidas para procesar.")

        # Validar servicios sin mecanico
        self._check_services_have_mechanics(lines)

        # Obtener compañias para facturar
        company = self.env.company
        if company.mechanic_split_invoice:
            service_company = company.mechanic_service_company_id or company
            product_company = company.mechanic_product_company_id or company

            # Obtener lineas de servicios y lineas de productos
            service_lines, product_lines = self._split_lines_by_type(invoice_lines)

            # Generar facturas de servicios
            if service_lines:
                service_journal = self.get_invoice_journal(service_company)
                move_ids |= self.with_company(service_company)._create_invoice(service_lines, 'out_invoice', service_journal)

            # Generar facturas de productos
            if product_lines:
                product_journal = self.get_invoice_journal(product_company)
                move_ids |= self.with_company(product_company)._create_invoice(product_lines, 'out_invoice', product_journal)
        else:
            if invoice_lines:
                sale_journal = self.get_invoice_journal(company)
                move_ids |= self.with_company(company)._create_invoice(invoice_lines, 'out_invoice', sale_journal)

        # Si hay lineas para recibo
        if receipt_lines:
            main_company = company.mechanic_main_company_id or self.env.company
            receipt_journal = self.get_receipt_journal(main_company)
            move_ids |= self._create_receipt(receipt_lines, 'out_receipt', receipt_journal)
        
        # Orden finalizada
        self._register_vehicle_maintenance()
        self.state = 'done'

        # Reiniciar descuento
        if self.discount:
            self._register_discount_history(move_ids)

        return self.action_open_moves()

    def _create_receipt(self, lines, move_type, journal):
        
        receipt = self.env['account.move'].create({
            'invoice_date': fields.Date.context_today(self),
            'move_type': 'out_receipt',
            'partner_id': self.vehicle_id.partner_id.id,
            'journal_id': journal.id,
            'workorder_id': self.id,
            'vehicle_id': self.vehicle_id.id,
            'invoice_line_ids': [
                (0, 0, {
                    'product_id': l.product_id.id,
                    'quantity': l.quantity,
                    'price_unit': (l.price_unit * l.quantity - l.discount) / l.quantity if l.quantity else l.price_unit,
                    'tax_ids': [(6, 0, [])],
                    'mechanic_ids': [(6, 0, l.mechanic_ids.ids)],
                }) for l in lines
            ],
        })
        # Publicar recibo
        receipt.action_post()

        lines.write({'is_invoiced': True})
        self.move_ids = [(4, receipt.id)]

        return receipt

    def get_receipt_journal(self, company):
        journal = self.env['user.account.journal'].search(
            [('user_id', '=', self.env.user.id), ('company_id', '=', company.id)],
            limit=1
        ).receipt_journal_id
        if not journal:
            raise UserError(f"No se ha configurado un diario de recibos para este usuario en la compañía {company.name}.")
        return journal

    def action_generate_receipt(self):
        self.ensure_one()

        move_ids = self.env["account.move"]

        lines_to_receipt = self.line_ids.filtered(lambda l: not l.is_invoiced)
        if not lines_to_receipt:
            raise UserError("No hay líneas pendientes para generar recibo.")
        
        # Validar servicios sin mecanico
        self._check_services_have_mechanics(lines_to_receipt)

        # Obtener diario de recibo
        company = self.env.company
        if company.mechanic_split_invoice:
            company = company.mechanic_main_company_id or company
        receipt_journal = self.get_receipt_journal(company)
        move_ids |= self._create_receipt(lines_to_receipt, 'out_receipt', receipt_journal)

        # Finalizar orden de trabajo
        self._register_vehicle_maintenance()
        self.state = 'done'

        # Reiniciar descuento
        if self.discount:
            self._register_discount_history(move_ids)

        return self.action_open_moves()

    def action_open_moves(self):
        self.ensure_one()

        return {
            'name': 'Facturas / Recibos',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.move_ids.ids)],
            'context': {
                'create': False,
            },
        }

    def action_open_discounts(self):
        self.ensure_one()
        return {
            "name": "Descuentos",
            "type": "ir.actions.act_window",
            "res_model": "mechanic.workorder.discount",
            "view_mode": "list",
            "view_id": self.env.ref("ebal_mechanic.view_mechanic_workorder_discount_tree").id,
            "domain": [("workorder_id", "=", self.id)],
            "context": {
                "create": False
            }
        }

    def action_generate_ticket(self):
        self.ensure_one()
        return {
            "name": "Nuevo Ticket",
            "type": "ir.actions.act_window",
            "res_model": "helpdesk.ticket",
            "view_mode": "form",
            "target": "current",
            "context": {
                "default_vehicle_id": self.vehicle_id.id,
                "default_workorder_id": self.id,
                "default_partner_id": self.vehicle_id.partner_id.id,
            },
        }
    
    def action_open_tickets(self):
        self.ensure_one()
        return {
            "name": "Tickets",
            "type": "ir.actions.act_window",
            "res_model": "helpdesk.ticket",
            "view_mode": "list,form",
            "domain": [("workorder_id", "=", self.id)],
            "context": {
                "default_vehicle_id": self.vehicle_id.id,
                "default_workorder_id": self.id,
            },
        }

    def action_register_payment(self):

        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": "Registrar Abono",
            "res_model": "customer.payment.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_partner_id": self.partner_id.id,
                "default_workorder_id": self.id,
            }
        }

    def action_open_payments(self):
        self.ensure_one()

        return {
            "name": "Pagos",
            "type": "ir.actions.act_window",
            "res_model": "account.payment",
            "view_mode": "list,form",
            "domain": [("workorder_id", "=", self.id)],
            "context": {
                "create": False
            }
        }
    
    def _register_vehicle_maintenance(self):
        Maintenance = self.env['mechanic.vehicle.maintenance']

        for line in self.line_ids:
            product = line.product_id.product_tmpl_id

            if not product.track_by_mileage:
                continue

            # Archivar mantenimiento anterior del mismo producto
            previous = Maintenance.search([
                ('vehicle_id', '=', self.vehicle_id.id),
                ('product_id', '=', line.product_id.id),
                ('active', '=', True),
            ])

            previous.write({'active': False})

            # Crear nuevo registro
            Maintenance.create({
                'vehicle_id': self.vehicle_id.id,
                'product_id': line.product_id.id,
                'workorder_id': self.id,
                'mileage': self.mileage,
                'next_mileage': int(self.mileage) + int(line.product_id.mileage_durability or 0),
            })

    def action_print_workorder(self):
        self.ensure_one()
        return self.env.ref('ebal_mechanic.action_report_workorder').report_action(self)
    
    def action_print_quotation(self):
        self.ensure_one()
        return self.env.ref('ebal_mechanic.action_report_quotation').report_action(self)

    def action_reset_to_draft(self):
        self.ensure_one()
        self.state = 'draft'

    def _generate_public_quotation_pdf(self):
        self.ensure_one()

        ir_actions_report_sudo = self.env['ir.actions.report'].sudo()
        quotation_report_action_sudo = self.env.ref('ebal_mechanic.action_report_quotation').sudo()
        content, _content_type = ir_actions_report_sudo._render_qweb_pdf(
            quotation_report_action_sudo, res_ids=self.ids
        )
        attachment = self.env['ir.attachment'].create({
            'name': f'Proforma_{self.name}.pdf',
            'type': 'binary',
            'mimetype': 'application/pdf',
            'raw': content,
            'res_model': self._name,
            'res_id': self.id,
            'public': True,
        })

        return attachment
    
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
        lines.append("⚠️ *IMPORTANTE*")
        lines.append(
            "Según las condiciones aceptadas en la Orden de Trabajo, el vehículo deberá ser retirado dentro de las próximas 24 horas posteriores a esta notificación."
        )
        lines.append(
            "Pasado este tiempo, se aplicará un cargo de $3.00 diarios por concepto de bodegaje, mismo que será incluido en la planilla final."
        )
        lines.append("")
        lines.append("Para evitar cargos adicionales recomendamos coordinar el retiro lo antes posible.")
        lines.append("")
        lines.append("Gracias por confiar en CAR-ELECTRONIC 🙌")
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

    def action_dummy(self):
        return True

class MechanicWorkorderLine(models.Model):
    _name = "mechanic.workorder.line"
    _description = "Línea de Orden de Trabajo"

    currency_id = fields.Many2one('res.currency', string='Moneda', default=lambda self: self.env.company.currency_id)
    workorder_id = fields.Many2one("mechanic.workorder", string="Orden de trabajo", required=True)
    product_id = fields.Many2one("product.product", string="Producto/Servicio", required=True)
    mechanic_ids = fields.Many2many(
        'res.users',
        'mechanic_workorder_line_user_rel',
        'line_id',
        'user_id',
        string='Mecánicos',
        domain="[('share','=',False)]"
    )
    quantity = fields.Float(string="Cantidad", default=1.0)
    price_unit = fields.Float(
        string="Precio Unitario",
        currency_field="currency_id")
    discount = fields.Monetary(
        string="Descuento",
        currency_field="currency_id"
    )
    total = fields.Monetary(string="Total", compute="_compute_total", store=True, currency_field="currency_id")
    
    is_invoiced = fields.Boolean(
        string="Facturado?",
        default=False,
        readonly=True
    )

    def unlink(self):
        for line in self:
            if line.is_invoiced:
                raise UserError("No puede eliminar líneas ya facturadas.")
        return super().unlink()

    @api.depends("quantity", "price_unit", "discount")
    def _compute_total(self):
        for line in self:
            subtotal = line.quantity * line.price_unit
            line.total = subtotal - line.discount

    @api.onchange('product_id')
    def _onchange_product_id(self):
        for line in self:
            if line.product_id:
                line.price_unit = line.product_id.lst_price

class MechanicWorkorderAttachmentLine(models.Model):
    _name = "mechanic.workorder.attachment.line"
    _description = "Línea de adjuntos de Orden de Trabajo"
    _rec_name = "display_name"
    _order = "id desc"

    workorder_id = fields.Many2one(
        "mechanic.workorder",
        string="Orden de Trabajo",
        required=True,
        ondelete="cascade",
        index=True,
    )
    attachment_id = fields.Many2one(
        "ir.attachment",
        string="Archivo",
        required=True,
        ondelete="cascade",
    )

    # titulo personalizado
    title = fields.Char(
        string="Título"
    )

    selected = fields.Boolean(
        string="Enviar",
        default=False
    )

    # nombre final inteligente
    display_name = fields.Char(
        compute="_compute_display_name",
        store=False
    )

    create_date_attachment = fields.Datetime(
        string="Fecha creación",
        related="attachment_id.create_date",
        store=False,
        readonly=True,
    )

    @api.depends("title", "attachment_id.name")
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = rec.title or rec.attachment_id.name

class MechanicWorkorderDiscount(models.Model):
    _name = "mechanic.workorder.discount"
    _description = "Descuentos de Orden de Trabajo"
    _order = "date desc, id desc"

    # Relaciones
    workorder_id = fields.Many2one(
        "mechanic.workorder",
        string="Orden de Trabajo",
        required=True,
        ondelete="cascade",
        index=True
    )

    move_ids = fields.Many2many(
        "account.move",
        string="Facturas / Recibos",
        readonly=True
    )

    # Campos principales
    amount = fields.Monetary(
        string="Monto Descuento",
        required=True
    )

    currency_id = fields.Many2one(
        "res.currency",
        string="Moneda",
        required=True,
        default=lambda self: self.env.company.currency_id
    )

    date = fields.Datetime(
        string="Fecha",
        default=fields.Datetime.now,
        required=True
    )

    description = fields.Char(
        string="Descripción"
    )

    # Auditoria
    user_id = fields.Many2one(
        "res.users",
        string="Aplicado por",
        default=lambda self: self.env.user,
        readonly=True
    )

    # Campos compute
    move_count = fields.Integer(
        string="N° Comprobantes",
        compute="_compute_move_count"
    )

    @api.depends("move_ids")
    def _compute_move_count(self):
        for rec in self:
            rec.move_count = len(rec.move_ids)

    # Acciones
    def action_open_moves(self):
        self.ensure_one()
        return {
            "name": "Facturas / Recibos",
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "view_mode": "list,form",
            "domain": [("id", "in", self.move_ids.ids)],
            "context": {"create": False},
        }