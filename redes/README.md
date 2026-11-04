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

## Créditos

Fuentes Bricolage Grotesque e Instrument Sans (SIL OFL). Emojis de Twemoji (CC-BY 4.0), ver
`plantillas/emoji/CREDITOS.txt`.
