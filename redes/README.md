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
  - `explicado`: reel animado con voz (18-30 s, formato v2): gancho en el primer fotograma, zoom en cada
    corte, contadores, subtítulos grandes palabra a palabra, la mascota Jota y cierre. En vez de `diapositivas` lleva
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
| `terminal` | Meme de terminal: comandos y salida, el remate en la última línea | `titulo`?, `ventana`?, `prompt`?, `lineas`: [{`cmd`} o {`out`, `color`: out/gris/ok/warn/error}] (2-9) |
| `codigo` | Meme de código: el chiste está en el código o un comentario | `titulo`?, `archivo`, `codigo` (máx. 14 líneas de 40 caracteres, `\n` entre líneas) |
| `error` | Ventana de error inventada (sin marcas) | `titulo`?, `ventana`, `emoji`, `mensaje`, `botones` [1-3], `abajo`? |
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

## Vídeos explicados (`"formato": "explicado"`) — formato v2

Los monta `redes/video.py` con la plantilla `plantillas/reel.html`. Voces gratuitas y locales, en español de España:
**narrador** (Álex, Kokoro `em_alex`, modelo completo) y **jota** (la mascota robot, Piper `es_ES-sharvard-medium`).
Los modelos (~420 MB) se descargan de GitHub releases la primera vez. Cada frase se sintetiza entera (la
entonación sale natural); la puntuación marca las pausas. Efectos (whoosh, pop, ding, golpe) y una base
rítmica suave se sintetizan en el propio script (sin derechos de autor).

```json
"guion": {
  "etiqueta": "MITO O VERDAD",
  "fuente": "Samsung 990 EVO Plus 1 TB · ficha técnica (600 TBW)",
  "escenas": [
    {"texto": "¿Tu SSD se gasta si lo usas mucho?", "visual": {"tipo": "gancho", "titulo": "¿TU SSD SE", "destacar": "GASTA?", "emoji": "ssd", "sello": "¿MITO?"}},
    {"voz": "jota", "texto": "Espóiler: te jubilas tú antes que él.", "visual": {"tipo": "gancho", "titulo": "TE JUBILAS", "destacar": "TÚ ANTES", "emoji": "🧓"}},
    {"texto": "Un SSD de un terabyte aguanta unos seiscientos terabytes escritos.", "visual": {"tipo": "cifra", "antes": "Un SSD de <b>1 TB</b> aguanta…", "hasta": 600, "unidad": "TB", "pie": "escritos, según el fabricante", "emoji": "ssd"}},
    {"texto": "Si escribes treinta gigas cada día, que ya es mucho, te dura…", "visual": {"tipo": "barra", "antes": "Escribiendo <b>30 GB al día</b>", "hasta": 55, "unidad": "AÑOS", "pie": "de vida útil", "emoji": "👴", "oculto": true}},
    {"texto": "¡Cincuenta y cinco años!", "pausa": 0.2, "visual": {"tipo": "barra", "antes": "Escribiendo <b>30 GB al día</b>", "hasta": 55, "unidad": "AÑOS", "pie": "de vida útil", "emoji": "👴", "sigue": true, "ding": true}},
    {"texto": "Pero ojo: puede morir de golpe, sin avisar.", "visual": {"tipo": "alerta", "titulo": "PUEDE MORIR", "destacar": "SIN AVISAR", "emoji": "💀"}},
    {"texto": "Mira su salud con CrystalDiskInfo y haz copias de seguridad.", "visual": {"tipo": "lista", "titulo": "QUÉ HACER", "puntos": [{"e": "🩺", "t": "Mira su salud", "s": "CrystalDiskInfo o smartctl"}, {"e": "☁️", "t": "Copias de seguridad", "s": "regla 3-2-1"}]}},
    {"voz": "jota", "texto": "Dale a seguir: cada semana desmontamos un mito.", "visual": {"tipo": "cierre", "texto": "Un mito informático cada semana"}}
  ]
}
```
- `voz`: `narrador` (por defecto) o `jota` (para el giro gracioso, el «espóiler» y el cierre).
- `visual.tipo`:
  - `gancho`: texto enorme (`titulo` + `destacar`, máx. 34 caracteres entre los dos), `emoji` grande y `sello` opcional («¿MITO?», «¡OJO!»).
  - `cifra`: número que se cuenta solo (`hasta` numérico, `unidad` ≤ 6, `decimales`, `prefijo`, `antes`, `pie`, `emoji`).
    Si no es un número, `cifra` con texto corto (≤ 8). `oculto: true` enseña «¿?» (suspense para la escena siguiente).
  - `barra`: como `cifra` con una barra que se llena. `sigue: true` continúa la barra de la escena anterior. `ding: true` confeti y campanita.
  - `alerta`: fondo rojo, sacudida y golpe (`titulo`, `destacar`, `emoji`). Para el «pero ojo».
  - `lista`: 2-3 tarjetas (`titulo`, `puntos`: [{`e`: emoji, `t`: ≤ 22 caracteres, `s`: subtítulo}]).
  - `terminal`: se escribe sola (`titulo` opcional arriba, `ventana`, `prompt`, `lineas`: [{`cmd`} o {`out`, `color`: ok/warn/error/gris}], 1-7 líneas de ≤ 36 caracteres).
  - `escena`: 1-3 emojis grandes + etiqueta amarilla (≤ 14) y `titulo`/`destacar` opcionales. Para contar historias.
  - `cierre`: logo, `texto` (la serie: «Un mito informático cada semana») y botón «SÍGUENOS».
- Emojis: el carácter (💀) o su código Twemoji; `ssd` es un dibujo propio de un SSD.
- 5-10 escenas, 60-105 palabras habladas (≈ 18-30 s). La primera es el gancho (`gancho`, `escena` o `terminal` con `titulo`):
  se ve completo en el fotograma 0, sin fundidos. La última es `cierre`.
- Números con letras en `texto` («cincuenta y cinco») y con cifras en `visual`.
- **Nada de palabras en inglés en `texto`** (las voces las leen mal): o se traduce o se escribe como suena
  («espóiler», «backup» → «copia de seguridad»). Los comandos van en `visual`, y en `texto` se dicen en castellano.
  Evitar «Síguenos» (la voz de Jota lo pronuncia mal): «Dale a seguir».
- Datos siempre comprobados y con `fuente`.

## Créditos

Fuentes Bricolage Grotesque, Instrument Sans y JetBrains Mono (SIL OFL). Voces Kokoro (Apache 2.0) y Piper (MIT). Emojis de Twemoji (CC-BY 4.0), ver
`plantillas/emoji/CREDITOS.txt`.
