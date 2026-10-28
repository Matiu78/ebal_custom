# -*- coding: utf-8 -*-
import logging
import os

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError
from odoo.modules.module import get_manifest, get_module_path

_logger = logging.getLogger(__name__)


class EbalSiteBuilder(models.TransientModel):
    """Aplica el sitio web que trae un módulo de cliente.

    El módulo del cliente guarda su sitio en ``<módulo>/site/``:
      - ``apply.py``  : script que escribe las vistas/menús/imágenes en el sitio (se ejecuta con
                        ``env``, ``D`` (carpeta ``site/`` con barra final) y ``OPTIONS`` ya definidos);
      - el resto      : plantillas (home.xml, footer.xml…), estilos (head.html) e imágenes (assets/).
    """

    _name = "ebal.site.builder"
    _description = "Aplicar sitio web de un cliente"

    module = fields.Char(string="Módulo", required=True, readonly=True)
    summary = fields.Char(string="Sitio", compute="_compute_summary")
    # opciones que solo algunos sitios usan (ver apply.py de cada módulo)
    whatsapp = fields.Char(
        string="WhatsApp (con código de país)",
        help="Solo dígitos, p. ej. 593995959358. Si queda vacío, el sitio sale sin botones de WhatsApp.",
    )
    company_logo = fields.Boolean(
        string="Cambiar también el logo de la compañía",
        help="Además del logo del sitio, reemplaza el logo de la compañía (sale en proformas, órdenes y facturas en PDF).",
    )

    @api.depends("module")
    def _compute_summary(self):
        for rec in self:
            manifest = get_manifest(rec.module) if rec.module else {}
            rec.summary = manifest.get("summary") or rec.module

    # -- ejecución ------------------------------------------------------------

    @api.model
    def apply_module(self, module, **options):
        """Carga el sitio del módulo ``module`` (también se puede llamar desde ``odoo shell``)."""
        if not self.env.su and not self.env.user.has_group("base.group_system"):
            raise AccessError(_("Solo un administrador puede aplicar un sitio web."))
        path = get_module_path(module)
        if not path:
            raise UserError(_("El módulo %s no existe.", module))
        site_dir = os.path.join(path, "site")
        script = os.path.join(site_dir, "apply.py")
        if not os.path.isfile(script):
            raise UserError(_("El módulo %s no trae un sitio (falta site/apply.py).", module))
        if not self.env["ir.module.module"].sudo().search_count([("name", "=", module), ("state", "=", "installed")]):
            raise UserError(_("El módulo %s no está instalado.", module))
        env = self.env
        namespace = {
            "env": env,
            "D": site_dir + os.sep,
            "OPTIONS": {k: v for k, v in options.items() if v},
            "__name__": "ebal_site_apply",
        }
        _logger.info("Aplicando el sitio web del módulo %s", module)
        with open(script, encoding="utf-8") as fh:
            exec(compile(fh.read(), script, "exec"), namespace)  # noqa: S102 - código del propio módulo, solo admin
        # vacía los cachés de vistas y avisa a los demás procesos de Odoo (workers) cuando se guarde
        env.registry.clear_all_caches()
        env.cr.postcommit.add(env.registry.signal_changes)
        return namespace.get("RESULT") or _("Sitio aplicado.")

    def action_apply(self):
        self.ensure_one()
        result = self.apply_module(
            self.module,
            whatsapp="".join(ch for ch in (self.whatsapp or "") if ch.isdigit()),
            company_logo=self.company_logo,
        )
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Sitio web"),
                "message": result,
                "type": "success",
                "sticky": False,
                "next": {"type": "ir.actions.client", "tag": "reload"},
            },
        }
