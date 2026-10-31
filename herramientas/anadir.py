#!/usr/bin/env python3
"""Añade los artículos de un JSON (lista) a feed.json, comprueba el formato y deja solo los 60 más recientes.
Uso: python3 herramientas/anadir.py nuevos.json"""
import json, re, sys, html as H
CATS = {"Ciberseguridad", "Apps", "Automatización", "Sistemas", "Actualidad"}
REQ = ["id", "slug", "title", "category", "date", "excerpt", "metaTitle", "metaDescription", "tags", "html", "sources", "image", "imageAlt"]

def check(p):
    errs = [f"falta {k}" for k in REQ if not p.get(k)]
    if p.get("category") not in CATS: errs.append("categoría no válida")
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", p.get("slug", "")): errs.append("slug no válido")
    if not re.fullmatch(r"https://images\.unsplash\.com/[A-Za-z0-9_\-./=?&%]+", p.get("image", "")): errs.append("la foto tiene que ser de images.unsplash.com")
    text = re.sub(r"<[^>]+>", " ", p.get("html", ""))
    words = len(H.unescape(text).split())
    if words < 350: errs.append(f"artículo corto ({words} palabras, mínimo 350)")
    if len(p.get("metaTitle", "")) > 60: errs.append("metaTitle > 60")
    if not 110 <= len(p.get("metaDescription", "")) <= 165: errs.append("metaDescription fuera de 110-165")
    if "<h2>" not in p.get("html", ""): errs.append("sin subtítulos <h2>")
    if not all(s.get("url", "").startswith("https://") for s in p.get("sources", [])): errs.append("fuente sin https")
    return errs

new = json.load(open(sys.argv[1], encoding="utf-8"))
try:
    feed = json.load(open("feed.json", encoding="utf-8"))
except FileNotFoundError:
    feed = {"posts": []}
ids = {p["id"] for p in feed["posts"]}
slugs = {p["slug"] for p in feed["posts"]}
bad = False
for p in new:
    e = check(p)
    if p["id"] in ids or p["slug"] in slugs: e.append("repetido (id o slug ya en el feed)")
    if e:
        bad = True
        print("✗", p.get("id"), "→", "; ".join(e))
    else:
        print("✓", p["id"], "·", p["title"])
if bad:
    sys.exit(1)
feed["posts"] = sorted(new + feed["posts"], key=lambda p: p["date"], reverse=True)[:60]
feed["updated"] = max(p["date"] for p in feed["posts"])
json.dump(feed, open("feed.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"feed.json: {len(feed['posts'])} artículos")
