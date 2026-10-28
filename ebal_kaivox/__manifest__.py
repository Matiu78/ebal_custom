# -*- coding: utf-8 -*-
{
    "name": "Kaivox — sitio web y tienda en línea",
    "version": "18.0.1.0.0",
    "summary": "Tienda en línea de Kaivox (Gualaceo): portada, categorías, buscador y catálogo publicado con los colores de su logo",
    "description": """
Kaivox — sitio web y tienda en línea
====================================

Trae el sitio de Kaivox en ``site/`` (portada, estilos, pie, buscador, categorías, imágenes).
Se carga desde **Sitio web → Configuración → Aplicar sitio de Kaivox**: crea las categorías de la
tienda (clasificando por el nombre en español), publica los productos con stock y precio, y
despublica lo que ya no los tiene. No cambia precios, stock ni nombres.
""",
    "author": "EBAL SOFTWARE",
    "license": "LGPL-3",
    "category": "Website",
    "depends": ["ebal_site_builder", "website_sale", "website_sale_stock"],
    "data": ["views/site_menu.xml"],
    "installable": True,
    "application": False,
}
