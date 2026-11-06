#!/usr/bin/env python3
"""Vídeos explicativos con voz para reels de Instagram/Facebook y borradores de TikTok.

Uso:
  python3 redes/video.py guion.json salida.mp4          # genera un vídeo
  (crear.py lo usa solo para las publicaciones con "formato": "explicado")

Guion (ver README):
{
  "etiqueta": "DATO RÁPIDO",
  "fuente": "Hive Systems 2025 · 12× RTX 5090 · bcrypt",
  "escala": true,                        # opcional: línea de tiempo logarítmica (segundos → milenios)
  "escenas": [
    {"voz": "dora", "texto": "¿Cuánto tarda…?", "visual": {"tipo": "titulo", "titulo": "¿CUÁNTO TARDA…", "destacar": "TU CONTRASEÑA?"}},
    {"voz": "dora", "texto": "…tres semanas.", "visual": {"tipo": "cifra", "cifra": "3 semanas", "pie": "8 caracteres", "chip": "a-z 0-9", "segundos": 1814400}},
    {"voz": "jota", "texto": "Pero ojo…", "visual": {"tipo": "cifra", "cifra": "0 s", "pie": "si se filtra", "segundos": 0, "alerta": true}},
    {"voz": "dora", "texto": "Usa…", "visual": {"tipo": "lista", "titulo": "Qué hacer", "puntos": ["…", "…"]}},
    {"voz": "dora", "texto": "Síguenos…", "visual": {"tipo": "cierre"}}
  ]
}
Voces: "dora" (narradora, Kokoro ef_dora) y "jota" (la mascota, Piper es-carlfm). Ambas gratuitas y locales:
los modelos se descargan de GitHub la primera vez a ~/.cache/javertix-voces.
"""
import json
import math
import os
import re
import subprocess
import sys
import tempfile
import urllib.request
import wave
from pathlib import Path

AQUI = Path(__file__).resolve().parent
PLANTILLAS = AQUI / "plantillas"
CACHE = Path(os.environ.get("JAVERTIX_VOCES", Path.home() / ".cache" / "javertix-voces"))
FPS = 30
ANCHO, ALTO = 1080, 1920
PAUSA = 0.35          # silencio entre escenas
FINAL = 1.2           # cola al final

MODELOS = {
    "kokoro-v1.0.int8.onnx": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.int8.onnx",
    "voices-v1.0.bin": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin",
    "es-carlfm-x-low.tar.gz": "https://github.com/rhasspy/piper/releases/download/v0.0.2/voice-es-carlfm-x-low.tar.gz",
}


def preparar_voces():
    """Descarga los modelos de voz (una vez) e instala lo que falte."""
    CACHE.mkdir(parents=True, exist_ok=True)
    for nombre, url in MODELOS.items():
        f = CACHE / nombre
        if not f.exists():
            print(f"Descargando {nombre}…", file=sys.stderr)
            urllib.request.urlretrieve(url, f)
    if not (CACHE / "es-carlfm-x-low.onnx").exists():
        subprocess.run(["tar", "xzf", str(CACHE / "es-carlfm-x-low.tar.gz"), "-C", str(CACHE)], check=True)
    try:
        import kokoro_onnx, piper, soundfile  # noqa: F401
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "--break-system-packages",
                        "kokoro-onnx", "piper-tts", "soundfile"], check=True)


PAUSAS = {".": 0.45, "?": 0.45, "!": 0.45, "…": 0.55, ",": 0.22, ";": 0.3, ":": 0.3}


def trozos(texto):
    """Parte la frase en la puntuación para meter una pausa de verdad en cada coma y cada punto."""
    partes = re.findall(r"[^.,;:!?…]+[.,;:!?…]*", texto)
    out = []
    for p in partes:
        p = p.strip()
        if not p:
            continue
        if re.fullmatch(r"[.,;:!?…¿¡\s]+", p) and out:
            out[-1] += p
        else:
            out.append(p)
    return out


def _sintetizar(texto, voz, destino):
    import soundfile as sf
    crudo = destino.with_suffix(".raw.wav")
    if voz == "jota":
        subprocess.run([sys.executable, "-m", "piper", "-m", str(CACHE / "es-carlfm-x-low.onnx"), "-f", str(crudo),
                        "--length-scale", "0.95"], input=texto.encode(), check=True, capture_output=True)
    else:
        global _KOKORO
        if "_KOKORO" not in globals():
            from kokoro_onnx import Kokoro
            _KOKORO = Kokoro(str(CACHE / "kokoro-v1.0.int8.onnx"), str(CACHE / "voices-v1.0.bin"))
        audio, sr = _KOKORO.create(texto, voice="ef_dora", speed=1.08, lang="es")
        sf.write(crudo, audio, sr)
    # 24 kHz mono y sin el silencio que añade el modelo al principio y al final
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(crudo), "-ar", "24000", "-ac", "1",
                    "-af", "silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse",
                    str(destino)], check=True)
    crudo.unlink()


def decir(texto, voz, destino):
    """Genera la voz trozo a trozo con pausas en la puntuación.
    Devuelve (duración, [(trozo, inicio, fin)]) con los tiempos relativos al inicio del WAV."""
    import array
    muestras = array.array("h")
    marcas = []
    sr = 24000
    for i, tz in enumerate(trozos(texto)):
        f = destino.with_name(f"{destino.stem}-{i}.wav")
        hablar = tz.strip("¿¡ ")
        if not re.search(r"\w", hablar):
            continue
        _sintetizar(tz, voz, f)
        with wave.open(str(f)) as w:
            datos = array.array("h", w.readframes(w.getnframes()))
        f.unlink()
        ini = len(muestras) / sr
        muestras.extend(datos)
        marcas.append((tz, ini, len(muestras) / sr))
        signo = tz.rstrip()[-1:] if tz.rstrip()[-1:] in PAUSAS else ""
        muestras.extend(array.array("h", [0]) * int(sr * PAUSAS.get(signo, 0.08)))
    # quita la última pausa (ya hay pausa entre escenas)
    fin = int(marcas[-1][2] * sr) if marcas else 0
    del muestras[fin:]
    crudo = destino.with_suffix(".junto.wav")
    with wave.open(str(crudo), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes(muestras.tobytes())
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(crudo), "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
                    "-ar", "24000", "-ac", "1", str(destino)], check=True)
    crudo.unlink()
    with wave.open(str(destino)) as w:
        dur = w.getnframes() / w.getframerate()
    return dur, marcas


def niveles(wav, fps=FPS):
    """Volumen por fotograma (0-1) para mover la boca de la mascota."""
    with wave.open(str(wav)) as w:
        sr, n = w.getframerate(), w.getnframes()
        datos = w.readframes(n)
    import array
    a = array.array("h", datos)
    paso = sr // fps
    out = []
    for i in range(0, len(a), paso):
        trozo = a[i:i + paso]
        if not trozo:
            break
        rms = math.sqrt(sum(x * x for x in trozo) / len(trozo)) / 32768
        out.append(round(min(1.0, rms * 6), 3))
    return out


def palabras(texto, inicio, dur):
    """Reparte el tiempo de la frase entre sus palabras según su longitud (y las pausas de la puntuación)."""
    ws = texto.split()
    pesos = []
    for w in ws:
        p = len(re.sub(r"[^\wáéíóúüñÁÉÍÓÚÜÑ0-9]", "", w)) + 2
        if re.search(r"[.!?…,;:]$", w):
            p += 1
        pesos.append(p)
    total = sum(pesos) or 1
    t = inicio
    util = dur
    out = []
    for w, p in zip(ws, pesos):
        d = util * p / total
        out.append({"w": w, "a": round(t, 3), "b": round(t + d, 3)})
        t += d
    return out


def grupos(ws, maximo=4):
    """Subtítulos en bloques de hasta 4 palabras, cortando también en la puntuación."""
    out, actual = [], []
    for w in ws:
        actual.append(w)
        if len(actual) >= maximo or re.search(r"[.,;:!?…]$", w["w"]):
            out.append(actual)
            actual = []
    if actual:
        out.append(actual)
    return [{"a": g[0]["a"], "b": g[-1]["b"], "ws": g} for g in out]


PAGINA = """<!doctype html><html><head><meta charset="utf-8">
<link rel="stylesheet" href="fuentes/marca.css">
<style>
:root{--azul:#0B1E33;--azul2:#12325a;--amarillo:#FFC83D;--naranja:#FF8A3D;--cian:#5CE1E6;--rojo:#FF5A5F}
*{box-sizing:border-box;margin:0;padding:0}
html,body{width:1080px;height:1920px;overflow:hidden;background:var(--azul)}
#lienzo{position:relative;width:1080px;height:1920px;overflow:hidden;
  background:radial-gradient(900px 700px at 50% 42%,#173f6e 0%,#0d2440 55%,#081626 100%);font-family:'Instrument Sans',sans-serif;color:#fff}
#rejilla{position:absolute;inset:-60px;background-image:radial-gradient(rgba(255,255,255,.09) 2px,transparent 2px);background-size:60px 60px}
.zona{position:absolute;left:80px;right:80px}
#cabeza{top:250px}
.chip{display:inline-block;font:700 26px 'JetBrains Mono',monospace;letter-spacing:.06em;background:var(--amarillo);color:var(--azul);padding:6px 14px;border-radius:6px}
#titulo{font:800 96px/1.02 'Bricolage Grotesque',sans-serif;letter-spacing:-.01em;margin-top:26px;text-transform:uppercase}
#titulo .d{color:var(--amarillo)}
#cifra{font:800 200px/1 'Bricolage Grotesque',sans-serif;color:var(--amarillo);letter-spacing:-.02em;white-space:nowrap;text-shadow:0 8px 40px rgba(255,200,61,.25)}
#cifra.alerta{color:var(--rojo);text-shadow:0 8px 40px rgba(255,90,95,.35)}
#pieCifra{display:flex;gap:16px;align-items:center;margin-top:18px}
#pieCifra .txt{font:700 30px 'JetBrains Mono',monospace;text-transform:uppercase;border-left:6px solid var(--amarillo);padding-left:14px;color:#dfe8f5}
#chipCifra{font:700 26px 'JetBrains Mono',monospace;background:var(--amarillo);color:var(--azul);padding:6px 12px;border-radius:6px}
#escala{top:720px;height:300px}
#pista{position:absolute;left:0;right:0;top:120px;height:34px;border-radius:17px;background:rgba(255,255,255,.08);overflow:hidden}
#relleno{position:absolute;left:0;top:0;bottom:0;border-radius:17px;background:linear-gradient(90deg,var(--amarillo),var(--naranja))}
#relleno.alerta{background:var(--rojo)}
.marca{position:absolute;top:170px;transform:translateX(-50%);font:700 26px 'JetBrains Mono',monospace;color:#8fa6c4;white-space:nowrap}
.marca.fin::before{left:auto;right:0}.marca.ini::before{left:0}.marca::before{content:'';position:absolute;left:50%;top:-22px;width:2px;height:14px;background:#4d6a8f}
#candado{position:absolute;top:28px;width:84px;height:84px;transform:translateX(-50%)}
#lista{top:300px}
#escena{position:absolute;left:0;right:0;top:300px;height:880px}
#escena .disco{position:absolute;left:50%;top:330px;width:620px;height:620px;margin:-310px 0 0 -310px;border-radius:50%;
  background:radial-gradient(circle at 50% 45%,rgba(255,255,255,.18),rgba(255,255,255,.04) 60%,transparent 70%)}
#escena .rayos{position:absolute;left:50%;top:330px;width:1400px;height:1400px;margin:-700px 0 0 -700px;opacity:.10;
  background:repeating-conic-gradient(from 0deg,#fff 0deg 6deg,transparent 6deg 18deg)}
#emos{position:absolute;left:0;right:0;top:130px;height:400px;display:flex;justify-content:center;align-items:center;gap:30px}
#emos img{width:300px;height:300px;filter:drop-shadow(0 18px 30px rgba(0,0,0,.4))}
#emos.dos img{width:260px;height:260px} #emos.tres img{width:220px;height:220px}
#etiq{position:absolute;left:50%;top:560px;transform:translateX(-50%) rotate(-3deg);background:var(--amarillo);color:var(--azul);
  font:800 92px/1 'Bricolage Grotesque',sans-serif;text-transform:uppercase;padding:18px 40px;border-radius:18px;white-space:nowrap;
  box-shadow:0 14px 0 #c99410,0 24px 40px rgba(0,0,0,.35)}
#escTit{position:absolute;left:80px;right:80px;top:0;font:800 64px/1.05 'Bricolage Grotesque',sans-serif;text-transform:uppercase}
#escTit .d{color:var(--amarillo)}
#term{position:absolute;left:60px;right:60px;top:300px;background:#060d18;border:2px solid #22344f;border-radius:24px;overflow:hidden;box-shadow:0 24px 60px rgba(0,0,0,.45)}
#term .barra{display:flex;align-items:center;gap:12px;padding:20px 26px;background:#15233a;font:600 28px 'JetBrains Mono',monospace;color:#8fa6c4}
#term .barra i{width:20px;height:20px;border-radius:50%;background:#FF5F57;display:inline-block}
#term .barra i:nth-child(2){background:#FEBC2E}#term .barra i:nth-child(3){background:#28C840}
#tcuerpo{padding:30px 32px 40px;font:500 36px/1.45 'JetBrains Mono',monospace;color:#E6EDF7;min-height:420px}
#tcuerpo .l{white-space:pre-wrap;word-break:break-word;margin-bottom:6px}
#tcuerpo .p{color:#5CE1E6;font-weight:700}
#tcuerpo .error{color:#FF6B6B}#tcuerpo .ok{color:#4ADE80}#tcuerpo .warn{color:#FFC83D}#tcuerpo .gris{color:#7E8FA8}
#tcuerpo .cur{display:inline-block;width:20px;height:40px;background:#E6EDF7;vertical-align:middle}
#lista h3{font:800 84px 'Bricolage Grotesque',sans-serif;margin-bottom:36px}
.punto{display:flex;gap:26px;align-items:center;font:600 54px/1.15 'Instrument Sans',sans-serif;margin-bottom:34px}
.punto .ok{flex:none;width:64px;height:64px;border-radius:16px;background:var(--amarillo);color:var(--azul);font:800 44px/64px 'Bricolage Grotesque';text-align:center}
#subs{position:absolute;left:60px;right:60px;top:1330px;text-align:center;font:600 54px/1.3 'JetBrains Mono',monospace;color:#fff;text-shadow:0 3px 12px rgba(0,0,0,.6)}
#subs .w{padding:2px 8px;border-radius:8px;margin:0 2px}
#subs .w.on{background:var(--amarillo);color:var(--azul);text-shadow:none}
#subs.jota .w.on{background:var(--cian)}
#quien{display:block;font:700 26px 'JetBrains Mono';color:var(--cian);margin-bottom:8px;letter-spacing:.1em}
#fuente{position:absolute;left:80px;right:300px;top:1560px;font:400 22px 'JetBrains Mono',monospace;color:#8fa6c4;border-left:4px solid var(--cian);padding-left:12px}
#fuente b{color:var(--cian)}
#marca{position:absolute;left:80px;bottom:120px;display:flex;align-items:center;gap:14px;font:800 34px 'Bricolage Grotesque';letter-spacing:.08em}
#marca img{height:54px}
#marca span{font:400 26px 'JetBrains Mono';color:#8fa6c4;letter-spacing:0;margin-left:12px}
#jota{position:absolute;width:250px;height:300px;right:70px;top:1000px}
#cierre{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:30px;opacity:0}
#cierre h2{font:800 110px 'Bricolage Grotesque';letter-spacing:.06em}
#cierre .raya{width:120px;height:6px;background:var(--amarillo);border-radius:3px}
#cierre p{font:600 44px 'JetBrains Mono';color:var(--amarillo);text-align:center;padding:0 80px}
#cierre .web{font:400 34px 'JetBrains Mono';color:#cfe0f5}
.oculto{display:none!important}
</style></head><body><div id="lienzo">
<div id="rejilla"></div>
<div id="cabeza" class="zona"><span class="chip" id="chip"></span><div id="titulo"></div>
  <div id="bloqueCifra" class="oculto"><div id="cifra"></div><div id="pieCifra"><span class="txt" id="pieTxt"></span><span id="chipCifra"></span></div></div></div>
<div id="escala" class="zona oculto"><svg id="candado" viewBox="0 0 84 84"><rect x="14" y="36" width="56" height="42" rx="10" fill="#FFC83D"/>
  <path id="arco" d="M26 36 V26 a16 16 0 0 1 32 0 V36" fill="none" stroke="#FFC83D" stroke-width="9" stroke-linecap="round"/>
  <circle cx="42" cy="55" r="6" fill="#0B1E33"/><rect x="39" y="56" width="6" height="12" rx="3" fill="#0B1E33"/></svg>
  <div id="pista"><div id="relleno"></div></div></div>
<div id="escena" class="oculto"><div class="rayos"></div><div class="disco"></div><div id="escTit"></div><div id="emos"></div><div id="etiq"></div></div>
<div id="term" class="oculto"><div class="barra"><i></i><i></i><i></i><span id="tventana">bash</span></div><div id="tcuerpo"></div></div>
<div id="lista" class="zona oculto"><h3 id="listaTit"></h3><div id="puntos"></div></div>
<svg id="jota" viewBox="0 0 250 300">
  <g id="cuerpo">
    <line x1="125" y1="40" x2="125" y2="12" stroke="#8fb3e0" stroke-width="6" stroke-linecap="round"/>
    <circle id="antena" cx="125" cy="10" r="10" fill="#FFC83D"/>
    <rect x="20" y="40" width="210" height="160" rx="44" fill="#2a6fd6"/>
    <rect x="42" y="62" width="166" height="116" rx="30" fill="#0B1E33"/>
    <g id="ojos"><ellipse id="oi" cx="95" cy="112" rx="15" ry="19" fill="#5CE1E6"/><ellipse id="od" cx="155" cy="112" rx="15" ry="19" fill="#5CE1E6"/></g>
    <rect id="boca" x="105" y="146" width="40" height="6" rx="3" fill="#5CE1E6"/>
    <rect x="62" y="206" width="126" height="76" rx="26" fill="#2a6fd6"/>
    <text x="125" y="262" text-anchor="middle" font-family="Bricolage Grotesque" font-weight="800" font-size="56" fill="#FFC83D">J</text>
    <rect x="30" y="214" width="26" height="56" rx="13" fill="#1f58ad"/><rect x="194" y="214" width="26" height="56" rx="13" fill="#1f58ad"/>
  </g></svg>
<div id="subs"></div>
<div id="fuente"></div>
<div id="marca"><img src="icono-blanco.png" alt="">JAVERTIX<span>javertix.site</span></div>
<div id="cierre"><svg width="330" height="396" viewBox="0 0 250 300"><use href="#cuerpo"/></svg><h2>JAVERTIX</h2><div class="raya"></div>
  <p>Escríbenos qué quieres que investiguemos</p><div class="web">javertix.site</div></div>
</div>
<script>
const D = __DATOS__;
const $ = id => document.getElementById(id);
const escH = x => String(x).replace(/&/g,'&amp;').replace(/</g,'&lt;');
const ease = x => x<0?0:x>1?1:1-Math.pow(1-x,3);
const back = x => {x=Math.max(0,Math.min(1,x));const c=1.7;return 1+(c+1)*Math.pow(x-1,3)+c*Math.pow(x-1,2);};
const MARCAS = [[1,'1 s'],[60,'1 min'],[3600,'1 h'],[86400,'1 día'],[31536000,'1 año'],[31536000000,'1000 años']];
const LMIN = 0, LMAX = Math.log10(31536000000);
const pos = s => s<=0 ? 0 : Math.max(0, Math.min(1, (Math.log10(s)-LMIN)/(LMAX-LMIN)));
function init(){
  $('chip').textContent = D.etiqueta || 'DATO RÁPIDO';
  $('fuente').innerHTML = D.fuente ? '<b>FUENTE</b> ' + D.fuente : '';
  if (D.escala) { const e=$('escala'); MARCAS.forEach(([s,t],i)=>{ if(i%1)return; const m=document.createElement('div'); m.className='marca'; m.style.left=(pos(s)*100)+'%'; m.textContent=t; if(i===MARCAS.length-1){m.style.transform='translateX(-100%)';m.classList.add('fin');} if(i===0){m.style.transform='none';m.classList.add('ini');} e.appendChild(m); }); }
}
function escena(t){ let a=null; for(const s of D.escenas){ if(t>=s.a) a=s; } return a; }
let ultima=null;
function frame(t){
  const s = escena(t) || D.escenas[0];
  const v = s.visual || {};
  const dt = t - s.a;
  // fondo que se mueve despacio
  $('rejilla').style.transform = `translate(${(t*6)%60}px,${(t*4)%60}px)`;
  const cierre = v.tipo === 'cierre';
  // cabecera: título o cifra
  const tit = $('titulo'), bc = $('bloqueCifra');
  const ultCifra = [...D.escenas].filter(x=>x.a<=t && x.visual && x.visual.tipo==='cifra').pop();
  if (v.tipo === 'titulo') {
    tit.innerHTML = (v.titulo||'') + (v.destacar? ' <span class="d">'+v.destacar+'</span>':'');
    tit.style.display=''; tit.style.opacity = ease(dt/0.35); tit.style.transform = `translateY(${(1-ease(dt/0.35))*30}px)`;
    bc.classList.add('oculto'); $('chip').style.opacity=1;
  } else if (ultCifra && v.tipo==='cifra') {
    const c = ultCifra.visual, d2 = t-ultCifra.a;
    tit.style.display='none'; bc.classList.remove('oculto'); $('chip').style.opacity=1;
    $('cifra').textContent = c.cifra; $('cifra').classList.toggle('alerta', !!c.alerta);
    $('pieTxt').textContent = c.pie||''; $('chipCifra').textContent = c.chip||''; $('chipCifra').style.display = c.chip?'':'none';
    const cf=$('cifra'); cf.style.fontSize='200px'; let fs=200; while(cf.scrollWidth>920 && fs>90){fs-=6; cf.style.fontSize=fs+'px';}
    const k = back(d2/0.45); $('cifra').style.transform=`scale(${0.7+0.3*k})`; $('cifra').style.transformOrigin='left center';
    $('cifra').style.opacity = ease(d2/0.25);
    if (v.tipo==='lista') { bc.classList.add('oculto'); $('chip').style.opacity=0; }
  } else { tit.style.display='none'; bc.classList.add('oculto'); if (v.tipo==='lista') $('chip').style.opacity=0; }
  // escala de tiempo
  const esc = $('escala');
  if (D.escala && ultCifra && v.tipo==='cifra') {
    esc.classList.remove('oculto');
    const prev = [...D.escenas].filter(x=>x.a<ultCifra.a && x.visual && x.visual.tipo==='cifra').pop();
    const p0 = prev ? pos(prev.visual.segundos) : 0, p1 = pos(ultCifra.visual.segundos);
    const k = ease((t-ultCifra.a)/0.9), p = p0 + (p1-p0)*k;
    $('relleno').style.width = (p*100)+'%'; $('relleno').classList.toggle('alerta', !!ultCifra.visual.alerta);
    $('candado').style.left = (p*100)+'%';
    const abierto = ultCifra.visual.alerta ? -14 : 0; $('arco').setAttribute('transform', `translate(0 ${abierto})`);
  } else esc.classList.add('oculto');
  // lista
  const li = $('lista');
  if (v.tipo === 'lista') {
    li.classList.remove('oculto'); $('listaTit').textContent = v.titulo||'';
    if (li.dataset.s !== String(s.a)) { li.dataset.s = s.a; $('puntos').innerHTML = (v.puntos||[]).map(p=>'<div class="punto"><span class="ok">✓</span><span>'+p+'</span></div>').join(''); }
    const ps = [...document.querySelectorAll('.punto')], n = ps.length, durS = s.b - s.a;
    ps.forEach((p,i)=>{ const ti = (durS*0.9)*i/n; const k=ease((dt-ti)/0.35); p.style.opacity=k; p.style.transform=`translateX(${(1-k)*-40}px)`; });
  } else li.classList.add('oculto');
  // escena (historia con dibujo y etiqueta)
  const es = $('escena');
  if (v.tipo === 'escena') {
    es.classList.remove('oculto');
    if (es.dataset.s !== String(s.a)) { es.dataset.s = s.a;
      $('emos').innerHTML = v.emojisHtml || ''; $('emos').className = ['','','dos','tres'][Math.min(3,(v.n||1))];
      $('etiq').textContent = v.etiqueta || ''; $('etiq').style.display = v.etiqueta ? '' : 'none';
      $('escTit').innerHTML = v.titulo ? (v.titulo + (v.destacar ? ' <span class="d">'+v.destacar+'</span>' : '')) : ''; }
    const k = back(dt/0.5);
    [...$('emos').children].forEach((im,i)=>{ const ki=back((dt-0.12*i)/0.5); im.style.transform=`scale(${Math.max(0,ki)}) translateY(${Math.sin(t*2.2+i)*10}px) rotate(${Math.sin(t*1.3+i)*4}deg)`; });
    const ke = back((dt-0.35)/0.45); $('etiq').style.transform = `translateX(-50%) rotate(-3deg) scale(${Math.max(0,ke)})`;
    es.querySelector('.rayos').style.transform = `rotate(${t*6}deg)`;
    $('escTit').style.opacity = ease(dt/0.3);
    $('chip').style.opacity = 1; $('titulo').style.display='none'; $('bloqueCifra').classList.add('oculto');
  } else es.classList.add('oculto');
  // terminal que se escribe sola
  const te = $('term');
  if (v.tipo === 'terminal') {
    te.classList.remove('oculto'); $('tventana').textContent = v.ventana || 'bash';
    const ls = v.lineas || [], dur = Math.max(1, (s.b - s.a) * 0.85);
    // cada comando se teclea; cada salida aparece de golpe
    const pesos = ls.map(l => l.cmd != null ? Math.max(6, l.cmd.length) : 8), tot = pesos.reduce((a,b)=>a+b,0);
    let acc = 0, html = '', cursor = true;
    for (let i=0;i<ls.length;i++){ const l=ls[i], a0=acc/tot*dur, a1=(acc+pesos[i])/tot*dur; acc+=pesos[i];
      if (dt < a0) break;
      const f = Math.min(1,(dt-a0)/(a1-a0));
      if (l.cmd != null) { const n=Math.floor(l.cmd.length*f); html += '<div class="l"><span class="p">'+(v.prompt||'$')+'</span> '+escH(l.cmd.slice(0,n))+(f<1?'<span class="cur"></span>':'')+'</div>'; if(f<1){cursor=false;} }
      else if (f>0.2) html += '<div class="l '+(l.color||'')+'">'+escH(l.out||'')+'</div>';
    }
    if (cursor) html += '<span class="cur" style="opacity:'+((t*2|0)%2)+'"></span>';
    $('tcuerpo').innerHTML = html;
    $('chip').style.opacity = 1; $('titulo').style.display='none'; $('bloqueCifra').classList.add('oculto');
  } else te.classList.add('oculto');
  // subtítulos
  const sub = $('subs');
  let g = null; for (const x of D.grupos) if (t >= x.a - 0.05 && t <= x.b + 0.25) g = x;
  if (g && !cierre) {
    sub.className = g.voz==='jota' ? 'jota' : '';
    sub.innerHTML = (g.voz==='jota'?'<span id="quien">JOTA</span>':'') + g.ws.map(w=>'<span class="w'+(t>=w.a&&t<w.b+0.02?' on':'')+'">'+w.w.replace(/</g,'&lt;')+'</span>').join(' ');
    sub.style.opacity = 1;
  } else sub.style.opacity = 0;
  // mascota
  const j = $('jota');
  const habla = s.voz === 'jota' && !cierre;
  const fi = Math.floor((t - s.a) * D.fps);
  const nivel = habla && s.niveles ? (s.niveles[fi] || 0) : 0;
  $('boca').setAttribute('height', 6 + nivel*34); $('boca').setAttribute('y', 146 - nivel*10);
  const parp = (t % 3.7) < 0.12 ? 0.1 : 1; $('oi').setAttribute('ry', 19*parp); $('od').setAttribute('ry', 19*parp);
  const mira = habla ? 0 : -6; $('ojos').setAttribute('transform', `translate(${mira} ${habla?0:4})`);
  $('antena').setAttribute('fill', habla && nivel>0.2 ? '#5CE1E6' : '#FFC83D');
  const salto = Math.sin(t*2.4)*6 + (habla ? Math.sin(t*14)*2*nivel : 0);
  j.style.transform = `translateY(${salto}px) ${habla?'scale(1.12)':''}`; j.style.transformOrigin='center bottom';
  j.style.opacity = cierre ? 0 : 1;
  // cierre
  const ci = $('cierre');
  if (cierre) { const k=ease(dt/0.5); ci.style.opacity=k; ci.style.transform=`scale(${0.92+0.08*k})`;
    ['cabeza','escala','lista','fuente','marca','escena','term'].forEach(id=>$(id).style.opacity=1-k); }
  else { ci.style.opacity=0; ['cabeza','fuente','marca'].forEach(id=>$(id).style.opacity=1); }
  // fundido de entrada
  $('lienzo').style.opacity = Math.min(1, t/0.3);
}
init();
</script></body></html>"""


def generar(guion, salida):
    from playwright.sync_api import sync_playwright
    sys.path.insert(0, str(AQUI))
    from crear import servidor
    preparar_voces()
    tmp = Path(tempfile.mkdtemp(prefix="jxvideo-"))
    escenas, grupos_todos, t = [], [], 0.25
    pistas = []
    for i, esc in enumerate(guion["escenas"]):
        voz = esc.get("voz", "dora")
        wav = tmp / f"e{i}.wav"
        dur, marcas = decir(esc["texto"], voz, wav)
        ws = []
        for tz, a, b in marcas:
            ws += palabras(tz, t + a, b - a)
        vis = dict(esc.get("visual", {}))
        if vis.get("tipo") == "escena":
            from crear import emojis as a_imagen
            lista = vis.get("emojis") or []
            vis["emojisHtml"] = "".join(a_imagen(x) for x in lista)
            vis["n"] = len(lista)
        e = {"a": round(t, 3), "b": round(t + dur, 3), "voz": voz, "visual": vis}
        if voz == "jota":
            e["niveles"] = niveles(wav)
        escenas.append(e)
        for g in grupos(ws):
            g["voz"] = voz
            grupos_todos.append(g)
        pistas.append((t, wav))
        t += dur + PAUSA
    total = t - PAUSA + FINAL
    datos = {"etiqueta": guion.get("etiqueta"), "fuente": guion.get("fuente"), "escala": bool(guion.get("escala")),
             "escenas": escenas, "grupos": grupos_todos, "fps": FPS}

    # audio: cada escena en su sitio
    args = ["ffmpeg", "-y", "-loglevel", "error"]
    for _, w in pistas:
        args += ["-i", str(w)]
    filtros = [f"[{i}:a]adelay={int(a * 1000)}|{int(a * 1000)}[a{i}]" for i, (a, _) in enumerate(pistas)]
    filtros.append("".join(f"[a{i}]" for i in range(len(pistas))) + f"amix=inputs={len(pistas)}:normalize=0,apad,atrim=0:{total:.2f}[out]")
    audio = tmp / "voz.wav"
    subprocess.run(args + ["-filter_complex", ";".join(filtros), "-map", "[out]", "-ar", "44100", "-ac", "2", str(audio)], check=True)

    pagina = PLANTILLAS / f"_video-{os.getpid()}.html"
    pagina.write_text(PAGINA.replace("__DATOS__", json.dumps(datos, ensure_ascii=False)), encoding="utf-8")
    srv = servidor()
    try:
        ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(FPS), "-c:v", "mjpeg", "-i", "-",
                               "-i", str(audio), "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
                               "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", str(salida)], stdin=subprocess.PIPE)
        with sync_playwright() as p:
            nav = p.chromium.launch()
            pg = nav.new_page(viewport={"width": ANCHO, "height": ALTO})
            pg.goto(f"http://127.0.0.1:{srv.server_port}/{pagina.name}")
            pg.evaluate("document.fonts.ready")
            pg.wait_for_timeout(300)
            n = int(total * FPS)
            for f in range(n):
                pg.evaluate(f"frame({f / FPS:.4f})")
                ff.stdin.write(pg.screenshot(type="jpeg", quality=92))
            nav.close()
        ff.stdin.close()
        ff.wait()
        if ff.returncode:
            raise RuntimeError("ffmpeg no pudo montar el vídeo")
    finally:
        srv.shutdown()
        pagina.unlink(missing_ok=True)
    # portada: el fotograma del título
    portada = Path(salida).with_suffix(".jpg")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{min(1.2, total / 2):.2f}", "-i", str(salida), "-frames:v", "1", "-q:v", "3", str(portada)], check=True)
    return {"duracion": round(total, 1), "portada": portada.name}


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    g = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    print(generar(g, Path(sys.argv[2])))
