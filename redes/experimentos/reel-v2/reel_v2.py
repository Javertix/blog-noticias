#!/usr/bin/env python3
"""PRUEBA (no está en el repositorio): reel con voz más natural y mucho más movimiento.
- Voz: Kokoro ef_dora con el modelo completo (no int8) y cada frase de una vez (sin trocear en las comas).
  Jota: Piper es_ES sharvard (medium) en vez de carlfm x-low.
- Movimiento: primer fotograma ya lleno, zoom de corte en cada escena, cámara que respira, subtítulos grandes
  palabra a palabra, contadores animados, sacudida en el aviso, barra de progreso, efectos de sonido y ritmo suave.
Uso: python3 reel_v2.py guion.json salida.mp4
"""
import json, math, subprocess, sys, tempfile, re, functools, http.server, threading
from pathlib import Path
import numpy as np, soundfile as sf

AQ = Path(__file__).resolve().parent
WEB = AQ / "web"
FPS, SR = 30, 44100
GAP = 0.12          # respiro entre frases

# ───────────── voces ─────────────
_K = None
_P = None
def voz(texto, quien):
    global _K, _P
    if quien == "jota":
        if _P is None:
            from piper import PiperVoice, SynthesisConfig
            v = PiperVoice.load(str(AQ / "vits-piper-es_ES-sharvard-medium/es_ES-sharvard-medium.onnx"))
            _P = (v, SynthesisConfig(speaker_id=0, length_scale=0.86, noise_scale=0.62, noise_w_scale=0.85))
        v, cfg = _P
        a = np.concatenate([c.audio_float_array for c in v.synthesize(texto, syn_config=cfg)]); sr = v.config.sample_rate
    else:
        if _K is None:
            from kokoro_onnx import Kokoro
            _K = Kokoro(str(AQ / "kokoro-v1.0.onnx"), str(AQ / "voices-v1.0.bin"))
        a, sr = _K.create(texto, voice="ef_dora", speed=1.12, lang="es")
    a = np.asarray(a, np.float32)
    idx = np.where(np.abs(a) > 0.006)[0]
    a = a[max(0, idx[0] - 200): idx[-1] + 400]
    # a 44.1 kHz
    n = int(len(a) * SR / sr)
    return np.interp(np.linspace(0, len(a) - 1, n), np.arange(len(a)), a).astype(np.float32)

def palabras(texto, a, b):
    ws = texto.split()
    pesos = [len(re.sub(r"\W", "", w)) + 2 + (2 if re.search(r"[.!?…,:;]$", w) else 0) for w in ws]
    tot, t, out = sum(pesos), a, []
    for w, p in zip(ws, pesos):
        d = (b - a) * p / tot
        out.append({"w": w, "a": round(t, 3), "b": round(t + d, 3)}); t += d
    return out

def grupos(ws, maximo=3):
    out, cur = [], []
    for w in ws:
        cur.append(w)
        if len(cur) >= maximo or re.search(r"[.,;:!?…]$", w["w"]):
            out.append(cur); cur = []
    if cur: out.append(cur)
    return [{"a": g[0]["a"], "b": g[-1]["b"], "ws": g} for g in out]

# ───────────── sonido (todo sintetizado aquí, sin derechos) ─────────────
def env(n, ataque, caida):
    t = np.arange(n) / SR
    return np.minimum(1, t / max(ataque, 1e-4)) * np.exp(-t / caida)

def whoosh(d=0.35):
    n = int(SR * d); ruido = np.random.default_rng(1).standard_normal(n)
    # barrido de filtro sencillo: ruido filtrado cuya frecuencia sube
    out, y, k = np.zeros(n), 0.0, np.linspace(0.02, 0.35, n)
    for i in range(n):
        y += k[i] * (ruido[i] - y); out[i] = y
    e = np.sin(np.pi * np.arange(n) / n) ** 2
    return (out * e * 0.5).astype(np.float32)

def pop(f=900, d=0.09):
    n = int(SR * d); t = np.arange(n) / SR
    return (np.sin(2 * np.pi * f * t * (1 - t * 3)) * env(n, 0.002, 0.03) * 0.35).astype(np.float32)

def ding():
    n = int(SR * 0.9); t = np.arange(n) / SR
    s = sum(np.sin(2 * np.pi * f * t) * g for f, g in ((1318, 1), (1976, .5), (2637, .25)))
    return (s * env(n, 0.003, 0.25) * 0.22).astype(np.float32)

def boom():
    n = int(SR * 0.7); t = np.arange(n) / SR
    s = np.sin(2 * np.pi * (60 + 80 * np.exp(-t * 18)) * t) * env(n, 0.003, 0.22)
    r = np.random.default_rng(2).standard_normal(n) * env(n, 0.001, 0.05) * 0.3
    return ((s + r) * 0.6).astype(np.float32)

def tic():
    n = int(SR * 0.03); return (np.random.default_rng(3).standard_normal(n) * env(n, 0.0005, 0.006) * 0.25).astype(np.float32)

def ritmo(total, bpm=104):
    """Base muy suave: bombo, charles y un bajo de dos notas."""
    n = int(SR * total); out = np.zeros(n, np.float32); beat = 60 / bpm
    kn = int(SR * 0.25); kt = np.arange(kn) / SR
    kick = (np.sin(2 * np.pi * (50 + 90 * np.exp(-kt * 30)) * kt) * env(kn, 0.002, 0.08)).astype(np.float32)
    hn = int(SR * 0.05); hat = (np.random.default_rng(4).standard_normal(hn) * env(hn, 0.0005, 0.012)).astype(np.float32)
    hat = np.diff(hat, prepend=0) * 0.6
    b = 0
    while b * beat < total:
        i = int(b * beat * SR)
        if b % 1 == 0: add(out, kick * 0.55, i)
        add(out, hat * 0.18, int((b + 0.5) * beat * SR))
        nota = (55.0, 55.0, 65.4, 49.0)[(b // 4) % 4]
        bn = int(SR * beat * 0.9); bt = np.arange(bn) / SR
        add(out, (np.sin(2 * np.pi * nota * bt) * env(bn, 0.01, 0.3) * 0.18).astype(np.float32), i)
        b += 1
    return out

def add(dst, src, i):
    if i >= len(dst): return
    m = min(len(src), len(dst) - i); dst[i:i + m] += src[:m]

# ───────────── página ─────────────
PAGINA = (AQ / "reel_v2.html").read_text(encoding="utf-8")

def generar(guion, salida):
    from playwright.sync_api import sync_playwright
    tmp = Path(tempfile.mkdtemp(prefix="reelv2-"))
    escenas, gs, t = [], [], 0.0
    vozpista = []
    for e in guion["escenas"]:
        a = voz(e["texto"], e.get("voz", "dora"))
        d = len(a) / SR
        vozpista.append((t, a))
        ws = palabras(e["texto"], t, t + d)
        for g in grupos(ws):
            g["voz"] = e.get("voz", "dora"); gs.append(g)
        x = {"a": round(t, 3), "b": round(t + d, 3), "voz": e.get("voz", "dora"), "v": e["visual"]}
        if x["voz"] == "jota":
            paso = SR // FPS
            x["niv"] = [round(min(1, float(np.sqrt(np.mean(a[i:i + paso] ** 2))) * 7), 3) for i in range(0, len(a), paso)]
        escenas.append(x)
        t += d + e.get("pausa", GAP)
    total = t + 0.6
    # mezcla
    n = int(SR * total)
    v = np.zeros(n, np.float32)
    for a0, a in vozpista: add(v, a, int(a0 * SR))
    fx = np.zeros(n, np.float32)
    for i, x in enumerate(escenas):
        if i: add(fx, whoosh() * 0.55, max(0, int((x["a"] - 0.18) * SR)))
        tipo = x["v"]["tipo"]
        if tipo == "cifra":
            for k in range(10): add(fx, tic(), int((x["a"] + k * 0.07) * SR))
            add(fx, pop(1200), int((x["a"] + 0.75) * SR))
        if x["v"].get("ding"): add(fx, ding(), int((x["a"] + 0.8) * SR))
        if tipo == "alerta": add(fx, boom(), int(x["a"] * SR))
        if tipo == "lista":
            for k in range(len(x["v"]["puntos"])): add(fx, pop(700 + 150 * k), int((x["a"] + 0.25 + k * 0.6) * SR))
    add(fx, pop(500, 0.12), 0)
    mus = ritmo(total)
    # «ducking»: la música baja cuando hay voz
    envv = np.convolve(np.abs(v), np.ones(4410) / 4410, mode="same")
    duck = 1 - np.clip(envv * 18, 0, 0.7)
    mezcla = v * 1.0 + fx * 0.7 + mus * 0.32 * duck
    sf.write(tmp / "mezcla.wav", mezcla, SR)
    audio = tmp / "audio.wav"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(tmp / "mezcla.wav"),
                    "-af", "highpass=f=70,acompressor=threshold=-18dB:ratio=3:attack=5:release=80,loudnorm=I=-14:TP=-1.2:LRA=9",
                    "-ar", "44100", "-ac", "2", str(audio)], check=True)

    datos = {"escenas": escenas, "grupos": gs, "total": round(total, 3), "fps": FPS, "etiqueta": guion.get("etiqueta", "MITO O VERDAD"),
             "fuente": guion.get("fuente", "")}
    pag = WEB / "_reel.html"
    pag.write_text(PAGINA.replace("__DATOS__", json.dumps(datos, ensure_ascii=False)), encoding="utf-8")
    class S(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(S, directory=str(WEB)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(FPS), "-c:v", "mjpeg", "-i", "-",
                               "-i", str(audio), "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p",
                               "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(salida)], stdin=subprocess.PIPE)
        with sync_playwright() as p:
            b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1080, "height": 1920})
            pg.goto(f"http://127.0.0.1:{srv.server_port}/_reel.html"); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(400)
            for f in range(int(total * FPS)):
                pg.evaluate(f"frame({f / FPS:.4f})")
                ff.stdin.write(pg.screenshot(type="jpeg", quality=90))
            b.close()
        ff.stdin.close(); ff.wait()
    finally:
        srv.shutdown()
    return round(total, 1)

if __name__ == "__main__":
    print(generar(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8")), Path(sys.argv[2])))
