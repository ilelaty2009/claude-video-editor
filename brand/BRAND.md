# Hoja de marca de Pablo (brand sheet)

Esto le dice a Claude cómo se ven TUS videos: colores, fuentes, subtítulos, títulos y sonidos. Sin esto, cada video
empieza de cero; con esto, todos parecen del mismo canal. Los valores que usa el código están en `brand/marca.json`.

## Colores (brand/marca.json → colores)
| papel | color | dónde se usa |
|---|---|---|
| amarillo (principal) | #FFC94D | palabra de color en titulares, números, destacados |
| azul (secundario) | #5CC8FF | segunda palabra de color, gráficas |
| rojo (acento) | #FF3B5C | palabra activa de los subtítulos cine, puntos de las etiquetas |
| verde | #2ED47A | chulitos de listas, tarjetas "sí" |
| fondo | #1d2447 → #07080f | fondo de escenas de pantalla completa (degradado azul noche) |

## Fuentes
- Escenas, títulos y gráficos: **Inter** (Black 900 y Bold 700).
- Subtítulos TikTok: **Montserrat Black**. Cine/caja/etiqueta: Inter.
- Para una fuente nueva: `.venv/bin/python scripts/fuente_google.py "Nombre"` y ponla en marca.json.

## Subtítulos y títulos
- Clase/TV: estilo `cine` (palabra actual en rojo, máx. 2 líneas). Proyector con mucha luz: `caja`.
- TikTok: `tiktok` (amarillo, borde negro, emojis) o `etiqueta` (una palabra) con pantalla dividida.
- Títulos: MAYÚSCULAS, 1–3 palabras por línea, una sola palabra de color.

## Sonidos y música
- Efectos: los sintetizados de `public/sfx/` (y los reales de Openverse en `public/sfx/real/` si existen).
  Tus propios sonidos: ponlos en `public/sfx/propios/` con el nombre de lo que suenan (whoosh, pop, ding…).
- Música: original del editor (calma para clase, energía para TikTok), siempre debajo de la voz (ducking).

## Reglas anti "AI slop" (lo que hace que un video se vea hecho con IA)
- Nada de imágenes sobreanimadas (todo rebotando, girando o con zoom a la vez).
- Nada de fuentes serif en itálica.
- Nada de movimientos de cámara que no tengan razón (un acercamiento debe coincidir con algo que se dice).
- Una idea por escena, una palabra de color por titular, nunca dos pantallas completas seguidas sin ver a la persona.

## Cómo se actualiza
- Desde tu web: `.venv/bin/python scripts/marca.py desde-web https://tu-pagina.com`
- Desde videos que te gustan: `bash scripts/analizar_referencia.sh <link o archivo>` y Claude anota las reglas aquí.
- Brand Lab: Claude arma muestras de estilo para que las califiques Keep / Maybe / Drop (`scripts/brand_lab.py`).
- Cada vez que algo te guste, pídele a Claude: "agrega esto a mi marca".
