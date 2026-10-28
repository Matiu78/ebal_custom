# Sitio web de ebalsoft.com (website 1). Idempotente. Lo ejecuta ebal_site_builder (ventana «Aplicar sitio de ebalsoft»).
# Reemplaza la portada, el pie, los estilos y los datos de ejemplo de Odoo; no toca menú, logo ni productos.
import base64, os, re

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
        name = "sitio_web_" + fn
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
VW = V.with_context(website_id=website.id)

# 2) portada y pie de página (vistas propias del sitio, con todas las traducciones)
page = env["website.page"].search([("url", "=", "/"), ("website_id", "=", website.id)], limit=1)
for lang in langs:
    page.view_id.with_context(lang=lang).write({"arch_db": fill(open(D + "home.xml").read())})
footer = VW.search([("key", "=", "website.footer_custom"), ("website_id", "in", (False, website.id))], order="website_id", limit=1)
for lang in langs:
    footer.with_context(lang=lang, website_id=website.id).write({"arch_db": fill(open(D + "footer.xml").read())})

# 3) textos de ejemplo de Odoo -> datos reales (copia propia del sitio, conserva las traducciones)
PH = [("tel:+1 555-555-5556", "tel:+593987521999"), ("+1 555-555-5556", "+593 987 521 999"),
      ("info@yourcompany.example.com", "info@ebalsoft.com"), ("info@suempresa.ejemplo.com", "info@ebalsoft.com"),
      ("3575 Fake Buena Vista Avenue", "Calle del Retorno, S/N, Calle del Fico")]
for key in ("website.header_text_element", "website.contactus", "website.contactus_thanks"):
    generic = V.search([("key", "=", key), ("website_id", "=", False)], limit=1)
    target = V.search([("key", "=", key), ("website_id", "=", website.id)], limit=1)
    if not target and generic:
        generic.with_context(website_id=website.id).write({"arch_db": generic.arch_db})
        target = V.search([("key", "=", key), ("website_id", "=", website.id)], limit=1)
    for lang in langs if target else []:
        tl = target.with_context(lang=lang, no_cow=True)
        arch = tl.arch_db
        new_arch = arch
        for x, y in PH:
            new_arch = new_arch.replace(x, y)
        if new_arch != arch:
            tl.write({"arch_db": new_arch})
cp = VW.search([("key", "=", "website.footer_copyright_company_name"), ("website_id", "in", (False, website.id))], order="website_id", limit=1)
new = ('<data inherit_id="website.layout">\n    <xpath expr="//footer//span[hasclass(\'o_footer_copyright_name\')]" position="replace">\n'
       '        <span class="o_footer_copyright_name me-2">Copyright © EbalSoftware</span>\n    </xpath>\n</data>')
for lang in langs:
    cp.with_context(lang=lang, website_id=website.id).write({"arch_db": new})

# 4) estilos del sitio
website.write({"custom_code_head": open(D + "head.html").read()})
RESULT = "Sitio de ebalsoft aplicado (%d imágenes)." % len(urls)
