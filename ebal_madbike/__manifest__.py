# -*- coding: utf-8 -*-
{
    "name": "Madbike — Personalizaciones",
    "version": "19.0.1.3.0",
    "summary": "Ajustes específicos de la instancia Madbike (reportes de "
               "orden de trabajo y proforma) y su sitio web con tienda e INGCO.",
    "author": "EBAL SOFTWARE",
    "website": "https://www.ebalsoft.com",
    "category": "Mechanic Management",
    "license": "LGPL-3",
    "depends": ["ebal_mechanic", "ebal_site_builder", "website_sale", "stock"],
    "data": [
        "report/report_mechanic_customizations.xml",
        "data/cron.xml",
        "views/gala_views.xml",
        "views/site_menu.xml",
    ],
    "installable": True,
    "application": False,
}
