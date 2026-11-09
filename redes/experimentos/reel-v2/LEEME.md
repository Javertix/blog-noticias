# Experimento: reel v2 (NO se usa en la publicación automática)

Prueba del 10/11/2026 para comparar con `redes/video.py`:
- Voz de Dora con el modelo Kokoro completo (no int8) y cada frase sintetizada entera (sin trocear en las comas).
- Jota con Piper es_ES sharvard (medium) en vez de carlfm x-low.
- Más movimiento: primer fotograma ya lleno, zoom en cada corte, sacudida, contadores, subtítulos grandes palabra a palabra, barra de progreso, efectos y base rítmica sintetizados.
- `voces.py` compara voces y mide cuánto se entienden con Whisper (WER).

Los modelos (Kokoro, Piper sharvard/davefx, Whisper small) se descargan de GitHub releases; ver el código.
