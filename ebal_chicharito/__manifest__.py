# -*- coding: utf-8 -*-
{
    "name": "El Chicharito — sitio web",
    "version": "18.0.1.0.0",
    "summary": "Sitio web de El Chicharito (Cuenca): portada, comida rápida y postres con los colores de su logo",
    "description": """
El Chicharito — sitio web
=========================

Trae el sitio en ``site/`` (portada, página de comida rápida, página de postres, estilos, pie e imágenes).
Se carga desde **Sitio web → Configuración → Aplicar sitio de El Chicharito**: además crea en el
inventario los postres (sin precio) para usarlos en el punto de venta. Manual a propósito.
""",
    "author": "EBAL SOFTWARE",
    "license": "LGPL-3",
    "category": "Website",
    "depends": ["ebal_site_builder", "point_of_sale"],
    "data": ["views/site_menu.xml"],
    "installable": True,
    "application": False,
}
