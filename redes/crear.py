#!/usr/bin/env python3
"""Publicaciones de redes sociales de Javertix (Instagram y Facebook).

Uso:
  python3 redes/crear.py nuevos.json            # comprueba, genera las imágenes y lo añade a redes/feed.json
  python3 redes/crear.py nuevos.json --prueba   # solo genera las imágenes en redes/prueba/ para revisarlas

nuevos.json es una lista de publicaciones. Ver redes/README.md para el formato y las plantillas.
La web (javertix.site) lee redes/feed.json cada 15 minutos y publica cada una a su hora.
"""
import datetime as dt
import html
import json
import os
import re
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
PLANTILLAS = AQUI / "plantillas"
FEED = AQUI / "feed.json"
DIAS_GUARDADOS = 21

TIPOS = {"meme", "noticia", "dato", "tip", "presentacion", "servicio"}
FORMATOS = {"post", "historia", "reel", "explicado"}
PLANTILLAS_VALIDAS = {
    "comparacion", "nadie-yo", "chat", "post", "expectativa", "escala", "clasico",   # memes
    "terminal", "codigo", "error",                                                    # memes «nativos» de informática
    "portada", "puntos", "cierre",                                                    # noticias
    "dato", "texto", "logo", "tip",                                                          # datos y genéricas
}
# Palabras que nunca deben salir en una publicación de la marca
PROHIBIDAS = re.compile(r"\b(put[ao]s?|mierda|joder|cabr[oó]n\w*|gilipollas|coñ[oa]|polla|follar|maric[oó]n\w*|subnormal|retrasad[oa]|idiotas?|imb[eé]cil\w*)\b", re.I)
UNSPLASH = re.compile(r"https://images\.unsplash\.com/[A-Za-z0-9_\-./=?&%]+")


EMOJIS = {f.stem for f in (PLANTILLAS / "emoji").glob("*.svg")}


def emojis(s):
    """Cambia cada emoji por su imagen de Twemoji (así se ven igual en cualquier sitio)."""
    out, i = [], 0
    while i < len(s):
        hecho = False
        if ord(s[i]) >= 0x2000:
            for largo in range(min(10, len(s) - i), 0, -1):
                cps = [f"{ord(c):x}" for c in s[i:i + largo]]
                for nombre in ("-".join(cps), "-".join(c for c in cps if c != "fe0f")):
                    if nombre in EMOJIS:
                        out.append(f'<img class="emo" src="emoji/{nombre}.svg" alt="">')
                        i += largo
                        hecho = True
                        break
                if hecho:
                    break
        if not hecho:
            out.append(s[i])
            i += 1
    return "".join(out)


def e(s):
    """Escapa el texto, convierte saltos de línea, **negrita** y emojis."""
    s = html.escape(str(s or ""))
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    return emojis(s).replace("\n", "<br>")


def pie(n, total, oscuro=False):
    derecha = f'<span class="contador">{n}/{total}</span>' if total > 1 else '<span class="web">javertix.site</span>'
    return f'<div class="pie"><div class="marca"><img src="icono.png" alt="">JAVERTIX</div>{derecha}</div>'


def slide_html(d, n, total, tipo):
    p = d["plantilla"]
    fondo = d.get("fondo")
    if p == "comparacion":
        filas = "".join(
            f'<div class="fila {"no" if i == 0 and len(d["filas"]) == 2 else "si" if i == len(d["filas"]) - 1 and len(d["filas"]) == 2 else ""}">'
            f'<div class="lado emoji">{e(f.get("emoji"))}</div><div class="txt">{e(f["texto"])}</div></div>'
            for i, f in enumerate(d["filas"]))
        titulo = f'<div class="meme-titulo">{e(d["titulo"])}</div>' if d.get("titulo") else ""
        body = f'<div class="contenido">{titulo}<div class="filas">{filas}</div></div>'
        clase = fondo or "suave"
    elif p == "nadie-yo":
        lineas = "".join(f'<div><b>{e(l["quien"])}</b> {e(l.get("texto", ""))}</div>' for l in d["lineas"])
        emo = f'<div class="gran-emoji emoji">{e(d["emoji"])}</div>' if d.get("emoji") else ""
        body = f'<div class="contenido"><div class="nadie">{lineas}{emo}</div></div>'
        clase = fondo or "claro"
    elif p == "chat":
        cab = (f'<div class="chat-cab"><div class="avatar emoji">{e(d.get("emoji", "🙂"))}</div>'
               f'<div>{e(d.get("contacto", "Cliente"))}<small>en línea</small></div></div>')
        msgs = "".join(
            f'<div class="burbuja {"yo" if m.get("yo") else "ellos"}">{f"<small>{e(m["de"])}</small>" if m.get("de") else ""}{e(m["texto"])}</div>'
            for m in d["mensajes"])
        titulo = f'<div class="meme-titulo">{e(d["titulo"])}</div>' if d.get("titulo") else ""
        body = f'<div class="contenido">{titulo}<div class="chat">{cab}{msgs}</div></div>'
        clase = fondo or "suave"
    elif p == "post":
        body = (f'<div class="contenido"><div class="post"><div class="post-cab"><img src="icono.png" alt="">'
                f'<div><b>Javertix</b><span>@javertix · {e(d.get("hace", "2 min"))}</span></div></div>'
                f'<div class="post-txt">{e(d["texto"])}</div>'
                f'<div class="post-meta"><span>💬 {e(d.get("respuestas", "128"))}</span><span>🔁 {e(d.get("compartidos", "1,2 mil"))}</span><span>❤️ {e(d.get("megusta", "9,8 mil"))}</span></div></div></div>')
        clase = fondo or "azul"
    elif p == "expectativa":
        paneles = "".join(
            f'<div class="panel"><div class="eti">{e(x["etiqueta"])}</div><div class="emo emoji">{e(x.get("emoji", ""))}</div><div class="txt">{e(x["texto"])}</div></div>'
            for x in d["paneles"])
        titulo = f'<div class="meme-titulo">{e(d["titulo"])}</div>' if d.get("titulo") else ""
        body = f'<div class="contenido">{titulo}<div class="paneles">{paneles}</div></div>'
        clase = fondo or "claro"
    elif p == "escala":
        luces = ["🙂", "🧠", "💡", "✨", "🌌"]
        niveles = "".join(
            f'<div class="nivel"><div class="txt">{e(x["texto"])}</div><div class="luz emoji" style="background:rgba(232,163,23,{0.08 + i * 0.2:.2f})">{e(x.get("emoji") or luces[min(i, 4)])}</div></div>'
            for i, x in enumerate(d["niveles"]))
        titulo = f'<div class="meme-titulo">{e(d["titulo"])}</div>' if d.get("titulo") else ""
        body = f'<div class="contenido">{titulo}<div class="escala">{niveles}</div></div>'
        clase = fondo or "oscuro"
    elif p == "clasico":
        body = (f'<div class="contenido"><div class="clasico"><div class="linea">{e(d["arriba"])}</div>'
                f'<div class="gran-emoji emoji">{e(d["emoji"])}</div><div class="linea">{e(d.get("abajo", ""))}</div></div></div>')
        clase = fondo or "claro"
    elif p == "terminal":
        # Terminal: líneas con prompt ($ comando) y salida; la última línea puede ser el remate
        filas = []
        for l in d["lineas"]:
            if l.get("cmd") is not None:
                filas.append(f'<div class="t-l"><span class="t-p">{e(d.get("prompt", "yo@oficina:~$"))}</span> {e(l["cmd"])}</div>')
            else:
                filas.append(f'<div class="t-l t-{l.get("color", "out")}">{e(l.get("out", ""))}</div>')
        titulo = f'<div class="meme-titulo">{e(d["titulo"])}</div>' if d.get("titulo") else ""
        body = (f'<div class="contenido">{titulo}<div class="terminal"><div class="t-barra"><i></i><i></i><i></i>'
                f'<span>{e(d.get("ventana", "bash"))}</span></div><div class="t-cuerpo">{"".join(filas)}<span class="t-cursor"></span></div></div></div>')
        clase = fondo or "oscuro"
    elif p == "codigo":
        # Código con resaltado sencillo: el chiste suele estar en un comentario o en un nombre
        def resaltar(linea):
            tok = re.compile(r'(?P<com>(//|#).*$)|(?P<str>"[^"]*"|\'[^\']*\')|(?P<kw>\b(?:if|else|return|function|const|let|var|def|while|for|true|false|null|None|try|catch|except|throw|new|class|import|from|await|async)\b)')
            out, i = [], 0
            for m in tok.finditer(linea):
                out.append(html.escape(linea[i:m.start()]))
                clase = {"com": "c-com", "str": "c-str", "kw": "c-kw"}[m.lastgroup]
                out.append(f'<span class="{clase}">{html.escape(m.group(0))}</span>')
                i = m.end()
            out.append(html.escape(linea[i:]))
            return emojis("".join(out))
        lineas = "".join(f'<div class="c-l"><span class="c-n">{i}</span><span>{resaltar(l) or "&nbsp;"}</span></div>' for i, l in enumerate(d["codigo"].split("\n"), 1))
        titulo = f'<div class="meme-titulo">{e(d["titulo"])}</div>' if d.get("titulo") else ""
        body = (f'<div class="contenido">{titulo}<div class="editor"><div class="t-barra"><i></i><i></i><i></i><span>{e(d.get("archivo", "main.js"))}</span></div>'
                f'<div class="c-cuerpo">{lineas}</div></div></div>')
        clase = fondo or "oscuro"
    elif p == "error":
        # Ventana de error genérica (sin marcas): título, icono, mensaje y botones
        botones = "".join(f'<span class="{"pri" if i == len(d.get("botones", [])) - 1 else ""}">{e(b)}</span>' for i, b in enumerate(d.get("botones", ["Aceptar"])))
        titulo = f'<div class="meme-titulo">{e(d["titulo"])}</div>' if d.get("titulo") else ""
        body = (f'<div class="contenido">{titulo}<div class="dialogo"><div class="d-barra">{e(d.get("ventana", "Error"))}<span>✕</span></div>'
                f'<div class="d-cuerpo"><div class="d-icono emoji">{e(d.get("emoji", "⚠️"))}</div><div class="d-msg">{e(d["mensaje"])}</div></div>'
                f'<div class="d-botones">{botones}</div></div>'
                + (f'<div class="pie-meme">{e(d["abajo"])}</div>' if d.get("abajo") else "") + '</div>')
        clase = fondo or "suave"
    elif p == "portada":
        return (f'<div class="lienzo portada"><div class="velo"></div>'
                f'<div class="dentro"><span class="etiqueta">{e(d.get("categoria", "Noticia"))}</span><h1>{e(d["titulo"])}</h1>'
                + (f'<p class="medio" style="color:rgba(255,255,255,.85)">{e(d["subtitulo"])}</p>' if d.get("subtitulo") else "")
                + (f'<span class="desliza">Desliza para el resumen →</span>' if total > 1 else "")
                + f'{pie(n, total)}</div></div>')
    elif p == "puntos":
        lis = "".join(f"<li><span>{e(x)}</span></li>" for x in d["puntos"])
        body = f'<div class="contenido"><h2>{e(d["titulo"])}</h2><ol class="puntos">{lis}</ol></div>'
        clase = fondo or "claro"
    elif p == "cierre":
        body = (f'<div class="contenido"><img class="cierre-logo" src="icono.png" alt=""><h2>{e(d["texto"])}</h2>'
                + (f'<p class="medio gris">{e(d["subtexto"])}</p>' if d.get("subtexto") else "")
                + f'<span class="cta">{e(d.get("cta", "Más en javertix.site"))}</span></div>')
        clase = fondo or "azul"
    elif p == "dato":
        top = f'<span class="etiqueta">{e(d.get("etiqueta", "¿Sabías que…?"))}</span>'
        cifra = f'<div class="cifra">{e(d["cifra"])}</div>' if d.get("cifra") else (f'<div class="dato-emoji emoji">{e(d["emoji"])}</div>' if d.get("emoji") else "")
        fuente = f'<p class="fuente gris">Fuente: {e(d["fuente"])}</p>' if d.get("fuente") else ""
        body = f'<div class="contenido">{top}{cifra}<p class="grande">{e(d["texto"])}</p>{fuente}</div>'
        clase = fondo or "amarillo"
    elif p == "tip":
        top = f'<span class="etiqueta">{e(d.get("etiqueta", "Tip"))}</span>'
        emo = f'<div class="dato-emoji emoji">{e(d["emoji"])}</div>' if d.get("emoji") else ""
        lis = ("<ol class=\"puntos\">" + "".join(f"<li><span>{e(x)}</span></li>" for x in d["puntos"]) + "</ol>") if d.get("puntos") else ""
        txt = f'<p class="medio gris">{e(d["texto"])}</p>' if d.get("texto") else ""
        body = f'<div class="contenido">{top}{emo}<h2>{e(d["titulo"])}</h2>{txt}{lis}</div>'
        clase = fondo or "azul"
    elif p == "logo":
        body = (f'<div class="contenido logo-c"><img class="logo-grande" src="logo-completo.png" alt="">'
                + (f'<h2>{e(d["titulo"])}</h2>' if d.get("titulo") else "")
                + (f'<p class="medio gris">{e(d["texto"])}</p>' if d.get("texto") else "") + "</div>")
        clase = fondo or "claro"
    elif p == "texto":
        top = f'<span class="etiqueta">{e(d["etiqueta"])}</span>' if d.get("etiqueta") else ""
        body = f'<div class="contenido">{top}<h2>{e(d["titulo"])}</h2>' + (f'<p class="medio gris">{e(d["texto"])}</p>' if d.get("texto") else "") + "</div>"
        clase = fondo or "claro"
    else:
        raise ValueError(f"plantilla desconocida: {p}")
    return f'<div class="lienzo {clase}">{body}{pie(n, total)}</div>'


def documento(cuerpo, vertical=False):
    return ('<!doctype html><html lang="es"' + (' class="vertical"' if vertical else '') + '><head><meta charset="utf-8">'
            '<link rel="stylesheet" href="fuentes/marca.css">'
            f'<link rel="stylesheet" href="estilos.css"></head><body>{cuerpo}</body></html>')


def textos(p):
    """Todo el texto visible de una publicación (para revisar palabras prohibidas)."""
    return json.dumps([p.get("texto"), p.get("hashtags"), p.get("diapositivas"), p.get("alt"), p.get("guion")], ensure_ascii=False)


VISUALES = {"gancho", "cifra", "barra", "alerta", "lista", "terminal", "escena", "cierre"}


def check_guion(g):
    """Comprueba el guion de un reel con voz (formato v2, ver video.py y README)."""
    from video import emoji as a_emoji
    errs = []
    esc = g.get("escenas") or []
    if not (5 <= len(esc) <= 10):
        errs.append("guion: entre 5 y 10 escenas")
    palabras = 0
    for i, e in enumerate(esc, 1):
        v = e.get("visual") or {}
        tipo = v.get("tipo")
        if e.get("voz", "narrador") not in ("narrador", "jota"):
            errs.append(f"escena {i}: voz tiene que ser narrador o jota")
        if not e.get("texto"):
            errs.append(f"escena {i}: falta texto (lo que se dice)")
        palabras += len(str(e.get("texto", "")).split())
        if tipo not in VISUALES:
            errs.append(f"escena {i}: visual.tipo tiene que ser " + ", ".join(sorted(VISUALES)))
        for k in ("emoji",):
            if v.get(k) and not a_emoji(v[k]):
                errs.append(f"escena {i}: emoji {v[k]!r} no disponible")
        if tipo in ("gancho", "alerta") and (not v.get("titulo") or len(str(v.get("titulo", "")) + str(v.get("destacar", ""))) > 34):
            errs.append(f"escena {i}: {tipo} lleva titulo (+ destacar), entre los dos máx. 34 caracteres")
        if tipo == "escena" and (not (1 <= len(v.get("emojis") or []) <= 3) or len(str(v.get("etiqueta", ""))) > 14):
            errs.append(f"escena {i}: escena lleva 1-3 emojis y una etiqueta de máx. 14 caracteres")
        if tipo == "terminal":
            ls = v.get("lineas") or []
            if not (1 <= len(ls) <= 7) or any(len(str(l.get("cmd") or l.get("out") or "")) > 36 for l in ls):
                errs.append(f"escena {i}: terminal lleva 1-7 líneas de máx. 36 caracteres")
        if tipo in ("cifra", "barra"):
            if v.get("hasta") is None and (tipo == "barra" or not v.get("cifra") or len(str(v["cifra"])) > 8):
                errs.append(f"escena {i}: {tipo} necesita 'hasta' (número que se cuenta) o, solo en cifra, 'cifra' corta (máx. 8)")
            if v.get("hasta") is not None and not isinstance(v["hasta"], (int, float)):
                errs.append(f"escena {i}: 'hasta' tiene que ser un número")
            if len(str(v.get("unidad", ""))) > 6:
                errs.append(f"escena {i}: unidad de máx. 6 caracteres")
        if tipo == "lista":
            ps = v.get("puntos") or []
            if not (2 <= len(ps) <= 3) or any(len(str(p.get("t", "") if isinstance(p, dict) else p)) > 22 for p in ps):
                errs.append(f"escena {i}: la lista lleva 2-3 puntos de máx. 22 caracteres (+ 's' opcional)")
    if esc and (esc[0].get("visual") or {}).get("tipo") not in ("gancho", "escena", "terminal"):
        errs.append("guion: la primera escena es el gancho (gancho, escena o terminal)")
    if esc and (esc[0].get("visual") or {}).get("tipo") == "terminal" and not esc[0]["visual"].get("titulo"):
        errs.append("guion: si el gancho es una terminal, lleva titulo (se tiene que entender sin sonido)")
    if esc and (esc[-1].get("visual") or {}).get("tipo") != "cierre":
        errs.append("guion: la última escena es el cierre")
    if not (60 <= palabras <= 105):
        errs.append(f"guion: {palabras} palabras; tiene que quedar entre 60 y 105 (unos 18-30 s)")
    if not g.get("fuente"):
        errs.append("guion: falta fuente")
    return errs


def check(p):
    errs = []
    obligatorios = ("id", "tipo", "publicar", "texto", "hashtags", "alt") + (("guion",) if p.get("formato") == "explicado" else ("diapositivas",))
    for k in obligatorios:
        if not p.get(k):
            errs.append(f"falta {k}")
    if errs:
        return errs
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}-[a-z0-9]+(-[a-z0-9]+)*", p["id"]):
        errs.append("id no válido (AAAA-MM-DD-algo)")
    if p["tipo"] not in TIPOS:
        errs.append("tipo no válido (meme, noticia, dato, tip, servicio o presentacion)")
    try:
        cuando = dt.datetime.fromisoformat(p["publicar"])
        if cuando.tzinfo is None:
            errs.append("publicar necesita zona horaria (+01:00 / +02:00)")
        elif cuando < dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=1):
            errs.append("la hora de publicar ya ha pasado")
    except ValueError:
        errs.append("publicar no es una fecha ISO")
    if len(p["texto"]) > 1800:
        errs.append("texto > 1800 caracteres")
    tags = p["hashtags"]
    if not (3 <= len(tags) <= 12) or not all(re.fullmatch(r"#[0-9A-Za-zÁÉÍÓÚÜÑáéíóúüñ_]+", t) for t in tags):
        errs.append("hashtags: entre 3 y 12, con # y sin espacios")
    if p.get("enlace") and not p["enlace"].startswith("https://javertix.site/"):
        errs.append("enlace tiene que ser de https://javertix.site/")
    formato = p.get("formato", "post")
    if formato not in FORMATOS:
        errs.append("formato no válido (post, historia o reel)")
    if formato == "explicado":
        errs += check_guion(p["guion"])
        p["diapositivas"] = []
    elif not (1 <= len(p["diapositivas"]) <= 10):
        errs.append("entre 1 y 10 diapositivas")
    if formato == "historia" and len(p["diapositivas"]) > 3:
        errs.append("una historia tiene como mucho 3 imágenes")
    if formato == "reel":
        if not (2 <= len(p["diapositivas"]) <= 8):
            errs.append("un reel tiene entre 2 y 8 diapositivas")
        if any(d.get("plantilla") == "portada" for d in p["diapositivas"]):
            errs.append("los reels no pueden usar la plantilla portada (no hay foto de fondo en vídeo)")
    for i, d in enumerate(p["diapositivas"], 1):
        if d.get("plantilla") not in PLANTILLAS_VALIDAS:
            errs.append(f"diapositiva {i}: plantilla no válida")
        if d.get("plantilla") == "codigo":
            ls = str(d.get("codigo", "")).split("\n")
            if len(ls) > 14 or any(len(l) > 40 for l in ls):
                errs.append(f"diapositiva {i}: código de máx. 14 líneas y 40 caracteres por línea")
        if d.get("plantilla") == "terminal" and not (2 <= len(d.get("lineas") or []) <= 9):
            errs.append(f"diapositiva {i}: la terminal lleva 2-9 líneas")
        if d.get("plantilla") == "portada" and not UNSPLASH.fullmatch(d.get("foto", "")):
            errs.append(f"diapositiva {i}: la foto de portada tiene que ser de images.unsplash.com")
    if PROHIBIDAS.search(textos(p)):
        errs.append("contiene palabras malsonantes: " + ", ".join(sorted({m.group(0) for m in PROHIBIDAS.finditer(textos(p))})))
    if len(p["alt"]) > 1000:
        errs.append("alt > 1000 caracteres")
    return errs


def servidor():
    """Servidor local para las plantillas: Chromium no carga fuentes desde file://."""
    import functools, http.server, threading
    class Silencioso(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    h = functools.partial(Silencioso, directory=str(PLANTILLAS))
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), h)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def video(p, destino, imagenes):
    """Reel: las diapositivas con un zoom suave y fundidos, en MP4 vertical (H.264, 30 fps, con pista de audio en silencio)."""
    import subprocess
    seg = float(p.get("segundos", 3.5))
    fundido = 0.5
    n = len(imagenes)
    args = ["ffmpeg", "-y", "-loglevel", "error"]
    for img in imagenes:
        args += ["-loop", "1", "-t", f"{seg:.2f}", "-i", str(img)]
    args += ["-f", "lavfi", "-t", f"{n * seg - (n - 1) * fundido:.2f}", "-i", "anullsrc=r=44100:cl=stereo"]
    frames = int(seg * 30)
    filtros = []
    for i in range(n):
        filtros.append(f"[{i}:v]scale=1188:2112,zoompan=z='min(zoom+0.0007,1.08)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s=1080x1920:fps=30,setsar=1,format=yuv420p[v{i}]")
    actual = "v0"
    for i in range(1, n):
        off = i * (seg - fundido)
        filtros.append(f"[{actual}][v{i}]xfade=transition=fade:duration={fundido}:offset={off:.2f}[x{i}]")
        actual = f"x{i}"
    nombre = f"{p['id']}.mp4"
    args += ["-filter_complex", ";".join(filtros), "-map", f"[{actual}]", "-map", f"{n}:a",
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-pix_fmt", "yuv420p", "-r", "30",
             "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", str(destino / nombre)]
    subprocess.run(args, check=True)
    return {"src": nombre, "portada": imagenes[0].name}


def render(posts, destino):
    from playwright.sync_api import sync_playwright
    destino.mkdir(parents=True, exist_ok=True)
    errores = {}
    # Vídeos explicados (con voz): los monta video.py con su propio navegador
    for p in posts:
        if p.get("formato") == "explicado":
            import video as jxvideo
            nombre = f"{p['id']}.mp4"
            try:
                r = jxvideo.generar(p["guion"], destino / nombre)
            except Exception as ex:
                errores.setdefault(p["id"], []).append(f"no se pudo montar el vídeo: {ex}")
                continue
            p["_imgs"] = [{"src": r["portada"]}]
            p["_video"] = {"src": nombre, "portada": r["portada"]}
    srv = servidor()
    base = f"http://127.0.0.1:{srv.server_address[1]}/"
    with sync_playwright() as pw:
        nav = pw.chromium.launch()
        pags = {False: nav.new_page(viewport={"width": 1080, "height": 1350}, device_scale_factor=1),
                True: nav.new_page(viewport={"width": 1080, "height": 1920}, device_scale_factor=1)}
        for p in posts:
            if p.get("formato") == "explicado":
                continue
            vertical = p.get("formato", "post") != "post"
            pag = pags[vertical]
            imgs = []
            total = len(p["diapositivas"])
            for n, d in enumerate(p["diapositivas"], 1):
                tmp = PLANTILLAS / f"_render-{p['id']}-{n}.html"
                tmp.write_text(documento(slide_html(d, n, 1 if vertical else total, p["tipo"]), vertical), encoding="utf-8")
                pag.goto(base + tmp.name)
                tmp.unlink()
                pag.evaluate("document.fonts.ready")
                pag.wait_for_load_state("networkidle")
                pag.wait_for_timeout(150)
                # ¿Se sale el texto?
                sale = pag.evaluate("""() => {
                    const c = document.querySelector('.contenido, .dentro');
                    if (!c) return false;
                    if (c.scrollHeight > c.clientHeight + 8) return true;
                    return [...document.querySelectorAll('.txt, .linea, h1, h2, .burbuja, .post-txt')].some(x => x.scrollWidth > x.clientWidth + 2);
                }""")
                if sale:
                    errores.setdefault(p["id"], []).append(f"diapositiva {n}: el texto no cabe, acórtalo")
                if d["plantilla"] == "portada":
                    # La foto la pone la web (descarga la de Unsplash y la coloca debajo de este PNG transparente)
                    nombre = f"{p['id']}-{n}.png"
                    pag.screenshot(path=str(destino / nombre), type="png", omit_background=True)
                    imgs.append({"src": nombre, "fondo": d["foto"]})
                else:
                    nombre = f"{p['id']}-{n}.jpg"
                    pag.screenshot(path=str(destino / nombre), type="jpeg", quality=90)
                    imgs.append({"src": nombre})
            p["_imgs"] = imgs
            if p.get("formato") == "reel":
                p["_video"] = video(p, destino, [destino / i["src"] for i in imgs])
        nav.close()
    srv.shutdown()
    return errores


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    nuevos = json.load(open(sys.argv[1], encoding="utf-8"))
    prueba = "--prueba" in sys.argv
    try:
        feed = json.load(open(FEED, encoding="utf-8"))
    except FileNotFoundError:
        feed = {"posts": []}
    ids = {p["id"] for p in feed["posts"]}
    mal = False
    for p in nuevos:
        errs = check(p)
        if not prueba and p.get("id") in ids:
            errs.append("repetido (id ya en el feed)")
        if errs:
            mal = True
            print("✗", p.get("id"), "→", "; ".join(errs))
    if mal:
        sys.exit(1)

    destino = AQUI / ("prueba" if prueba else "img")
    errores = render(nuevos, destino)
    if errores:
        for k, v in errores.items():
            print("✗", k, "→", "; ".join(v))
        if not prueba:
            for p in nuevos:
                for f in p.get("_imgs", []):
                    (destino / f["src"]).unlink(missing_ok=True)
        sys.exit(1)
    for p in nuevos:
        print("✓", p["id"], "·", p.get("formato", "post"), "·", p["tipo"], "·", p["publicar"], "·", len(p["_imgs"]), "imagen(es)" + (" + vídeo" if p.get("_video") else ""))
    if prueba:
        # Vista previa de las portadas con un fondo liso (la foto real la pone la web)
        from PIL import Image
        for p in nuevos:
            for f in p["_imgs"]:
                if "fondo" in f:
                    capa = Image.open(destino / f["src"]).convert("RGBA")
                    base_img = Image.new("RGBA", capa.size, (60, 90, 130, 255))
                    Image.alpha_composite(base_img, capa).convert("RGB").save(destino / f["src"].replace(".png", "-vista.jpg"), quality=88)
        print(f"Imágenes de prueba en {destino}")
        return

    for p in nuevos:
        p.setdefault("formato", "post")
        if p["formato"] == "explicado":
            # Para la web es un reel normal (vídeo + portada); el guion no hace falta en el feed
            p["formato"] = "reel"
            p["estilo"] = "explicado"
            p.pop("guion", None)
        p.pop("diapositivas", None) if not p.get("diapositivas") else None
        p["imagenes"] = [dict(f, src=f"redes/img/{f['src']}") for f in p.pop("_imgs")]
        v = p.pop("_video", None)
        if v:
            # El vídeo se queda en redes/img/ con las imágenes (así se limpia igual)
            p["video"] = {"src": f"redes/img/{v['src']}", "portada": f"redes/img/{v['portada']}"}
    limite = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=DIAS_GUARDADOS))
    todos = nuevos + feed["posts"]
    todos = [p for p in todos if dt.datetime.fromisoformat(p["publicar"]) >= limite]
    todos.sort(key=lambda p: p["publicar"], reverse=True)
    feed = {"updated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "posts": todos}
    json.dump(feed, open(FEED, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    # Borra las imágenes que ya no están en el feed
    usadas = {Path(i["src"]).name for p in todos for i in p["imagenes"]} | {Path(p["video"]["src"]).name for p in todos if p.get("video")}
    borradas = 0
    for f in list((AQUI / "img").glob("*.jpg")) + list((AQUI / "img").glob("*.png")) + list((AQUI / "img").glob("*.mp4")):
        if f.name not in usadas:
            f.unlink()
            borradas += 1
    print(f"redes/feed.json: {len(todos)} publicaciones" + (f" · {borradas} imágenes antiguas borradas" if borradas else ""))


if __name__ == "__main__":
    main()
