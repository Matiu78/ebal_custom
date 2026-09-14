# -*- coding: utf-8 -*-
from odoo import api, models

CATEGORY_NAME = "MicroWisp Globox"

INTERNET = [
    ("102", "Plan Internet Smart", 13.95),
    ("119", "Plan Conectados", 15.00),
    ("121", "Plan Internet Stándard C", 15.10),
    ("109", "Plan Internet Ideal C", 17.10),
    ("110", "Plan Internet Familiar C", 21.10),
    ("108", "Plan Internet Plus", 23.90),
    ("113", "Plan Internet Premium C", 28.11),
    ("111D", "Plan Internet Standar Especial", 9.70),
    ("101D", "Plan Internet Ideal Especial", 11.25),
    ("112D", "Fibra Internet Familiar Especial", 12.45),
]

TV = [
    ("PS01", "Tv Smart", 10.95),
    ("PE01", "Tv Estándar", 12.00),
    ("PB01", "Tv Básico", 16.50),
]

COMBOS = [
    ("102-PS01", "Globox triple", 24.90, [("102", 13.95), ("PS01", 10.95)]),
    ("119-PE01", "Globox triple +", 27.00, [("119", 15.00), ("PE01", 12.00)]),
    ("121-PB01", "Combo Stándard", 31.60, [("121", 15.10), ("PB01", 16.50)]),
    ("109-PB01", "Combo Ideal", 33.90, [("109", 17.10), ("PB01", 16.50)]),
    ("110-PB01", "Combo Familiar", 37.90, [("110", 21.10), ("PB01", 16.50)]),
    ("108-PB01", "Combo Plus", 40.70, [("108", 23.90), ("PB01", 16.50)]),
    ("113-PB01", "Combo Premium", 44.90, [("113", 28.11), ("PB01", 16.50)]),
    ("111D-PE01", "Combo Especial 1", 21.70, [("111D", 9.70), ("PE01", 12.00)]),
    ("101D-PE01", "Combo Especial 2", 23.25, [("101D", 11.25), ("PE01", 12.00)]),
    ("112D-PB01", "Combo Especial 3", 28.95, [("112D", 12.45), ("PB01", 16.50)]),
]


class MicrowispProduct(models.Model):
    _inherit = "microwisp.product"

    @api.model
    def _ebal_globox_load_catalog(self):
        """Crea productos Odoo limpios y combos en Productos MicroWisp."""
        Category = self.env["product.category"]
        categ = Category.search([("name", "=", CATEGORY_NAME)], limit=1)
        if not categ:
            categ = Category.create({"name": CATEGORY_NAME})

        Tmpl = self.env["product.template"]
        Line = self.env["microwisp.product.line"]
        MwProduct = self.env["microwisp.product"]
        Config = self.env["microwisp.config"]

        def _ensure_odoo_product(code, name, price):
            tmpl = Tmpl.search([("default_code", "=", code)], limit=1)
            vals = {
                "name": name,
                "default_code": code,
                "type": "service",
                "sale_ok": True,
                "purchase_ok": False,
                "list_price": price,
                "categ_id": categ.id,
            }
            if tmpl:
                tmpl.write({"name": name, "list_price": price, "categ_id": categ.id})
            else:
                tmpl = Tmpl.create(vals)
            return tmpl.product_variant_id

        by_code = {}
        for code, name, price in INTERNET + TV:
            by_code[code] = _ensure_odoo_product(code, name, price)

        configs = Config.search([])
        if not configs:
            return True

        for config in configs:
            for code, name, _price, parts in COMBOS:
                mw = MwProduct.find_by_comprobado(config, code)
                if not mw:
                    mw = MwProduct.search(
                        [("config_id", "=", config.id), ("name", "=", name)],
                        limit=1,
                    )
                if not mw:
                    mw = MwProduct.create(
                        {
                            "config_id": config.id,
                            "name": name,
                            "comprobado": code,
                        }
                    )
                elif not mw.comprobado:
                    mw.comprobado = code
                if mw.line_ids:
                    continue
                sequence = 10
                for part_code, amount in parts:
                    product = by_code.get(part_code)
                    if not product:
                        continue
                    Line.create(
                        {
                            "mw_product_id": mw.id,
                            "sequence": sequence,
                            "product_id": product.id,
                            "invoice_name": product.name,
                            "amount_type": "fixed",
                            "amount": amount,
                        }
                    )
                    sequence += 10
        return True


class MicrowispConfig(models.Model):
    _inherit = "microwisp.config"

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        self.env["microwisp.product"]._ebal_globox_load_catalog()
        return records
