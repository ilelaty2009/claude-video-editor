# Comparación con otros editores (2026-11-09)

Comparé este editor con lo que encontré en GitHub, TikTok/Instagram y la web. Fuentes: los README y páginas de
precios de cada herramienta y reseñas independientes (enlaces al final). "No verificado" = lo dice el fabricante o
una reseña, no lo probé yo.

## Quién es mejor en qué

| Función | Este editor | video-use (GitHub) | Guía Claude × Remotion (Michael Ly) | OpusClip | Descript | Submagic / CapCut / Captions |
|---|---|---|---|---|---|---|
| Precio | **Gratis, todo local** | Gratis + API de ElevenLabs (de pago) | Gratis (skill en Drive) | $15–29/mes | $16–50/mes | $12–20/mes |
| Cortar silencios y repeticiones | Sí | Sí | Sí | Sí | **Sí (el mejor: por texto)** | Sí |
| Editar borrando texto | **Sí (nuevo: `guion.py`)** | No | No | No | Sí | CapCut sí |
| Subtítulos palabra por palabra | Sí, 5 estilos, máx. 2 líneas medidas | Sí (2 palabras) | Sí | Sí, 20+ idiomas | Sí | **Sí (más plantillas de moda)** |
| Subtítulos medidos contra la voz | **Sí (nuevo: mide y corrige el desfase)** | No | Sí | No verificado | No verificado | No verificado |
| Escenas animadas / motion graphics | **Sí: 25 tipos + 5 animaciones completas** | Sí (vía HyperFrames/Remotion/Manim) | Sí | Sí (4.0) | Poco | Plantillas |
| Títulos detrás de la cabeza, fondo nuevo | Sí (nuevo, MODNet) | No | Sí | No | Sí (pantalla verde) | **Sí (CapCut: mejor recorte)** |
| Pantalla dividida, cara en círculo | Sí | No | Sí | Sí | Sí | Sí |
| Grabación de pantalla con zoom automático | Sí (nuevo) | No | Sí | No (lo dice su página) | Sí | No |
| Storyboard para revisar (Keep/Maybe/Drop) | Sí (nuevo) | No | **Sí (original)** | No | No | No |
| Hoja de marca + Brand Lab | Sí (nuevo) | No | **Sí (original)** | Plantilla de marca | Sí | Brand kit |
| Efectos 3D (HyperFrames) | Sí (nuevo, 1 efecto de ejemplo) | Sí | **Sí (más efectos: vidrio líquido, shaders)** | No | No | No |
| Clips cortos de un video largo | Sí (nuevo: `clips.py`, heurístico) | No | No | **Sí (el mejor; "Virality Score")** | Sí | Submagic (de pago) |
| Publicar directo en TikTok/Reels/Shorts | **No** | No | No | **Sí** | Sí | Sí |
| B-roll automático | Manual con Wikimedia (Claude lo busca) | No | No | **Sí (IA; 4 de 11 mal puestos según una reseña)** | Sí (genérico) | **Sí** |
| Corregir la mirada a cámara | **No** | No | No | No | Sí | **Sí** |
| Doblaje / traducción de voz | **No** (Claude puede traducir el .srt) | No | No | No | Sí | Sí |
| Música | **Original, compuesta por el editor** | No | Tu pack | No | Biblioteca | Biblioteca |
| Sonido medido (LUFS, música y efectos vs voz) | **Sí (-14 LUFS, pico real, cada efecto)** | Fundidos de 30 ms | Sí | No verificado | "Studio Sound" (**mejor limpieza de voz**) | No verificado |
| Control de calidad automático | **Sí (fps, tamaño, volumen, negros, parpadeos, sincronía, cortes)** | Sí (cada corte, hasta 3 intentos) | Sí | No | No | No |
| 60 fps | **Sí, siempre** | No | 30 fps | No verificado | Sí | Sí |
| Exportar cortes a DaVinci/Premiere | Sí (nuevo: EDL) | No | No | Sí (XML, plan Pro) | Sí | No |
| Reanudar un render interrumpido | **Sí** | No | No | (nube) | (nube) | (nube) |
| Pruebas automáticas del propio editor | **179** | No verificado | No | — | — | — |
| Transcripción con risas/aplausos y quién habla | **No** | **Sí (ElevenLabs Scribe)** | No | Sí | Sí | No verificado |
| Funciona en celular / sin instalar | **No** | No | No | Sí | Sí | **Sí** |

## Lo que copié en esta ronda (lo que ellos hacían mejor y se podía hacer gratis)
1. **Descript → editar borrando texto**: `scripts/guion.py` (borras frases del guion y se cortan del video).
2. **OpusClip → clips de un video largo**: `scripts/clips.py`. A propósito NO se llama "viralidad": una reseña midió
   que el clip con mejor resultado real tenía puntaje 64 y el peor 87; aquí el puntaje solo ordena y Claude decide.
3. **video-use → revisar cada corte**: `scripts/revisar_cortes.py` (antes/después de cada corte + clics de audio) y
   guion compacto para leer la transcripción gastando poco.
4. **Skill de r/ClaudeAI → "los subtítulos nunca antes de la palabra"**: medido contra el audio (Whisper marcaba las
   palabras ~40–48 ms antes en dos videos) y corregido solo.
5. **OpusClip/Descript → exportar a un editor profesional**: `scripts/exportar_edl.py`.
6. **Guía de Michael Ly (todo)**: storyboard, hoja de marca, Brand Lab, HyperFrames, títulos detrás de la cabeza,
   grabaciones de pantalla, generador de sonidos, HDR del iPhone, varios clips, medición del audio, parpadeos.

## Dónde siguen siendo mejores ellos (y por qué no lo copié)
- **Publicar directo en redes** (OpusClip, CapCut): necesita cuentas y permisos de cada red. Decisión de Pablo.
- **Corregir la mirada, doblaje con tu voz, b-roll generado con IA, 3D realista**: son modelos de IA de pago o muy
  pesados para un Mac de 8 GB. No hay versión gratis y local que funcione bien.
- **Recorte de persona** (CapCut): el suyo es más limpio en el pelo; el nuestro deja un borde claro con paredes claras.
- **Limpieza de voz** (Descript Studio Sound): quita eco de salón; la nuestra quita ruido y empareja, pero no el eco.
- **Risas, aplausos y quién habla** (video-use con ElevenLabs): de pago.
- **Plantillas de moda y uso desde el celular** (CapCut, Submagic): son apps con equipo de diseño; aquí Claude diseña.

## Conclusión honesta
No puedo afirmar que sea "el mejor editor del mundo": eso no se puede medir. Lo que sí se puede decir con lo medido:
- Es **más completo que los otros editores gratis de código abierto que revisé** (video-use, claude-code-video-toolkit,
  la guía Claude × Remotion): tiene lo de todos ellos juntos, más control de calidad medido y 179 pruebas.
- Frente a los de pago, **gana** en precio (gratis), privacidad (nada sale del Mac), 60 fps, audio medido y control
  de calidad; **pierde** en publicar en redes, funciones con IA pesada (mirada, doblaje, b-roll generado),
  plantillas de moda y comodidad (ellos son apps; este se usa hablando con Claude).

## Fuentes
- video-use: https://github.com/browser-use/video-use
- claude-code-video-toolkit: https://github.com/digitalsamba/claude-code-video-toolkit
- Guía Claude × Remotion: https://milleemd.com/guides/claude-x-remotion/
- HyperFrames: https://github.com/heygen-com/hyperframes
- OpusClip (precios y funciones): https://www.opus.pro/blog/best-ai-video-tools-for-content-creators
- Reseña de OpusClip con mediciones: https://bigvu.tv/blog/opus-clip-tested-2026-where-ai-wins-40-percent-discard/
- Alternativas a Descript: https://www.aicentralresources.com/blog/7-best-descript-alternatives-ai-video-podcast-editing-2026
- Alternativas a Submagic: https://www.blotato.com/blog/submagic-alternatives
- Consejos de edición (13,5 M de clips): https://www.opus.pro/blog/video-editing-tips
