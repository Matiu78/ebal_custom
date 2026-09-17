# -*- coding: utf-8 -*-
{
    "name": "Globox",
    "version": "18.0.1.1.0",
    "summary": "Catálogo MicroWisp Globox (combos internet + TV)",
    "description": """
Globox
======

Crea productos Odoo de internet y TV, y los combos en **Productos MicroWisp**:

* Comprobado (ej. 112D-PB01)
* Por línea: empresa, diario, producto Odoo, nombre en factura y monto
""",
    "author": "EBAL SOFTWARE",
    "website": "https://www.ebalsoft.com",
    "category": "Globox",
    "license": "LGPL-3",
    "depends": [
        "ebal_microwisp",
    ],
    "data": [
        "data/globox_product_catalog.xml",
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
}
