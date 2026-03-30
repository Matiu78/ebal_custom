from odoo import models, fields

class AccountMove(models.Model):
    _inherit = 'account.move'

    workorder_id = fields.Many2one(
        'mechanic.workorder', string='Orden de Trabajo', readonly=True
    )
    vehicle_id = fields.Many2one(
        'mechanic.vehicle', string='Vehículo', readonly=True
    )

    def get_portal_allowed_companies(self, user):
        """Devuelve las compañías cuyas facturas puede ver este usuario en el portal"""
        companies = self.env['res.company']
        for company in self.env['res.company'].sudo().search([]):
            if company.mechanic_split_invoice:
                if company.mechanic_service_company_id:
                    companies |= company.mechanic_service_company_id
                if company.mechanic_product_company_id:
                    companies |= company.mechanic_product_company_id
            else:
                companies |= company
        return companies

    def _get_overdue_invoices_domain(self, partner_id=None, allowed_companies=None):
        domain = [
            ('state', 'not in', ('cancel', 'draft')),
            ('move_type', 'in', ('out_invoice', 'out_receipt')),
            ('payment_state', 'not in', ('in_payment', 'paid', 'reversed', 'blocked', 'invoicing_legacy')),
            ('invoice_date_due', '<', fields.Date.today()),
            ('partner_id', '=', partner_id or request.env.user.partner_id.id),
        ]
        if allowed_companies:
            domain.append(('company_id', 'in', allowed_companies.ids))
        return domain

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    mechanic_ids = fields.Many2many(
        'res.users',
        'account_move_line_user_rel',
        'move_line_id',
        'user_id',
        string='Mecánicos',
        domain="[('share','=',False)]"
    )
