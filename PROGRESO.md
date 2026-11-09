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
- Nombre/correo de git: el primer commit quedó como "Pablo <pablo@users.noreply.github.com>"; desde el segundo se usa
  "Pablo <350574886+ilelaty2009@users.noreply.github.com>" (correo privado de GitHub de tu cuenta, no tu correo real).
