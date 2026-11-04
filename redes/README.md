# Redes sociales de Javertix (Instagram y Facebook)

Cada mañana una tarea programada prepara las publicaciones del día y las deja aquí. La web
(javertix.site) lee `redes/feed.json` cada 15 minutos, descarga las imágenes y las publica a su hora
en la página de Facebook y en la cuenta de Instagram (Panel › Contenido › Redes sociales).

## Cómo se añade una publicación

```bash
python3 redes/crear.py /tmp/nuevos.json --prueba   # genera las imágenes en redes/prueba/ para revisarlas
python3 redes/crear.py /tmp/nuevos.json            # comprueba, genera en redes/img/ y lo añade a feed.json
```

El script comprueba el formato, que el texto quepa en cada imagen y que no haya palabras malsonantes.
Borra solo las publicaciones de más de 21 días y sus imágenes. `redes/prueba/` no se sube (está en .gitignore).

## Formato de `nuevos.json` (lista)

```json
{
  "id": "2026-11-04-meme",
  "tipo": "meme",
  "publicar": "2026-11-04T20:00:00+01:00",
  "texto": "Texto de la publicación (emojis permitidos). Sin hashtags: van aparte.",
  "hashtags": ["#humorinformatico", "#programacion", "#javertix"],
  "enlace": "https://javertix.site/blog/...",
  "alt": "Descripción de la imagen para personas ciegas",
  "tendencia": {"formato": "Nombre del formato de meme", "fuente": "https://..."},
  "diapositivas": [ { "plantilla": "comparacion", "...": "..." } ]
}
```

- `id`: `AAAA-MM-DD-algo`, único. `tipo`: `meme`, `noticia`, `dato`, `tip` o `presentacion`.
- `formato` (opcional, por defecto `post`):
  - `post`: foto o carrusel en el perfil (1080 × 1350).
  - `historia`: historia de Instagram y Facebook (1080 × 1920), 1-3 imágenes; dura 24 h.
  - `reel`: vídeo vertical de 2-8 diapositivas con zoom suave y fundidos (unos 3,5 s cada una,
    `segundos` lo cambia). Se publica como reel en Instagram y como vídeo en Facebook.
    No admite la plantilla `portada`.
  - `explicado`: vídeo animado con voz (25-60 s) al estilo «dato rápido»: gancho, cifras grandes que
    aparecen, subtítulos palabra a palabra, la mascota Jota y cierre. En vez de `diapositivas` lleva
    `guion` (ver abajo). Se publica como reel en Instagram/Facebook y va a los borradores de TikTok.
- `publicar`: hora de Madrid con zona (`+01:00` en invierno, `+02:00` en verano).
- `texto`: hasta 1800 caracteres. En Instagram los enlaces no funcionan; si hay `enlace`, en el texto
  di «(enlace en la bio)»: la web lo cambia por el enlace de verdad en Facebook.
- `hashtags`: 3-12, siempre `#javertix`.
- `enlace` (opcional): solo de `https://javertix.site/`.
- `diapositivas`: 1 = foto normal; 2-10 = carrusel.

## Plantillas (1080 × 1350)

Todas admiten `"fondo": "claro" | "suave" | "oscuro" | "azul" | "amarillo"`. Colores por tipo para que el
perfil quede ordenado: noticias en oscuro, memes en claro/suave, tips en azul y datos en amarillo. En los textos, `**así**` va en negrita,
`\n` es un salto de línea y los emojis se dibujan con Twemoji.

| Plantilla | Para | Campos |
|---|---|---|
| `comparacion` | Meme «esto no / esto sí» (2-4 filas) | `titulo`?, `filas`: [{`emoji`, `texto`}] |
| `nadie-yo` | Meme «Nadie: / Yo:» | `lineas`: [{`quien`, `texto`?}], `emoji`? |
| `chat` | Conversación de WhatsApp inventada | `titulo`?, `contacto`, `emoji`, `mensajes`: [{`de`?, `texto`, `yo`?}] |
| `post` | Publicación de texto de Javertix (estilo tuit) | `texto`, `hace`?, `respuestas`?, `compartidos`?, `megusta`? |
| `expectativa` | Expectativa / realidad (2 paneles) | `titulo`?, `paneles`: [{`etiqueta`, `emoji`, `texto`}] |
| `escala` | Niveles que suben (3-5) | `titulo`?, `niveles`: [{`texto`, `emoji`?}] |
| `clasico` | Texto arriba, emoji grande, texto abajo | `arriba`, `emoji`, `abajo`? |
| `portada` | Portada de noticia con foto | `categoria`, `titulo`, `subtitulo`?, `foto` (images.unsplash.com) |
| `puntos` | Lista numerada (2-4 puntos) | `titulo`, `puntos`: [texto] |
| `cierre` | Última diapositiva con llamada a la acción | `texto`, `subtexto`?, `cta`? |
| `tip` | Consejo práctico (fondo azul) | `etiqueta`?, `emoji`?, `titulo`, `texto`?, `puntos`? |
| `logo` | Logo completo de la marca | `titulo`?, `texto`? |
| `dato` | Dato curioso (fondo amarillo) | `etiqueta`?, `cifra`? o `emoji`?, `texto`, `fuente`? |
| `texto` | Diapositiva genérica | `etiqueta`?, `titulo`, `texto`? |

La foto de la `portada` la pone la web: aquí se genera un PNG transparente y la web coloca debajo la foto
de Unsplash (el contenedor de la tarea no puede descargarla).

## Vídeos explicados (`"formato": "explicado"`)

Los monta `redes/video.py`. Voces gratuitas y locales: **Dora** (narradora, Kokoro `ef_dora`) y **Jota**
(la mascota robot, Piper `es-carlfm`). Los modelos (~140 MB) se descargan de GitHub la primera vez.
La puntuación marca las pausas: cada coma y cada punto es una pausa real en la voz.

```json
"guion": {
  "etiqueta": "DATO RÁPIDO",
  "fuente": "Hive Systems 2025 · 12× RTX 5090",
  "escala": true,
  "escenas": [
    {"voz": "dora", "texto": "¿Cuánto tarda…?", "visual": {"tipo": "titulo", "titulo": "¿Cuánto tarda…", "destacar": "tu contraseña?"}},
    {"voz": "dora", "texto": "…tres semanas.", "visual": {"tipo": "cifra", "cifra": "≈ 3 semanas", "pie": "8 caracteres", "chip": "a-z 0-9", "segundos": 1814400}},
    {"voz": "jota", "texto": "Pero ojo…", "visual": {"tipo": "cifra", "cifra": "0 segundos", "pie": "si se filtra", "segundos": 0, "alerta": true}},
    {"voz": "dora", "texto": "Así que…", "visual": {"tipo": "lista", "titulo": "Qué hacer", "puntos": ["…", "…", "…"]}},
    {"voz": "dora", "texto": "Síguenos para más. ¿Qué quieres que investiguemos?", "visual": {"tipo": "cierre"}}
  ]
}
```
- 4-12 escenas; la primera `titulo` y la última `cierre`. Entre 50 y 140 palabras habladas en total.
- `cifra`: máx. 14 caracteres. `escala: true` añade una barra de tiempo (1 s → 1000 años) y entonces
  cada cifra lleva `segundos`. `alerta: true` la pone en rojo.
- `lista`: 2-4 puntos cortos. Jota (voz robótica) para el giro o la frase graciosa; Dora para el resto.
- Escribe los números con letras en `texto` («sesenta y dos») y con cifras en `visual`.
- Datos siempre comprobados y con `fuente`.

## Créditos

Fuentes Bricolage Grotesque, Instrument Sans y JetBrains Mono (SIL OFL). Voces Kokoro (Apache 2.0) y Piper (MIT). Emojis de Twemoji (CC-BY 4.0), ver
`plantillas/emoji/CREDITOS.txt`.
