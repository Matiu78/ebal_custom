# -*- coding: utf-8 -*-
{
    "name": "Sitio web por cliente (cargador)",
    "version": "18.0.1.0.0",
    "summary": "Aplica el sitio web de un cliente (portada, estilos, menú, tienda) que viaja dentro de su módulo ebal_<cliente>",
    "description": """
Sitio web por cliente — cargador
================================

Cada módulo de cliente (ebal_kaivox, ebal_carelectronic, ebal_diegovelez, ebal_ebalsoft…)
trae su sitio en la carpeta ``site/`` (portada, estilos, pie, imágenes y un ``apply.py``).
Este módulo agrega la ventana **Sitio web → Configuración → Aplicar sitio de <cliente>**
que lo carga en la base. Es manual a propósito: aplicar un sitio reemplaza la portada
y el pie del sitio web, así que nunca se hace solo al instalar o actualizar.

Solo para administradores. Repetible: aplicarlo otra vez deja todo igual.
""",
    "author": "EBAL SOFTWARE",
    "license": "LGPL-3",
    "category": "Website",
    "depends": ["website"],
    "data": [
        "security/ir.model.access.csv",
        "views/site_builder_views.xml",
    ],
    "installable": True,
    "application": False,
}
