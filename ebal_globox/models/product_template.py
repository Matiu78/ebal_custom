# -*- coding: utf-8 -*-
from odoo import api, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.model
    def _ebal_globox_load_catalog(self):
        """Compat: el catálogo ahora vive en Productos MicroWisp."""
        return self.env["microwisp.product"]._ebal_globox_load_catalog()
