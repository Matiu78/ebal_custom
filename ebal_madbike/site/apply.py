# Arma el sitio de Madbike (MDBK Racing Suspensions): portada, servicios, tienda y sección INGCO. Idempotente.
# Lo ejecuta ebal_site_builder (ventana «Aplicar sitio de Madbike»). No toca precios, stock, nombres ni publicación de productos.
import base64, os, re

website = env["website"].browse(1)
langs = env["res.lang"].search([]).mapped("code")
if "en_US" not in langs:
    langs.append("en_US")
WA_NUM = "593998724316"
WA = "https://wa.me/" + WA_NUM

# ---------------------------------------------------------------- imágenes
Att = env["ir.attachment"].sudo()
MIME = {".png": "image/png", ".webp": "image/webp", ".jpg": "image/jpeg"}
urls = {}
for fn in sorted(os.listdir(D + "assets")):
    raw = open(D + "assets/" + fn, "rb").read()
    name = "madbike_web_" + fn
    att = Att.search([("name", "=", name), ("res_model", "=", "website"), ("res_id", "=", website.id)], limit=1)
    vals = {"name": name, "datas": base64.b64encode(raw), "mimetype": MIME[os.path.splitext(fn)[1]],
            "public": True, "res_model": "website", "res_id": website.id}
    if att:
        att.write(vals)
    else:
        att = Att.create(vals)
    urls[fn] = "/web/image/%s-%s/%s" % (att.id, att.checksum[:8], fn)

# ---------------------------------------------------------------- categorías de la tienda: INGCO y sus subcategorías
PC = env["product.public.category"]
def public_cat(name, parent=None, seq=10):
    rec = PC.search([("name", "=", name), ("parent_id", "=", parent.id if parent else False)], limit=1)
    if not rec:
        rec = PC.create({"name": name, "parent_id": parent.id if parent else False, "sequence": seq})
    return rec
ingco = public_cat("INGCO", None, 5)
subs = [public_cat(n, ingco, i * 10) for i, n in enumerate(
    ["Herramientas eléctricas", "Herramientas manuales", "Jardinería", "Accesorios y consumibles"], start=1)]
slug = lambda rec: env["ir.http"]._slug(rec)

# ---------------------------------------------------------------- tarjetas de producto (portada y /ingco)
def card(var="p"):
    return '''<a class="mb-card" t-att-href="%(v)s.website_url">
                    <span t-attf-class="mb-card-img #{'' if %(v)s.image_128 else 'mb-noimg'}">
                        <img t-if="%(v)s.image_128" t-att-src="website.image_url(%(v)s, 'image_512')" t-att-alt="%(v)s.name" loading="lazy"/>
                        <img t-else="" src="{{img:logo_madbike.png}}" alt="" loading="lazy"/>
                    </span>
                    <span class="mb-card-body">
                        <span class="mb-card-code" t-out="%(v)s.default_code or ''"/>
                        <span class="mb-card-name" t-out="%(v)s.name"/>
                        <span class="mb-card-price" t-if="%(v)s.list_price" t-out="prices.get(%(v)s.id, {}).get('price_reduce', %(v)s.list_price)" t-options="{'widget': 'monetary', 'display_currency': website.currency_id}"/>
                        <span class="mb-card-price mb-ask" t-else="">Consultar precio</span>
                    </span>
                </a>''' % {"v": var}

def row(title, sub, link, domain, dark=False):
    return '''<t t-set="items" t-value="request.env['product.template'].search(%(domain)s, order='id desc', limit=5)"/>
<t t-set="prices" t-value="items._get_sales_prices(website)"/>
<section t-if="items" class="mb-sec %(cls)s" data-name="%(title)s">
    <div class="mb-wrap">
        <div class="mb-sec-head"><h2 class="mb-h">%(title)s<small>%(sub)s</small></h2></div>
        <div class="mb-cards">
            <t t-foreach="items" t-as="p">
                %(card)s
            </t>
        </div>
        <p class="mt-4"><a class="mb-btn mb-btn-dark" href="%(link)s">Ver todo</a></p>
    </div>
</section>''' % {"cls": "mb-sec-grey" if dark else "", "title": title, "sub": sub, "link": link,
                 "domain": domain, "card": card()}

INGCO_ROW = row("Novedades INGCO", "Lo último en herramientas", "/ingco",
                "[('is_published','=',True),('public_categ_ids','child_of',%d)]" % ingco.id, dark=True)
SHOP_ROW = row("De la tienda", "Repuestos, lubricantes y más", "/shop",
               "[('is_published','=',True)]")

def fill(text):
    subs_html = "\n".join('            <a href="/shop/category/%s">%s</a>' % (slug(s), s.name) for s in subs)
    for a, b in (("{{INGCO_ROW}}", INGCO_ROW), ("{{SHOP_ROW}}", SHOP_ROW), ("{{INGCO_SUBS}}", subs_html),
                 ("{{INGCO_ID}}", str(ingco.id)), ("{{INGCO_SLUG}}", slug(ingco)), ("{{WA}}", WA)):
        text = text.replace(a, b)
    # las imágenes van DESPUÉS: las filas también las usan
    return re.sub(r"\{\{img:([^}]+)\}\}", lambda m: urls[m.group(1)], text)

V = env["ir.ui.view"]
VW = V.with_context(website_id=website.id)

def write_arch(view, arch):
    for lang in langs:
        view.with_context(lang=lang).write({"arch_db": arch})

# portada
page = env["website.page"].search([("url", "=", "/"), ("website_id", "=", website.id)], limit=1)
write_arch(page.view_id, fill(open(D + "home.xml").read()))
page.write({
    "website_meta_title": "MDBK Racing Suspensions | Suspensión y mecánica de competencia en Cuenca",
    "website_meta_description": "Taller de suspensión, mecánica y preparación de competencia en Cuenca. Calibración de chasis, diagnóstico eléctrico, repuestos, lubricantes y herramientas INGCO.",
    "website_meta_keywords": "suspensión, calibración de chasis, rally, mecánica, Cuenca, INGCO, repuestos",
})

# página /ingco
iv = V.search([("key", "=", "ebal_madbike.ingco_page"), ("website_id", "=", website.id)], limit=1)
arch = fill(open(D + "ingco.xml").read())
if iv:
    write_arch(iv, arch)
else:
    iv = V.create({"name": "INGCO", "key": "ebal_madbike.ingco_page", "type": "qweb", "arch_db": arch,
                   "website_id": website.id, "active": True})
    write_arch(iv, arch)
ipage = env["website.page"].search([("url", "=", "/ingco"), ("website_id", "=", website.id)], limit=1)
if not ipage:
    ipage = env["website.page"].create({"url": "/ingco", "view_id": iv.id, "website_id": website.id,
                                        "is_published": True, "website_indexed": True})
ipage.write({
    "website_meta_title": "Herramientas INGCO | MDBK Racing Suspensions",
    "website_meta_description": "Herramientas eléctricas, manuales, de jardinería y accesorios INGCO en Cuenca.",
})

# pie de página (copia propia del sitio)
footer = VW.search([("key", "=", "website.footer_custom"), ("website_id", "in", (False, website.id))], order="website_id", limit=1)
for lang in langs:
    footer.with_context(lang=lang, website_id=website.id).write({"arch_db": fill(open(D + "footer.xml").read())})

# opciones de la tienda: botón de agregar al carrito en el listado y categorías al costado
for key in ("website_sale.products_add_to_cart", "website_sale.products_categories"):
    v = VW.search([("key", "=", key), ("website_id", "in", (False, website.id))], order="website_id", limit=1)
    if v and not v.active:
        v.with_context(website_id=website.id).write({"active": True})

# menú
Menu = env["website.menu"]
root = website.menu_id
want = [("Inicio", "/"), ("Servicios", "/#servicios"), ("Tienda", "/shop"), ("INGCO", "/ingco"),
        ("Consultar orden", "/consultar-orden"), ("Reservas", "/appointment"), ("Contáctenos", "/contactus")]
kids = Menu.search([("website_id", "=", website.id), ("parent_id", "=", root.id)])
by_url = {m.url: m for m in kids}
if not env["ir.module.module"].sudo().search_count([("name", "=", "website_slides"), ("state", "=", "installed")]):
    stale = by_url.pop("/slides", None)
    if stale:
        stale.unlink()
for seq, (name, url) in enumerate(want, start=1):
    m = by_url.get(url) or Menu.create({"name": name, "url": url, "parent_id": root.id, "website_id": website.id})
    for lang in langs:
        m.with_context(lang=lang).write({"name": name, "sequence": seq * 10})

# textos de ejemplo de Odoo -> datos reales
PH = [("tel:+1 555-555-5556", "tel:+593998724316"), ("+1 555-555-5556", "099 872 4316"),
      ("info@yourcompany.example.com", "facturasmadbike@gmail.com"), ("info@suempresa.ejemplo.com", "facturasmadbike@gmail.com"),
      ("info@sucompañía.example.com", "facturasmadbike@gmail.com"),
      ("3575 Fake Buena Vista Avenue", "Av. de las Américas, Cuenca"),
      ("My Company", "MDBK Racing Suspensions"), ("Mi Compañía", "MDBK Racing Suspensions")]
for key in ("website.contactus", "website.contactus_thanks"):
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
       '        <span class="o_footer_copyright_name me-2">© MDBK Racing Suspensions</span>\n    </xpath>\n</data>')
if cp:
    for lang in langs:
        cp.with_context(lang=lang, website_id=website.id).write({"arch_db": new})

# sitio: estilos, logo, ícono, idioma y tienda
head = open(D + "head.html").read()
def b64(fn):
    return base64.b64encode(open(D + "assets/" + fn, "rb").read())
es = env["res.lang"].search([("code", "=", "es_EC")], limit=1) or env["res.lang"].search([("code", "=", "es_ES")], limit=1)
website.write({
    "name": "MDBK Racing Suspensions", "custom_code_head": head, "logo": b64("logo_madbike.png"), "favicon": b64("icono_madbike.png"),
    "shop_ppg": 24, "shop_ppr": 4, "shop_default_sort": "publish_date desc",
    **({"default_lang_id": es.id} if es else {}),
})
RESULT = "Sitio de Madbike aplicado (portada, /ingco, tienda, menú y pie)."
