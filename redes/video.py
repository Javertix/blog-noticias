#!/usr/bin/env python3
"""Reels con voz (formato v2, aprobado el 10/11/2026): rápidos (20-30 s), con mucho movimiento y voces en español de España.

Uso:
  python3 redes/video.py guion.json salida.mp4          # genera un vídeo
  (crear.py lo usa para las publicaciones con "formato": "explicado")

Guion (ver README):
{
  "etiqueta": "MITO O VERDAD",
  "fuente": "Samsung 990 EVO Plus 1 TB · ficha técnica",
  "escenas": [
    {"voz": "narrador", "texto": "¿Tu SSD se gasta si lo usas mucho?",
     "visual": {"tipo": "gancho", "titulo": "¿TU SSD SE", "destacar": "GASTA?", "emoji": "ssd", "sello": "¿MITO?"}},
    {"voz": "jota", "texto": "Espóiler: te jubilas tú antes que él.", "visual": {"tipo": "gancho", "titulo": "TE JUBILAS", "destacar": "TÚ ANTES", "emoji": "🧓"}},
    {"texto": "…aguanta seiscientos terabytes escritos.", "visual": {"tipo": "cifra", "antes": "Un SSD de <b>1 TB</b> aguanta…", "hasta": 600, "unidad": "TB", "pie": "escritos", "emoji": "ssd"}},
    {"texto": "…te dura…", "visual": {"tipo": "barra", "antes": "Escribiendo <b>30 GB al día</b>", "hasta": 55, "unidad": "AÑOS", "oculto": true, "emoji": "👴"}},
    {"texto": "¡Cincuenta y cinco años!", "visual": {"tipo": "barra", "antes": "…", "hasta": 55, "unidad": "AÑOS", "sigue": true, "ding": true, "emoji": "👴"}},
    {"texto": "Pero ojo: …", "visual": {"tipo": "alerta", "titulo": "PUEDE MORIR", "destacar": "SIN AVISAR", "emoji": "💀"}},
    {"texto": "Mira su salud…", "visual": {"tipo": "lista", "titulo": "QUÉ HACER", "puntos": [{"e": "🩺", "t": "Mira su salud", "s": "CrystalDiskInfo"}, {"e": "☁️", "t": "Copias"}]}},
    {"voz": "jota", "texto": "Dale a seguir: …", "visual": {"tipo": "cierre", "texto": "Un mito informático cada semana"}}
  ]
}
Visuales: gancho, cifra, barra, alerta, lista, terminal, escena, cierre (ver README).
Voces: "narrador" (Álex, Kokoro em_alex, modelo completo) y "jota" (la mascota, Piper es_ES sharvard).
Gratuitas y locales: los modelos se descargan de GitHub la primera vez a ~/.cache/javertix-voces.
Música y efectos se sintetizan aquí mismo (sin derechos de autor).
"""
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

AQUI = Path(__file__).resolve().parent
PLANTILLAS = AQUI / "plantillas"
CACHE = Path(os.environ.get("JAVERTIX_VOCES", Path.home() / ".cache" / "javertix-voces"))
FPS, SR = 30, 44100
ANCHO, ALTO = 1080, 1920
GAP = 0.12            # respiro entre frases
FINAL = 0.6           # cola al final

KOKORO = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/"
SHERPA = "https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/"
MODELOS = {
    "kokoro-v1.0.onnx": KOKORO + "kokoro-v1.0.onnx",
    "voices-v1.0.bin": KOKORO + "voices-v1.0.bin",
    "vits-piper-es_ES-sharvard-medium.tar.bz2": SHERPA + "vits-piper-es_ES-sharvard-medium.tar.bz2",
}
JOTA = CACHE / "vits-piper-es_ES-sharvard-medium" / "es_ES-sharvard-medium.onnx"


def preparar_voces():
    """Descarga los modelos de voz (una vez) e instala lo que falte."""
    CACHE.mkdir(parents=True, exist_ok=True)
    for nombre, url in MODELOS.items():
        f = CACHE / nombre
        if not f.exists() and not (nombre.endswith(".tar.bz2") and JOTA.exists()):
            print(f"Descargando {nombre}…", file=sys.stderr)
            urllib.request.urlretrieve(url, f)
    if not JOTA.exists():
        subprocess.run(["tar", "xjf", str(CACHE / "vits-piper-es_ES-sharvard-medium.tar.bz2"), "-C", str(CACHE)], check=True)
        (CACHE / "vits-piper-es_ES-sharvard-medium.tar.bz2").unlink(missing_ok=True)
    try:
        import kokoro_onnx, piper, soundfile, numpy  # noqa: F401
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "--break-system-packages",
                        "kokoro-onnx", "piper-tts", "soundfile", "numpy"], check=True)


# ───────────── voces ─────────────
_K = _P = None


def voz(texto, quien):
    """Sintetiza la frase entera (sin trocear en las comas: así conserva la entonación). Devuelve float32 a 44,1 kHz."""
    import numpy as np
    global _K, _P
    if quien == "jota":
        if _P is None:
            from piper import PiperVoice, SynthesisConfig
            v = PiperVoice.load(str(JOTA))
            _P = (v, SynthesisConfig(speaker_id=0, length_scale=0.86, noise_scale=0.62, noise_w_scale=0.85))
        v, cfg = _P
        a = np.concatenate([c.audio_float_array for c in v.synthesize(texto, syn_config=cfg)])
        sr = v.config.sample_rate
    else:
        if _K is None:
            from kokoro_onnx import Kokoro
            _K = Kokoro(str(CACHE / "kokoro-v1.0.onnx"), str(CACHE / "voices-v1.0.bin"))
        a, sr = _K.create(texto, voice="em_alex", speed=1.1, lang="es")
    a = np.asarray(a, np.float32)
    idx = np.where(np.abs(a) > 0.006)[0]
    if len(idx):
        a = a[max(0, idx[0] - 200): idx[-1] + 400]
    n = int(len(a) * SR / sr)
    return np.interp(np.linspace(0, len(a) - 1, n), np.arange(len(a)), a).astype(np.float32)


def palabras(texto, a, b):
    ws = texto.split()
    pesos = [len(re.sub(r"\W", "", w)) + 2 + (2 if re.search(r"[.!?…,:;]$", w) else 0) for w in ws]
    tot, t, out = sum(pesos) or 1, a, []
    for w, p in zip(ws, pesos):
        d = (b - a) * p / tot
        out.append({"w": w, "a": round(t, 3), "b": round(t + d, 3)})
        t += d
    return out


def grupos(ws, maximo=3):
    """Subtítulos de hasta 3 palabras, cortando también en la puntuación."""
    out, cur = [], []
    for w in ws:
        cur.append(w)
        if len(cur) >= maximo or re.search(r"[.,;:!?…]$", w["w"]):
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return [{"a": g[0]["a"], "b": g[-1]["b"], "ws": g} for g in out]


# ───────────── emojis → archivo de Twemoji ─────────────
EMOJIS = {f.stem for f in (PLANTILLAS / "emoji").glob("*.svg")}


def emoji(x):
    """'💾' → '1f4be' (nombre del SVG). Acepta también el código o 'ssd' (dibujo propio)."""
    if not x:
        return None
    x = str(x).strip()
    if x == "ssd" or x in EMOJIS:
        return x
    cps = [f"{ord(c):x}" for c in x]
    for nombre in ("-".join(cps), "-".join(c for c in cps if c != "fe0f")):
        if nombre in EMOJIS:
            return nombre
    return None


def preparar_visual(v):
    v = dict(v)
    if "emoji" in v:
        v["emoji"] = emoji(v["emoji"])
    if "emojis" in v:
        v["emojis"] = [e for e in (emoji(x) for x in v["emojis"]) if e]
    if "puntos" in v:
        v["puntos"] = [dict(p, e=emoji(p.get("e")) or "2705") if isinstance(p, dict) else {"e": "2705", "t": str(p)} for p in v["puntos"]]
    return v


# ───────────── sonido (sintetizado: sin derechos) ─────────────
def _env(n, ataque, caida):
    import numpy as np
    t = np.arange(n) / SR
    return np.minimum(1, t / max(ataque, 1e-4)) * np.exp(-t / caida)


def _add(dst, src, i):
    if i >= len(dst) or i < 0:
        return
    m = min(len(src), len(dst) - i)
    dst[i:i + m] += src[:m]


def _whoosh(d=0.35):
    import numpy as np
    n = int(SR * d)
    ruido = np.random.default_rng(1).standard_normal(n)
    out, y, k = np.zeros(n), 0.0, np.linspace(0.02, 0.35, n)
    for i in range(n):
        y += k[i] * (ruido[i] - y)
        out[i] = y
    return (out * np.sin(np.pi * np.arange(n) / n) ** 2 * 0.5).astype(np.float32)


def _pop(f=900, d=0.09):
    import numpy as np
    n = int(SR * d); t = np.arange(n) / SR
    return (np.sin(2 * np.pi * f * t * (1 - t * 3)) * _env(n, 0.002, 0.03) * 0.35).astype(np.float32)


def _ding():
    import numpy as np
    n = int(SR * 0.9); t = np.arange(n) / SR
    s = sum(np.sin(2 * np.pi * f * t) * g for f, g in ((1318, 1), (1976, .5), (2637, .25)))
    return (s * _env(n, 0.003, 0.25) * 0.22).astype(np.float32)


def _boom():
    import numpy as np
    n = int(SR * 0.7); t = np.arange(n) / SR
    s = np.sin(2 * np.pi * (60 + 80 * np.exp(-t * 18)) * t) * _env(n, 0.003, 0.22)
    r = np.random.default_rng(2).standard_normal(n) * _env(n, 0.001, 0.05) * 0.3
    return ((s + r) * 0.6).astype(np.float32)


def _tic():
    import numpy as np
    n = int(SR * 0.03)
    return (np.random.default_rng(3).standard_normal(n) * _env(n, 0.0005, 0.006) * 0.25).astype(np.float32)


def _ritmo(total, bpm=104):
    """Base muy suave: bombo, charles y un bajo de dos notas."""
    import numpy as np
    n = int(SR * total); out = np.zeros(n, np.float32); beat = 60 / bpm
    kn = int(SR * 0.25); kt = np.arange(kn) / SR
    kick = (np.sin(2 * np.pi * (50 + 90 * np.exp(-kt * 30)) * kt) * _env(kn, 0.002, 0.08)).astype(np.float32)
    hn = int(SR * 0.05)
    hat = np.diff((np.random.default_rng(4).standard_normal(hn) * _env(hn, 0.0005, 0.012)).astype(np.float32), prepend=0) * 0.6
    b = 0
    while b * beat < total:
        i = int(b * beat * SR)
        _add(out, kick * 0.55, i)
        _add(out, hat * 0.18, int((b + 0.5) * beat * SR))
        nota = (55.0, 55.0, 65.4, 49.0)[(b // 4) % 4]
        bn = int(SR * beat * 0.9); bt = np.arange(bn) / SR
        _add(out, (np.sin(2 * np.pi * nota * bt) * _env(bn, 0.01, 0.3) * 0.18).astype(np.float32), i)
        b += 1
    return out


# ───────────── montaje ─────────────
def generar(guion, salida):
    import numpy as np
    import soundfile as sf
    from playwright.sync_api import sync_playwright
    sys.path.insert(0, str(AQUI))
    from crear import servidor
    preparar_voces()
    tmp = Path(tempfile.mkdtemp(prefix="jxvideo-"))
    escenas, gs, pistas, t = [], [], [], 0.0
    for e in guion["escenas"]:
        quien = "jota" if e.get("voz") == "jota" else "narrador"
        a = voz(e["texto"], quien)
        d = len(a) / SR
        pistas.append((t, a))
        for g in grupos(palabras(e["texto"], t, t + d)):
            g["voz"] = quien
            gs.append(g)
        x = {"a": round(t, 3), "b": round(t + d, 3), "voz": quien, "v": preparar_visual(e.get("visual", {}))}
        if quien == "jota":
            paso = SR // FPS
            x["niv"] = [round(min(1, float(np.sqrt(np.mean(a[i:i + paso] ** 2))) * 7), 3) for i in range(0, len(a), paso)]
        escenas.append(x)
        t += d + float(e.get("pausa", GAP))
    total = t + FINAL

    # audio: voz + efectos + base suave que se aparta cuando hay voz
    n = int(SR * total)
    v, fx = np.zeros(n, np.float32), np.zeros(n, np.float32)
    for a0, a in pistas:
        _add(v, a, int(a0 * SR))
    for i, x in enumerate(escenas):
        tipo = x["v"].get("tipo")
        if i:
            _add(fx, _whoosh() * 0.55, max(0, int((x["a"] - 0.18) * SR)))
        if tipo in ("cifra", "barra") and x["v"].get("hasta") is not None and not x["v"].get("oculto"):
            for k in range(10):
                _add(fx, _tic(), int((x["a"] + k * 0.07) * SR))
            _add(fx, _pop(1200), int((x["a"] + 0.75) * SR))
        if x["v"].get("ding"):
            _add(fx, _ding(), int((x["a"] + 0.8) * SR))
        if tipo == "alerta":
            _add(fx, _boom(), int(x["a"] * SR))
        if tipo == "lista":
            for k in range(len(x["v"].get("puntos", []))):
                _add(fx, _pop(700 + 150 * k), int((x["a"] + 0.25 + k * 0.6) * SR))
        if tipo == "terminal":
            for k in range(int((x["b"] - x["a"]) * 0.85 / 0.09)):
                if k % 3:
                    _add(fx, _tic() * 0.6, int((x["a"] + k * 0.09) * SR))
    _add(fx, _pop(500, 0.12), 0)
    envv = np.convolve(np.abs(v), np.ones(4410) / 4410, mode="same")
    mezcla = v + fx * 0.7 + _ritmo(total) * 0.32 * (1 - np.clip(envv * 18, 0, 0.7))
    sf.write(tmp / "mezcla.wav", mezcla, SR)
    audio = tmp / "audio.wav"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(tmp / "mezcla.wav"),
                    "-af", "highpass=f=70,acompressor=threshold=-18dB:ratio=3:attack=5:release=80,loudnorm=I=-14:TP=-1.2:LRA=9",
                    "-ar", "44100", "-ac", "2", str(audio)], check=True)

    datos = {"escenas": escenas, "grupos": gs, "total": round(total, 3), "fps": FPS,
             "etiqueta": guion.get("etiqueta") or "DATO RÁPIDO", "fuente": guion.get("fuente", "")}
    pagina = PLANTILLAS / f"_video-{os.getpid()}.html"
    pagina.write_text((PLANTILLAS / "reel.html").read_text(encoding="utf-8").replace("__DATOS__", json.dumps(datos, ensure_ascii=False)), encoding="utf-8")
    srv = servidor()
    try:
        ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(FPS), "-c:v", "mjpeg", "-i", "-",
                               "-i", str(audio), "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p",
                               "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(salida)], stdin=subprocess.PIPE)
        with sync_playwright() as p:
            nav = p.chromium.launch()
            pg = nav.new_page(viewport={"width": ANCHO, "height": ALTO})
            pg.goto(f"http://127.0.0.1:{srv.server_port}/{pagina.name}")
            pg.evaluate("document.fonts.ready")
            pg.wait_for_timeout(400)
            for f in range(int(total * FPS)):
                pg.evaluate(f"frame({f / FPS:.4f})")
                ff.stdin.write(pg.screenshot(type="jpeg", quality=90))
            nav.close()
        ff.stdin.close()
        ff.wait()
        if ff.returncode:
            raise RuntimeError("ffmpeg no pudo montar el vídeo")
    finally:
        srv.shutdown()
        pagina.unlink(missing_ok=True)
    # portada: el gancho (fotograma 0 ya está completo)
    portada = Path(salida).with_suffix(".jpg")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", "0.6", "-i", str(salida), "-frames:v", "1", "-q:v", "3", str(portada)], check=True)
    return {"duracion": round(total, 1), "portada": portada.name}


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    g = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    print(generar(g, Path(sys.argv[2])))
