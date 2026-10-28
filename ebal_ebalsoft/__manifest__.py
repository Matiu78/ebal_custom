# -*- coding: utf-8 -*-
{
    "name": "EbalSoft — sitio web",
    "version": "18.0.1.0.0",
    "summary": "Sitio web de ebalsoft.com: portada con planes, datos de la empresa y páginas legales con el estilo de la marca",
    "description": """
EbalSoft — sitio web
====================

Trae el sitio de ebalsoft.com en ``site/`` (portada, planes, estilos, pie). Se carga desde
**Sitio web → Configuración → Aplicar sitio de ebalsoft**. Las páginas legales (privacidad,
condiciones, eliminación de datos) no se tocan: solo toman el encabezado y el pie nuevos.
""",
    "author": "EBAL SOFTWARE",
    "license": "LGPL-3",
    "category": "Website",
    "depends": ["ebal_site_builder"],
    "data": ["views/site_menu.xml"],
    "installable": True,
    "application": False,
}
