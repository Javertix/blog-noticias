"""Compara voces: genera la misma frase con cada una y mide cuánto se entiende (WER con Whisper small)."""
import re, subprocess, sys, json, unicodedata
from pathlib import Path
import numpy as np, soundfile as sf, sherpa_onnx

AQ = Path(__file__).parent
TXT = ("¿Tu SSD se gasta si lo usas mucho? Hemos hecho las cuentas. Un disco de un terabyte aguanta "
       "seiscientos terabytes escritos. Escribiendo treinta gigas al día, te duraría unos cincuenta y cinco años. "
       "Pero ojo: puede fallar de golpe, sin avisar. Así que haz copias de seguridad.")

def piper(nombre, sid=0, ls=1.0):
    from piper import PiperVoice, SynthesisConfig
    d = AQ / f"vits-piper-{nombre}"
    v = PiperVoice.load(str(next(d.glob("*.onnx"))))
    cfg = SynthesisConfig(speaker_id=sid if v.config.num_speakers > 1 else None, length_scale=ls, noise_scale=0.6, noise_w_scale=0.8)
    def f(texto):
        a = np.concatenate([c.audio_float_array for c in v.synthesize(texto, syn_config=cfg)])
        return a.astype(np.float32), v.config.sample_rate
    return f

_K = {}
def kokoro(voz, modelo="kokoro-v1.0.onnx", speed=1.0):
    from kokoro_onnx import Kokoro
    if modelo not in _K:
        _K[modelo] = Kokoro(str(AQ / modelo), str(AQ / "voices-v1.0.bin"))
    return lambda t: _K[modelo].create(t, voice=voz, speed=speed, lang="es")

def carl(t):
    out = AQ / "_c.wav"
    subprocess.run([sys.executable, "-m", "piper", "-m", str(AQ / "es-carlfm-x-low.onnx"), "-f", str(out)], input=t.encode(), check=True, capture_output=True)
    a, sr = sf.read(out, dtype="float32"); return a, sr

VOCES = {
    "actual_dora_kokoro_int8": kokoro("ef_dora", "kokoro-v1.0.int8.onnx", 1.08),
    "actual_jota_piper_carlfm_xlow": carl,
    "kokoro_dora_fp32": kokoro("ef_dora", "kokoro-v1.0.onnx", 1.0),
    "kokoro_alex_fp32": kokoro("em_alex", "kokoro-v1.0.onnx", 1.0),
    "piper_davefx_medium": piper("es_ES-davefx-medium", 0, 0.92),
    "piper_sharvard_m": piper("es_ES-sharvard-medium", 0, 0.92),
    "piper_sharvard_f": piper("es_ES-sharvard-medium", 1, 0.92),
    "piper_claude_high_MX": piper("es_MX-claude-high", 0, 0.92),
    "piper_daniela_high_AR": piper("es_AR-daniela-high", 0, 0.92),
}

def asr():
    d = AQ / "sherpa-onnx-whisper-small"
    return sherpa_onnx.OfflineRecognizer.from_whisper(encoder=str(d / "small-encoder.int8.onnx"), decoder=str(d / "small-decoder.int8.onnx"),
                                                      tokens=str(d / "small-tokens.txt"), language="es", num_threads=4)

def norm(s):
    s = unicodedata.normalize("NFKD", s.lower()); s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9 ]", " ", s).split()

def wer(r, h):
    import numpy as np
    d = np.zeros((len(r) + 1, len(h) + 1), int); d[:, 0] = range(len(r) + 1); d[0, :] = range(len(h) + 1)
    for i in range(1, len(r) + 1):
        for j in range(1, len(h) + 1):
            d[i, j] = min(d[i-1, j] + 1, d[i, j-1] + 1, d[i-1, j-1] + (r[i-1] != h[j-1]))
    return d[-1, -1] / len(r)

if __name__ == "__main__":
    out = AQ / "muestras"; out.mkdir(exist_ok=True)
    rec = asr(); res = {}
    for k, f in VOCES.items():
        a, sr = f(TXT)
        p = out / f"{k}.wav"; sf.write(p, a, sr)
        a16 = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(p), "-ar", "16000", "-ac", "1", "-f", "f32le", "-"], capture_output=True).stdout
        s = rec.create_stream(); s.accept_waveform(16000, np.frombuffer(a16, np.float32)); rec.decode_stream(s)
        h = s.result.text
        res[k] = {"wer": round(wer(norm(TXT), norm(h)), 3), "dur": round(len(a) / sr, 1), "oido": h}
        print(k, res[k], flush=True)
    json.dump(res, open(out / "resultado.json", "w"), ensure_ascii=False, indent=1)
