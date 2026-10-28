# Sitio web de Car Electrónic (website 1). Idempotente. Lo ejecuta ebal_site_builder (ventana «Aplicar sitio de Car Electrónic»).
import base64, os, re
FLAGS = {k for k, v in OPTIONS.items() if v}   # D y OPTIONS los pone ebal_site_builder
website = env["website"].browse(1)
langs = env["res.lang"].search([]).mapped("code")
if "en_US" not in langs:
    langs.append("en_US")
Att = env["ir.attachment"].sudo()
MIME = {".png": "image/png", ".webp": "image/webp", ".jpg": "image/jpeg"}

# 1) imágenes públicas -> url
urls = {}
for root, _dirs, files in os.walk(D + "assets"):
    for fn in sorted(files):
        raw = open(os.path.join(root, fn), "rb").read()
        name = "carelectronic_web_" + fn
        att = Att.search([("name", "=", name), ("res_model", "=", "website"), ("res_id", "=", website.id)], limit=1)
        vals = {"name": name, "datas": base64.b64encode(raw), "mimetype": MIME[os.path.splitext(fn)[1]],
                "public": True, "res_model": "website", "res_id": website.id}
        if att:
            att.write(vals)
        else:
            att = Att.create(vals)
        urls[fn] = "/web/image/%s-%s/%s" % (att.id, att.checksum[:8], fn)
def fill(text):
    return re.sub(r"\{\{img:([^}]+)\}\}", lambda m: urls[m.group(1)], text)

V = env["ir.ui.view"]
def write_arch(view, arch):
    for lang in langs:
        view.with_context(lang=lang).write({"arch_db": arch})

# 2) portada
page = env["website.page"].search([("url", "=", "/"), ("website_id", "=", website.id)], limit=1)
write_arch(page.view_id, fill(open(D + "home.xml").read()))
page.write({
    "website_meta_title": "Car Electrónic | Electromecánica automotriz en Cuenca",
    "website_meta_description": "Taller de electromecánica automotriz en San José de Balzay, Cuenca: diagnóstico, electricidad, electrónica, inyección y mantenimiento. Llámanos al 098 129 4927.",
    "website_meta_keywords": "electromecánica, diagnóstico automotriz, electricidad automotriz, inyección, mantenimiento, taller, Cuenca",
})

# 3) pie de página (vista propia del sitio)
VW = V.with_context(website_id=website.id)
footer = VW.search([("key", "=", "website.footer_custom"), ("website_id", "in", (False, website.id))], order="website_id", limit=1)
for lang in langs:
    footer.with_context(lang=lang, website_id=website.id).write({"arch_db": fill(open(D + "footer.xml").read())})

# 4) menú
Menu = env["website.menu"]
root = website.menu_id
want = [("Inicio", "/"), ("Servicios", "/#servicios"), ("Galería", "/#galeria"), ("Ubicación", "/#ubicacion"),
        ("Consultar orden", "/consultar-orden"), ("Contáctenos", "/contactus")]
kids = Menu.search([("website_id", "=", website.id), ("parent_id", "=", root.id)])
by_url = {m.url: m for m in kids}
for seq, (name, url) in enumerate(want, start=1):
    m = by_url.get(url) or Menu.create({"name": name, "url": url, "parent_id": root.id, "website_id": website.id})
    m.write({"name": name, "sequence": seq * 10})
for m in kids:
    if m.url not in dict((u, 1) for _n, u in want) and not m.child_id:
        m.unlink()  # solo los de ejemplo de Odoo; "Consultar orden" y "Contáctenos" se mantienen

# 5) textos de ejemplo de Odoo -> datos reales (copia propia del sitio CON sus traducciones)
PH_PHONE = [("tel:+1 555-555-5556", "tel:+593981294927"), ("+1 555-555-5556", "098 129 4927")]
def clean(arch):
    for x, y in PH_PHONE + [("3575 Fake Buena Vista Avenue", "Av. Del Tejar y César Andrade y Cordero, Cuenca")]:
        arch = arch.replace(x, y)
    # el correo de ejemplo (info@yourcompany.example.com / info@suempresa.ejemplo.com) no existe: se quita esa línea
    arch = re.sub(r"\s*<li>(?:(?!</li>).)*?(?:example\.com|ejemplo\.com)(?:(?!</li>).)*?</li>", "", arch, flags=re.S)
    arch = re.sub(r"\s*<a href=\"mailto:info@[^\"]*(?:example|ejemplo)\.com\"(?:(?!</a>).)*?</a>", "", arch, flags=re.S)
    return arch
for key in ("website.header_text_element", "website.contactus", "website.contactus_thanks"):
    generic = V.search([("key", "=", key), ("website_id", "=", False)], limit=1)
    target = V.search([("key", "=", key), ("website_id", "=", website.id)], limit=1)
    if not target and generic:
        # la copia propia del sitio la crea Odoo (COW) al escribir con el contexto del sitio: conserva clave y traducciones
        generic.with_context(website_id=website.id).write({"arch_db": generic.arch_db})
        target = V.search([("key", "=", key), ("website_id", "=", website.id)], limit=1)
    for lang in langs if target else []:
        tl = target.with_context(lang=lang, no_cow=True)
        arch = tl.arch_db
        new_arch = clean(arch)
        if new_arch != arch:
            tl.write({"arch_db": new_arch})
cp = VW.search([("key", "=", "website.footer_copyright_company_name"), ("website_id", "in", (False, website.id))], order="website_id", limit=1)
new = ('<data inherit_id="website.layout">\n    <xpath expr="//footer//span[hasclass(\'o_footer_copyright_name\')]" position="replace">\n'
       '        <span class="o_footer_copyright_name me-2">© Car Electrónic · Electromecánica automotriz</span>\n    </xpath>\n</data>')
for lang in langs:
    cp.with_context(lang=lang, website_id=website.id).write({"arch_db": new})

# 6) sitio: estilos, logo, ícono, Facebook
def b64(path):
    return base64.b64encode(open(D + "assets/" + path, "rb").read())
website.write({
    "custom_code_head": fill(open(D + "head.html").read()),
    "logo": b64("logo_carelectronic_alpha.png"),
    "favicon": b64("icono_carelectronic.png"),
    "social_facebook": "https://www.facebook.com/photo?fbid=1651007329880737&set=a.588684349446379",
    "name": "Car Electrónic",
})
# 7) logo de la compañía (documentos, tickets, etc.)
if "company_logo" in FLAGS:
    website.company_id.write({"logo": b64("logo_carelectronic.png")})
RESULT = "Sitio de Car Electrónic aplicado (%d imágenes%s)." % (len(urls), "; logo de la compañía cambiado" if "company_logo" in FLAGS else "")
