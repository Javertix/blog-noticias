# Noticias automáticas del blog de Javertix

Cada mañana una tarea programada de Claude escribe 5 artículos (ciberseguridad, apps, automatización,
sistemas y actualidad) y los añade a `feed.json`. La web **javertix.site** lee este archivo cada 15 minutos
y publica sola los artículos nuevos en el blog, con su foto, su SEO y las fuentes.

- No toques `feed.json` a mano salvo para quitar un artículo que todavía no se haya publicado.
- Para despublicar uno que ya está en la web: Panel › Contenido › Blog › abrirlo › Despublicar.
- Para pararlo todo: Panel › Contenido › Blog › «Noticias automáticas» › desmarcar.

## Formato de cada artículo

```json
{
  "id": "2026-11-02-ciberseguridad",
  "slug": "titulo-en-minusculas-con-guiones",
  "title": "Título (máx. 160)",
  "category": "Ciberseguridad | Apps | Automatización | Sistemas | Actualidad",
  "date": "2026-11-02T08:00:00",
  "excerpt": "Resumen de 1-2 frases",
  "metaTitle": "Título SEO (máx. 60)",
  "metaDescription": "Descripción SEO (140-160)",
  "tags": "etiqueta, otra",
  "html": "<p>…</p><h2>…</h2>…",
  "sources": [{"title": "Medio: titular", "url": "https://…"}],
  "image": "https://images.unsplash.com/photo-…?fm=jpg&q=80&w=1600&fit=max",
  "imageAlt": "Descripción de la foto",
  "imageCredit": "Foto: Nombre en Unsplash"
}
```
