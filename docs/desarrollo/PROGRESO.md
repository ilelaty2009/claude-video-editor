# Progreso — rama `mejoras-pro`

Este archivo (más el historial de git) es la memoria del trabajo. Si la sesión se corta, se retoma desde aquí.

## Fase 0 — auditoría
- [x] `git init`, primer commit en `main` con todo tal cual (commit `7c70455`)
- [x] Rama `mejoras-pro`
- [x] AUDITORIA.md (qué hace, estructura, qué funciona, qué está roto, 10 problemas)
- [x] Render de prueba con la versión original: 96 s, 30 fps, -14,6 LUFS, -1,4 dBTP (ver AUDITORIA.md)

## Fase 1 — mejoras (cada una con criterio medible)
| # | Frente | Criterio medible | Estado |
|---|---|---|---|
| 1 | 60 fps | `ffprobe` del resultado = 60/1; animaciones atadas a tiempo (src/tiempo.ts) | hecho, verificado en 16:9 |
| 2 | Formatos | tv 1920x1080, reel 1080x1920, cuadrado 1080x1080, retrato 1080x1350 | hecho, `test_formatos.py` |
| 3 | Exportación | H.264 High nivel 4.2, yuv420p, bt709, AAC 48 kHz, faststart; preview/final/maxima | hecho, verificado |
| 4 | Audio | -14 LUFS ±1 y pico real ≤ -1 dBTP medido en el archivo FINAL | hecho: -14,0 / -2,6 en 16:9 |
| 5 | Subtítulos | ≤ 2 líneas, sin cortar palabras, zona segura, contraste ≥ 4,5, letra ≥ 5,5 % | hecho, `subtitulos.test.ts` |
| 6 | Animación | curvas, salidas escalonadas, seguimiento de cara, escenas en src/escenas/ | hecho |
| 7 | Flujo | un comando, caché por huella, reanudar, reintento si se cuelga, errores en español | hecho, reanudación probada |
| 8 | Config | `editor.config.json` con presets colegio-tv y tiktok | hecho |
| 9 | Pruebas | `npm test`: tipos + 63 vitest + 31 Python | hecho, todo pasa |
| 10 | GitHub | README es/en con capturas, LICENSE, sin secretos | hecho |

## Pendiente en esta sesión
- [x] Verificar render 9:16 (preset tiktok) con el clip real: TODO BIEN (-14,0 LUFS, -2,3 dBTP, 60 fps)
- [x] Demo sin personas: 16:9 y 9:16 TODO BIEN (npm run prueba:render), capturas y GIF en docs/
- [ ] Rama limpia para publicar (sin historial con la foto del salón ni skills de terceros)

## Suposiciones y decisiones (tomadas sin preguntar, se pueden cambiar)
- Las capturas del README NO usan el video de la entrevista (salen otras personas). Se usa un video de demostración
  sin personas (fondo animado + voz sintética de macOS `say`), editado con el propio editor.
- Las skills de `.claude/skills/` vienen de `remotion-dev/skills`, cuyo repositorio no muestra licencia: no se publican
  (el instalador las vuelve a bajar). `public/broll/prueba_mapa.jpg` es un fotograma del salón: no se publica.
- El audio final se mezcla en Python (`scripts/mezcla.py`) y no con Remotion: renderizar el audio con Remotion tardaba
  91 s extra y por partes dejaba un desfase de 0,35 ms en cada unión. Medido: misma mezcla (desfase ≤ 0,33 ms).
- Estilo `clase` sigue con subtítulos `cine` (lo que le gustó a Pablo) pero más grandes (46 → 62 px) y con borde fino.
- Memoria: este Mac tiene 8 GB y durante la sesión tenía 9,6 GB en swap (Claude, Chrome, Spotify, una VM). Con los
  valores por defecto de Remotion (4 hilos, caché de video hasta 1,4 GB) los renders se trababan (una parte de 10 s:
  16 min, 93 % del tiempo esperando memoria). Decisión: en Macs de ≤ 8 GB o con < 2,5 GB libres se usan 2 hilos y
  caché de 256 MB, partes de 6 s, espera por cuadro de 15 min y 4 intentos por parte; y se avisa que cerrar apps acelera.
- Nombre/correo de git: "Pablo <350574886+ilelaty2009@users.noreply.github.com>" (correo privado de GitHub de tu
  cuenta, no tu correo real) en todos los commits.

## Ronda 2 (2026-11-09): reel de referencia + extras
- [x] Visto el reel (Instagram DfdLdLIBwo4, 41 s, 9:16): pantalla dividida, subtítulos de una palabra en etiqueta,
      banner fijo, app escribiendo (ya existía: `chat`), gráfica con contador, mapa con ruta, llamada a la acción.
- [x] Escenas nuevas: `dividida` (apilada / lado / pip), `grafica` (línea / barras), `mapa`, `cta`; estilo de subtítulos
      `etiqueta`; `banners`; `censurar` (pitido). Verificado: render 9:16 del demo TODO BIEN (-14,0 LUFS, 60 fps) y
      fotogramas revisados en 16:9 y 9:16.
- [x] Extras investigados (OpusClip): aviso `GANCHO:` de los primeros 3 s, capítulos para YouTube, zonas seguras pintadas
      en la revisión. Arreglado un error viejo de `revisar.sh` que solo sacaba 1 fotograma.
- [x] Pruebas: 92 vitest + 39 Python, todas pasan.
- No hecho (anotado en PENDIENTES.md): recorte vertical que sigue la cara en movimiento; los gráficos del reel original
  hechos con otras skills (animación 3D, figuras de palitos, vista explotada) son generación de contenido, no edición.

## Ronda 3 (2026-11-09): las 6 skills que menciona el reel
- [x] /minimalista, /palitos, /despiece, /mapa-ruta, /grafica (composición `Animacion`, `scripts/animar.py`, recetas en
      `demo/animaciones/`, comandos en `.claude/skills/`). Voz narrada (macOS), música, -14 LUFS, 60 fps.
- [x] Verificado: las 5 renderizadas en 9:16 (23–39 s cada una) y el mapa en 16:9; control de calidad todo ✓;
      cuadros revisados (se corrigieron poses, tamaño del despiece, ruta vertical del mapa, eje de la gráfica).
- [x] Pruebas: 95 vitest + 43 Python.
- [ ] /zach-d-films (3D realista): no posible gratis/local — explicado en PENDIENTES.md.


## Ronda 4 (2026-11-09): reel "How to make your own AI video editor for free" + guía Claude × Remotion (Michael Ly)
Fuentes: Instagram DfaKC58sBsb (98 s) y milleemd.com/guides/claude-x-remotion. Lo que dicen/muestran vs lo que tenemos:

| # | Qué | Teníamos | Estado |
|---|---|---|---|
| A1 | Storyboard de revisión: un clip por tramo, Keep/Maybe/Drop + notas, "Submit", Claude responde en la página | no | pendiente |
| A2 | Brand sheet `brand/BRAND.md` (colores, fuentes, subtítulos, títulos, sonidos) + sacarlo de una web | estilo.md (parcial) | pendiente |
| A3 | Brand Lab: página de muestras en tu marca para calificar Keep/Maybe/Drop | no | pendiente |
| A4 | Varios clips a la vez; referencias por link (yt-dlp); HDR de iPhone a SDR; corte de pausas de 0,1 s | no / no / no / opción | pendiente |
| A5 | Fuentes de Google por nombre (marca) | no | pendiente |
| B1 | Títulos DETRÁS de la cabeza (recorte de la persona) y pantalla verde / fondo nuevo | no | pendiente |
| B2 | Grabaciones de pantalla "cinematográficas" (zoom automático donde pasa algo, ventana con sombra) | no | pendiente |
| B3 | Frases cinéticas a pantalla completa, diagrama app→app, ventana de app con checklist y barra de progreso, collage de miniaturas, anotaciones a mano, vidrio líquido, transiciones tipo shader/glitch, palabra resaltada con caja, título fijo de texto | parcial | pendiente |
| B4 | HyperFrames (Apache 2.0) para efectos que Remotion no trae | no | pendiente |
| C1 | Medir música y CADA efecto contra la voz; escaneo de cuadros con fallas; re-sincronizar subtítulos con la voz | solo LUFS total | pendiente |
| C2 | Generador de sonidos que faltan (swipe, glitch, blip, tap, snap, chime) + packs propios de sonidos y música | sintetizados fijos | pendiente |
| C3 | Reglas anti "AI slop" (sin imágenes sobreanimadas, sin serif itálica, sin movimientos de cámara innecesarios) | no | pendiente |
| D | Comparación con otros editores (GitHub, TikTok, Instagram, web) y copiar lo que hacen mejor | — | pendiente |

### Estado ronda 4: TERMINADA (2026-11-09)
| # | Qué | Estado y cómo se verificó |
|---|---|---|
| A1 | Storyboard Keep/Maybe/Drop | hecho; probado en navegador (votar, nota, enviar, respuesta de Claude) y en el render real |
| A2 | Hoja de marca | hecho; marca desde web probada (colores + fuente Fraunces) y cuadro renderizado con ella |
| A3 | Brand Lab | hecho; 22 muestras generadas y revisadas en mosaico |
| A4 | Varios clips, links, HDR, pausas 0,15 s en tiktok | hecho; pruebas automáticas (HDR sintético, unión de 2 clips) |
| A5 | Fuentes de Google por nombre | hecho; probado bajando Fraunces |
| B1 | Títulos detrás de la cabeza y fondo nuevo | hecho; render real con el clip (la cabeza tapa el título) |
| B2 | Grabación de pantalla con zoom automático | hecho; 4 cuadros revisados (1,26x → completo → 2,2x) |
| B3 | Cinética, diagrama, ventana, collage, anotación, glitch, banners texto/vidrio, palabra en caja | hecho; hojas de revisión en 16:9 y 9:16 y render real |
| B4 | HyperFrames | hecho; efecto tarjeta3d renderizado con transparencia y visto encima del video |
| C1 | Música/efectos vs voz, cuadros con fallas, sincronía | hecho; pruebas con señales sintéticas y medición real (+48 ms, +39 ms) |
| C2 | Generador de sonidos + packs propios | hecho; 7 sonidos "escuchados" con oido.py; prioridad de propios probada |
| C3 | Reglas anti-slop | en CLAUDE.md, BRAND.md y fuente_google.py (rechaza itálicas) |
| D | Comparación con otros editores | COMPARACION.md; copiado: guion, clips, EDL, subtítulos sin adelanto, revisión de cortes |
| — | Render resistente | corta en seguida si Remotion se cae y reintenta (antes esperaba 15 min) |
| — | Pruebas | 105 vitest + 74 Python = 179, todas pasan |

