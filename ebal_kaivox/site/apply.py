# Arma la tienda en línea de Kaivox (website 1) en una base con website_sale instalado. Idempotente.
# Lo ejecuta ebal_site_builder (ventana «Aplicar sitio de Kaivox»). No cambia precios, stock ni nombres de productos.
import base64, os, re
ns = {}
exec(open(D + "classify.py").read(), ns)
CATS, OTHER, EXCLUDE, classify = ns["CATS"], ns["OTHER"], ns["EXCLUDE"], ns["classify"]

website = env["website"].browse(1)
langs = env["res.lang"].search([]).mapped("code")
if "en_US" not in langs:
    langs.append("en_US")
WA = "593990941947"

# ---------------------------------------------------------------- imágenes
Att = env["ir.attachment"].sudo()
MIME = {".png": "image/png", ".webp": "image/webp", ".jpg": "image/jpeg"}
urls = {}
for fn in sorted(os.listdir(D + "assets")):
    raw = open(D + "assets/" + fn, "rb").read()
    name = "kaivox_web_" + fn
    att = Att.search([("name", "=", name), ("res_model", "=", "website"), ("res_id", "=", website.id)], limit=1)
    vals = {"name": name, "datas": base64.b64encode(raw), "mimetype": MIME[os.path.splitext(fn)[1]],
            "public": True, "res_model": "website", "res_id": website.id}
    if att:
        att.write(vals)
    else:
        att = Att.create(vals)
    urls[fn] = "/web/image/%s-%s/%s" % (att.id, att.checksum[:8], fn)

# ---------------------------------------------------------------- categorías de la tienda
ORDER = ["celulares", "audifonos", "parlantes", "cargadores", "cables", "computacion", "memorias", "micas",
         "soportes", "iluminacion", "relojes", "pilas", "chips", "otros"]
LABELS = {k: lbl for k, lbl, _rx in CATS}
LABELS[OTHER[0]] = OTHER[1]
ICONS = {
    "celulares": '<rect x="7" y="2" width="10" height="20" rx="2"/><path d="M11 18h2"/>',
    "audifonos": '<path d="M4 14v-2a8 8 0 0 1 16 0v2"/><rect x="3" y="14" width="4" height="6" rx="1.5"/><rect x="17" y="14" width="4" height="6" rx="1.5"/>',
    "parlantes": '<rect x="6" y="2" width="12" height="20" rx="2"/><circle cx="12" cy="15" r="3.5"/><circle cx="12" cy="7" r="1"/>',
    "cargadores": '<path d="M9 2v5M15 2v5M7 7h10v4a5 5 0 0 1-10 0z"/><path d="M12 16v6"/>',
    "cables": '<path d="M3 18c4 0 3-6 7-6s3 6 7 6h4"/><path d="M4 6h4M16 6h4M6 4v4M18 4v4"/>',
    "computacion": '<rect x="3" y="4" width="18" height="12" rx="2"/><path d="M8 20h8M12 16v4"/>',
    "memorias": '<path d="M7 3h7l4 4v14H7z"/><path d="M10 7v3M13 7v3"/>',
    "micas": '<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/><path d="m9 12 2 2 4-4"/>',
    "soportes": '<rect x="8" y="3" width="8" height="12" rx="1.5"/><path d="M6 21h12M12 15v6"/>',
    "iluminacion": '<path d="M9 18h6M10 21h4"/><path d="M12 3a6 6 0 0 0-4 10.5c.7.7 1 1.5 1 2.5h6c0-1 .3-1.8 1-2.5A6 6 0 0 0 12 3z"/>',
    "relojes": '<rect x="7" y="6" width="10" height="12" rx="3"/><path d="M9 6l1-4h4l1 4M9 18l1 4h4l1-4"/>',
    "pilas": '<rect x="3" y="8" width="16" height="9" rx="2"/><path d="M21 11v3M8 12h4"/>',
    "chips": '<rect x="5" y="3" width="14" height="18" rx="2"/><path d="M5 9h14M5 15h14M10 9v12"/>',
    "otros": '<path d="M21 8l-9-5-9 5v8l9 5 9-5z"/><path d="M3 8l9 5 9-5M12 13v8"/>',
}
PC = env["product.public.category"]
cat = {}
for seq, key in enumerate(ORDER, start=1):
    label = LABELS[key]
    rec = PC.search([("name", "=", label)], limit=1)
    if not rec:
        rec = PC.create({"name": label, "sequence": seq * 10})
    else:
        rec.sequence = seq * 10
    cat[key] = rec
slug = lambda rec: env["ir.http"]._slug(rec)

# ---------------------------------------------------------------- productos: categoría y publicación
Tmpl = env["product.template"].with_context(active_test=True)
quants = env["stock.quant"].read_group(
    [("location_id.usage", "=", "internal")], ["product_id", "quantity:sum"], ["product_id"])
qty_by_product = {g["product_id"][0]: g["quantity"] for g in quants if g["product_id"]}
by_cat, publish_ids, counts = {}, [], {}
for t in Tmpl.search([("sale_ok", "=", True)]):
    # el nombre que ve el cliente (español); el inglés puede ser un nombre viejo distinto
    name = (t.with_context(lang="es_EC").name or t.with_context(lang="es_ES").name or t.with_context(lang=None).name or "")
    if EXCLUDE.match(name.strip()) or t.type == "service" or (t.list_price or 0) <= 0:
        continue
    qty = sum(qty_by_product.get(p.id, 0.0) for p in t.product_variant_ids)
    if qty <= 0:
        continue
    key = classify(name)
    by_cat.setdefault(key, []).append(t.id)
    counts[key] = counts.get(key, 0) + 1
    publish_ids.append(t.id)
shop_cats = PC.browse([c.id for c in cat.values()])
for key, ids in by_cat.items():
    # (6, 0, [...]) reemplaza TODO: la categoría vieja no se queda aunque la clasificación cambie
    Tmpl.browse(ids).write({"public_categ_ids": [(6, 0, [cat[key].id])]})
# lo que ya no cumple (sin stock, servicio, sin precio) se despublica: la tienda solo muestra lo que se puede comprar
stale = Tmpl.search([("is_published", "=", True), ("id", "not in", publish_ids)])
if stale:
    stale.write({"is_published": False})
for i in range(0, len(publish_ids), 200):
    Tmpl.browse(publish_ids[i:i + 200]).write({
        "is_published": True, "website_id": False,
        "show_availability": True, "available_threshold": 3.0, "allow_out_of_stock_order": False,
    })

# ---------------------------------------------------------------- sustituciones de texto de las plantillas
def tiles():
    out = []
    for key in ORDER:
        n = counts.get(key, 0)
        if not n:
            continue
        out.append('            <a class="kx-tile" href="/shop/category/%s"><span class="kx-ico"><svg viewBox="0 0 24 24">%s</svg></span><span>%s<small>%d productos</small></span></a>'
                   % (slug(cat[key]), ICONS[key], LABELS[key], n))
    return "\n".join(out)

ROW_KEYS = [("celulares", "Celulares y tablets", "Lo último en smartphones"),
            ("audifonos", "Audífonos y micrófonos", "Sonido para todo el día"),
            ("cargadores", "Cargadores y power banks", "Energía para tus equipos"),
            ("parlantes", "Parlantes y radios", "Música a todo volumen"),
            ("computacion", "Computación, TV y gaming", "Mouse, routers, controles y más")]

def rows():
    out = []
    for key, title, sub in ROW_KEYS:
        if not counts.get(key):
            continue
        out.append('''<section class="kx-sec" data-name="%(title)s">
    <div class="kx-wrap">
        <div class="kx-sec-head"><h2 class="kx-h">%(title)s<small>%(sub)s</small></h2><a class="kx-more" href="/shop/category/%(slug)s">Ver todo →</a></div>
        <div class="kx-grid">
            <t t-foreach="request.env['product.template'].search([('is_published','=',True),('public_categ_ids','child_of',%(id)d)], order='id desc', limit=8)" t-as="p">
                <t t-set="c" t-value="p._get_combination_info(only_template=True)"/>
                <div class="kx-card">
                    <a t-att-href="p.website_url" t-attf-class="kx-card-img kx-card-link #{'' if p.image_128 else 'kx-noimg'}">
                        <img t-if="p.image_128" t-att-src="website.image_url(p, 'image_512')" t-att-alt="p.name" loading="lazy"/>
                        <img t-else="" src="{{img:simbolo_kaivox.png}}" alt="" loading="lazy"/>
                    </a>
                    <div class="kx-card-body">
                        <a class="kx-card-title" t-att-href="p.website_url" t-out="p.name"/>
                        <span class="kx-price" t-out="c['price']" t-options="{'widget': 'monetary', 'display_currency': website.currency_id}"/>
                        <form action="/shop/cart/update" method="post">
                            <input type="hidden" name="csrf_token" t-att-value="request.csrf_token()"/>
                            <input type="hidden" name="product_id" t-att-value="p.product_variant_id.id"/>
                            <input type="hidden" name="add_qty" value="1"/>
                            <button type="submit" class="kx-add">Agregar al carrito</button>
                        </form>
                    </div>
                </div>
            </t>
        </div>
    </div>
</section>''' % {"title": title, "sub": sub, "slug": slug(cat[key]), "id": cat[key].id})
    return "\n".join(out)

NAV_KEYS = ["celulares", "audifonos", "parlantes", "cargadores", "cables", "computacion", "micas", "memorias", "relojes"]

def nav():
    return "\n".join('                <a href="/shop/category/%s">%s</a>' % (slug(cat[k]), LABELS[k]) for k in NAV_KEYS if counts.get(k))

def foot():
    return "\n".join('                                <li class="mb-2"><a href="/shop/category/%s">%s</a></li>' % (slug(cat[k]), LABELS[k]) for k in NAV_KEYS[:6] if counts.get(k))

def fill(text):
    for a, b in (("{{TILES}}", tiles()), ("{{ROWS}}", rows()), ("{{NAV_CATS}}", nav()), ("{{FOOTER_CATS}}", foot())):
        text = text.replace(a, b)
    # las imágenes van DESPUÉS: las filas y los bloques de arriba también las usan
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
    "website_meta_title": "Kaivox | Celulares y accesorios en Gualaceo",
    "website_meta_description": "Tienda de tecnología en Gualaceo: celulares, audífonos, cargadores, parlantes y accesorios con garantía. Compra en línea y retira en tienda.",
    "website_meta_keywords": "celulares, audífonos, cargadores, accesorios, tecnología, Gualaceo",
})

# pie de página (copia propia del sitio)
footer = VW.search([("key", "=", "website.footer_custom"), ("website_id", "in", (False, website.id))], order="website_id", limit=1)
for lang in langs:
    footer.with_context(lang=lang, website_id=website.id).write({"arch_db": fill(open(D + "footer.xml").read())})

# vistas propias (barra superior + categorías; tarjetas sin foto)
layout = V.search([("key", "=", "website.layout"), ("website_id", "=", False)], limit=1)
for key, fname, parent in (("kaivox_web.chrome", "chrome.xml", layout),
                           ("kaivox_web.sin_foto", "noimg.xml", V.search([("key", "=", "website_sale.products_item")], limit=1))):
    view = V.search([("key", "=", key), ("website_id", "=", website.id)], limit=1)
    vals = {"name": key, "key": key, "type": "qweb", "inherit_id": parent.id, "mode": "extension",
            "arch_db": fill(open(D + fname).read()), "website_id": website.id, "active": True, "priority": 99}
    if view:
        view.write({"arch_db": vals["arch_db"], "inherit_id": parent.id, "active": True})
    else:
        V.create(vals)

# opciones de la tienda: botón de agregar al carrito en el listado y categorías al costado
for key in ("website_sale.products_add_to_cart", "website_sale.products_categories"):
    v = VW.search([("key", "=", key), ("website_id", "in", (False, website.id))], order="website_id", limit=1)
    if v and not v.active:
        v.with_context(website_id=website.id).write({"active": True})

# encabezado: buscador siempre visible y ancho (como Novicompu); sin los textos de ejemplo ni el botón «Contáctenos»
SEARCH_ARCH = """<data inherit_id="website.placeholder_header_search_box" name="Header Search Bar" active="True">
    <xpath expr="." position="inside">
        <li class="kx-searchli">
            <t t-call="website.header_search_box_input"/>
        </li>
    </xpath>
</data>"""
def own_copy(key):
    v = V.search([("key", "=", key), ("website_id", "=", website.id)], limit=1)
    if not v:
        g = V.search([("key", "=", key), ("website_id", "=", False)], limit=1)
        if g:
            g.with_context(website_id=website.id).write({"arch_db": g.arch_db})
            v = V.search([("key", "=", key), ("website_id", "=", website.id)], limit=1)
    return v
sv = own_copy("website.header_search_box")
for lang in langs:
    sv.with_context(lang=lang, no_cow=True).write({"arch_db": SEARCH_ARCH})
for key in ("website.header_text_element", "website.header_call_to_action"):
    own_copy(key).with_context(no_cow=True).write({"active": False})

# buscador también en el celular: debajo del logo, siempre a la vista
MOBILE_ARCH = """<data inherit_id="website.template_header_mobile" name="Kaivox buscador en el celular" active="True" priority="30">
    <xpath expr="//div[hasclass('o_main_nav')]" position="inside">
        <div class="kx-mobile-search w-100 order-last pt-2 pb-2">
            <t t-call="website.header_search_box_input"><t t-set="limit" t-valuef="0"/></t>
        </div>
    </xpath>
</data>"""
mv = V.search([("key", "=", "kaivox_web.buscador_movil"), ("website_id", "=", website.id)], limit=1)
mparent = V.search([("key", "=", "website.template_header_mobile"), ("website_id", "=", False)], limit=1)
mvals = {"name": "kaivox_web.buscador_movil", "key": "kaivox_web.buscador_movil", "type": "qweb", "inherit_id": mparent.id,
         "mode": "extension", "arch_db": MOBILE_ARCH, "website_id": website.id, "active": True, "priority": 99}
if mv:
    mv.write({"arch_db": MOBILE_ARCH, "inherit_id": mparent.id, "active": True})
else:
    V.create(mvals)

# menú
Menu = env["website.menu"]
root = website.menu_id
want = [("Inicio", "/"), ("Tienda", "/shop"), ("Contáctenos", "/contactus")]
kids = Menu.search([("website_id", "=", website.id), ("parent_id", "=", root.id)])
by_url = {m.url: m for m in kids}
for seq, (name, url) in enumerate(want, start=1):
    m = by_url.get(url) or Menu.create({"name": name, "url": url, "parent_id": root.id, "website_id": website.id})
    m.write({"name": name, "sequence": seq * 10})

# texto de la ficha de producto (reemplaza el de Odoo sobre devolución y envío)
pt = VW.search([("key", "=", "website_sale.product_custom_text"), ("website_id", "=", website.id)], limit=1)
if not pt:
    g = V.search([("key", "=", "website_sale.product_custom_text"), ("website_id", "=", False)], limit=1)
    if g:
        g.with_context(website_id=website.id).write({"arch_db": g.arch_db})
        pt = VW.search([("key", "=", "website_sale.product_custom_text"), ("website_id", "=", website.id)], limit=1)
if pt:
    for lang in langs:
        pt.with_context(lang=lang, no_cow=True).write({"arch_db": open(D + "product_text.xml").read()})

# textos de ejemplo de Odoo -> datos reales
PH = [("tel:+1 555-555-5556", "tel:+593990941947"), ("+1 555-555-5556", "099 094 1947"),
      ("info@yourcompany.example.com", "kaivox03@gmail.com"), ("info@suempresa.ejemplo.com", "kaivox03@gmail.com"),
      ("info@sucompañía.example.com", "kaivox03@gmail.com"),
      ("3575 Fake Buena Vista Avenue", "Calle Colón, entre Luis Cordero y Vicente Peña Reyes, Gualaceo"),
      ("My Company", "Kaivox"), ("Mi Compañía", "Kaivox")]
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
       '        <span class="o_footer_copyright_name me-2">© Kaivox · Innovación sin límites</span>\n    </xpath>\n</data>')
for lang in langs:
    cp.with_context(lang=lang, website_id=website.id).write({"arch_db": new})

# sitio: estilos, logo, ícono, idioma y tienda
head = open(D + "head.html").read()
def b64(fn):
    return base64.b64encode(open(D + "assets/" + fn, "rb").read())
es = env["res.lang"].search([("code", "=", "es_EC")], limit=1) or env["res.lang"].search([("code", "=", "es_ES")], limit=1)
website.write({
    "name": "Kaivox", "custom_code_head": head, "logo": b64("logo_kaivox.png"), "favicon": b64("icono_kaivox.png"),
    "shop_ppg": 24, "shop_ppr": 4, "shop_default_sort": "create_date desc", "show_line_subtotals_tax_selection": "tax_included",
    **({"default_lang_id": es.id} if es else {}),
})
RESULT = "Tienda de Kaivox aplicada: %d imágenes, %d productos publicados en %d categorías." % (len(urls), len(publish_ids), len([k for k in ORDER if counts.get(k)]))
