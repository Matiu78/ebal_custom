# Sitio web de El Chicharito (website 1). Idempotente. Lo ejecuta ebal_site_builder (ventana «Aplicar sitio de El Chicharito»).
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
def write_arch(view, arch):
    for lang in langs:
        view.with_context(lang=lang).write({"arch_db": arch})

# 2) portada
page = env["website.page"].search([("url", "=", "/"), ("website_id", "=", website.id)], limit=1)
write_arch(page.view_id, fill(open(D + "home.xml").read()))
page.write({
    "website_meta_title": "El Chicharito | Hot dogs y postres en Cuenca",
    "website_meta_description": "Hot dogs gigantes con Pepsi incluida, comida rápida y postres: cheesecakes, red velvet, torta de chocolate, colada morada y guaguas de pan. Cuenca, Ecuador.",
    "website_meta_keywords": "hot dogs, chicharito, comida rápida, postres, cheesecake, red velvet, colada morada, Cuenca",
})

# 3) páginas propias: comida rápida y postres
def ensure_page(url, name, key, fname):
    view = V.search([("key", "=", key), ("website_id", "=", website.id)], limit=1)
    arch = fill(open(D + fname).read().replace("{KEY}", key))
    if not view:
        view = V.create({"name": name, "type": "qweb", "key": key, "website_id": website.id, "arch_db": arch})
    else:
        write_arch(view, arch)
    pg = env["website.page"].search([("url", "=", url), ("website_id", "=", website.id)], limit=1)
    vals = {"url": url, "name": name, "view_id": view.id, "website_id": website.id, "website_published": True, "is_published": True}
    if pg:
        pg.write(vals)
    else:
        env["website.page"].create(vals)
ensure_page("/comida-rapida", "Comida rápida", "ebal_chicharito.comida_rapida", "comida.xml")
ensure_page("/postres", "Postres", "ebal_chicharito.postres", "postres.xml")

# 4) pie de página (vista propia del sitio)
VW = V.with_context(website_id=website.id)
footer = VW.search([("key", "=", "website.footer_custom"), ("website_id", "in", (False, website.id))], order="website_id", limit=1)
for lang in langs:
    footer.with_context(lang=lang, website_id=website.id).write({"arch_db": fill(open(D + "footer.xml").read())})
cp = VW.search([("key", "=", "website.footer_copyright_company_name"), ("website_id", "in", (False, website.id))], order="website_id", limit=1)
new = ('<data inherit_id="website.layout">\n    <xpath expr="//footer//span[hasclass(\'o_footer_copyright_name\')]" position="replace">\n'
       '        <span class="o_footer_copyright_name me-2">© El Chicharito · Sabores que sorprenden</span>\n    </xpath>\n</data>')
for lang in langs:
    cp.with_context(lang=lang, website_id=website.id).write({"arch_db": new})

# 5) menú
Menu = env["website.menu"]
root = website.menu_id
want = [("Inicio", "/"), ("Comida rápida", "/comida-rapida"), ("Postres", "/postres"), ("Visítanos", "/#visitanos"), ("Contáctenos", "/contactus")]
kids = Menu.search([("website_id", "=", website.id), ("parent_id", "=", root.id)])
by_url = {m.url: m for m in kids}
for seq, (name, url) in enumerate(want, start=1):
    m = by_url.get(url) or Menu.create({"name": name, "url": url, "parent_id": root.id, "website_id": website.id})
    m.write({"name": name, "sequence": seq * 10})
for m in kids:
    if m.url not in dict((u, 1) for _n, u in want) and not m.child_id:
        m.unlink()

# 5b) textos de ejemplo de Odoo (teléfono +1 555…, "My Company") -> datos reales, con copia propia del sitio
def clean(arch):
    for x, y in [("tel:+1 555-555-5556", "tel:+593995839890"), ("+1 555-555-5556", "099 583 9890"), ("My Company", "El Chicharito"), ("Mi Compañía", "El Chicharito"), ("3575 Fake Buena Vista Avenue", "Calle del Hinojo y calle del Matorral, Cuenca")]:
        arch = arch.replace(x, y)
    arch = re.sub(r"\s*<li>(?:(?!</li>).)*?(?:example\.com|ejemplo\.com)(?:(?!</li>).)*?</li>", "", arch, flags=re.S)
    return arch
for key in ("website.header_text_element", "website.contactus", "website.contactus_thanks"):
    generic = V.search([("key", "=", key), ("website_id", "=", False)], limit=1)
    target = V.search([("key", "=", key), ("website_id", "=", website.id)], limit=1)
    if not target and generic:
        generic.with_context(website_id=website.id).write({"arch_db": generic.arch_db})
        target = V.search([("key", "=", key), ("website_id", "=", website.id)], limit=1)
    for lang in langs if target else []:
        tl = target.with_context(lang=lang, no_cow=True)
        new_arch = clean(tl.arch_db)
        if new_arch != tl.arch_db:
            tl.write({"arch_db": new_arch})

# 6) sitio: estilos, logo, ícono
def b64(path):
    return base64.b64encode(open(D + "assets/" + path, "rb").read())
website.write({"custom_code_head": open(D + "head.html").read(), "logo": b64("logo.webp"), "favicon": b64("icono.png"), "name": "El Chicharito"})

# 7) postres en el inventario (sin precio), para usarlos en el punto de venta
Cat = env["pos.category"]
cat = Cat.search([("name", "=", "Postres")], limit=1) or Cat.create({"name": "Postres"})
POSTRES = [("Cheesecake de fresa (porción)", "cheesecake"), ("Cheesecake de fresa (entero)", "cheesecake_entero"),
           ("Torta de chocolate (porción)", "torta_chocolate"), ("Torta de chocolate (entera)", "torta_chocolate_entera"),
           ("Red velvet (porción)", "red_velvet"), ("Red velvet (entera)", "red_velvet_entera"),
           ("Galletas", "galletas"), ("Colada morada", "colada_morada"), ("Guaguas de pan", "guaguas")]
Tpl = env["product.template"]
tax = env["account.tax"].search([("type_tax_use", "=", "sale"), ("amount", "=", 15), ("amount_type", "=", "percent")], limit=1)
made = 0
for pname, img in POSTRES:
    if Tpl.search_count([("name", "=", pname)]):
        continue
    Tpl.create({"name": pname, "list_price": 0.0, "type": "consu", "is_storable": False, "sale_ok": True,
                "available_in_pos": True, "pos_categ_ids": [(6, 0, cat.ids)], "image_1920": b64(img + ".webp"),
                "taxes_id": [(6, 0, tax.ids)]})
    made += 1
RESULT = "Sitio de El Chicharito aplicado (%d imágenes; %d postres nuevos en el inventario)." % (len(urls), made)
