from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    mechanic_split_invoice = fields.Boolean(
        string="Facturar repuestos y servicios por separado",
        related='company_id.mechanic_split_invoice',
        readonly=False
    )

    mechanic_main_company_id = fields.Many2one(
        'res.company',
        string="Compañía Principal",
        related='company_id.mechanic_main_company_id',
        readonly=False
    )

    mechanic_service_company_id = fields.Many2one(
        'res.company',
        string="Compañía para Servicios",
        related='company_id.mechanic_service_company_id',
        readonly=False
    )

    mechanic_product_company_id = fields.Many2one(
        'res.company',
        string="Compañía para Repuestos",
        related='company_id.mechanic_product_company_id',
        readonly=False
    )

class ResCompany(models.Model):
    _inherit = 'res.company'

    mechanic_split_invoice = fields.Boolean(
        string="Facturar repuestos y servicios por separado"
    )

    mechanic_main_company_id = fields.Many2one(
        'res.company',
        string="Compañía Principal"
    )

    mechanic_product_company_id = fields.Many2one(
        'res.company',
        string="Compañía para Repuestos"
    )

    mechanic_service_company_id = fields.Many2one(
        'res.company',
        string="Compañía para Servicios"
    )