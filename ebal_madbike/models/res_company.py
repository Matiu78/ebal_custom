from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    gala_price_margin = fields.Float(
        string="Recargo sobre precio Gala (%)",
        digits=(16, 4),
        default=44.35,
        help="Precio de venta = precio de distribuidor de galaimportaciones.com × (1 + %/100).",
    )

    def write(self, vals):
        res = super().write(vals)
        if "gala_price_margin" in vals:
            self.env["ebal.gala.sync"]._reprice_from_gala()
        return res


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    gala_price_margin = fields.Float(related="company_id.gala_price_margin", readonly=False)
