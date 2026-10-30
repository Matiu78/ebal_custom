# -*- coding: utf-8 -*-
"""Sincroniza precios y disponibilidad INGCO/WADFOW desde el catálogo de galaimportaciones.com
(la web del importador, un Next.js: cada página /catalogo?page=N trae el JSON de sus productos)."""
import logging
import re
import time

import requests

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

CATALOG_URL = "https://galaimportaciones.com/catalogo?page=%d"
# name ... sku ... price ... stockState/stockQty de cada producto del payload (comillas escapadas)
PRODUCT_RE = re.compile(
    r'\\"sku\\":\\"([^"\\]+)\\",\\"kronosCode\\":\\"[^"\\]*\\",\\"price\\":([0-9.]+),'
    r'.*?\\"stockState\\":\\"(\w+)\\",\\"stockQty\\":(\d+)')
MIN_EXPECTED = 500  # si trae menos, la web cambió o falló: no tocar nada


class GalaSync(models.AbstractModel):
    _name = "ebal.gala.sync"
    _description = "Sincronización de precios y stock con Gala Importaciones"

    @api.model
    def _fetch_catalog(self):
        data = {}
        for page in range(1, 200):
            resp = requests.get(CATALOG_URL % page, headers={"User-Agent": "Mozilla/5.0"}, timeout=60)
            resp.raise_for_status()
            found = PRODUCT_RE.findall(resp.text)
            if not found:
                break
            for sku, price, state, qty in found:
                data[sku] = (float(price), state, int(qty))
            time.sleep(0.4)  # ponytail: sin concurrencia para no cargar la web del proveedor
        return data

    @api.model
    def run_sync(self):
        data = self._fetch_catalog()
        if len(data) < MIN_EXPECTED:
            raise UserError(_("Gala devolvió solo %d productos; no se actualizó nada.", len(data)))
        ICP = self.env["ir.config_parameter"].sudo()
        factor = float(ICP.get_param("ebal_madbike.gala_price_factor", "1.0025"))
        now = fields.Datetime.now()
        Template = self.env["product.template"].sudo().with_context(active_test=False)
        variants = self.env["product.product"].sudo().with_context(active_test=False).search(
            [("default_code", "in", list(data))])
        seen, changed = set(), 0
        for variant in variants:
            tmpl = variant.product_tmpl_id
            price, state, qty = data[variant.default_code]
            vals = {
                "gala_state": "in_stock" if state == "IN_STOCK" else "out_of_stock",
                "gala_qty": qty, "gala_price": price, "gala_synced_at": now,
            }
            if price > 0:
                new_price = round(price * factor, 4)
                if abs(tmpl.list_price - new_price) > 0.0001:
                    vals["list_price"] = new_price
                    changed += 1
            if not tmpl.is_storable:
                vals["is_storable"] = True  # para que lo que se vende baje de mi inventario
            tmpl.write(vals)
            seen.add(tmpl.id)
        # ligados antes pero que ya no están en la web: quedan como agotados en Gala
        gone = Template.search([("gala_state", "!=", False), ("id", "not in", list(seen))])
        gone.write({"gala_state": "out_of_stock", "gala_qty": 0, "gala_synced_at": now})
        ICP.set_param("ebal_madbike.gala_last_sync", "%s | web: %d, productos: %d, precios cambiados: %d, ya no están: %d" % (
            now, len(data), len(seen), changed, len(gone)))
        _logger.info("Gala: web=%d ligados=%d precios=%d ausentes=%d", len(data), len(seen), changed, len(gone))
        return {"web": len(data), "linked": len(seen), "prices": changed, "gone": len(gone)}

    @api.model
    def action_run_sync(self):
        res = self.run_sync()
        return {"type": "ir.actions.client", "tag": "display_notification", "params": {
            "title": _("Gala sincronizado"), "type": "success", "sticky": False,
            "message": _("Productos ligados: %(linked)d · precios cambiados: %(prices)d · ausentes: %(gone)d", **res)}}
