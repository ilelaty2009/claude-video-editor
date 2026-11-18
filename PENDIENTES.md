# Pendientes (con su razón)

Lo que NO quedó hecho o NO se pudo verificar en esta sesión. Nada de esto rompe el editor.

## No verificado
- **Tiempo de render**: medido con Chrome y Spotify cerrados, un clip de 20 s a 60 fps en calidad final tarda
  **4 min 13 s** en total (antes: 96 s a 30 fps). Con la memoria llena (apps abiertas) el mismo clip tardó 22–40 min.
  Corrección: el "38 s de render" que se reportó antes era de una corrida que reanudó 2 de 4 partes, no un render completo.
- **Un archivo que desapareció**: una vez, a mitad de un render, el video preparado se borró de la caché, de `public/` y
  de la copia de Remotion al mismo tiempo. No se pudo encontrar la causa (se vigiló en las corridas siguientes y no se
  repitió). Quedó una red de seguridad: si falta, el editor lo detecta, rehace la copia y lo vuelve a poner.
- **Sonidos reales de Openverse** (`scripts/buscar_sonidos.py`): no se tocó ni se probó (necesita internet y gasta cupo
  diario). El editor sigue usando los sonidos sintetizados si no hay reales.
- **Videos largos (> 1 min)**: no se renderizaron; el video original de la entrevista (69 s) se borró del Mac durante la
  sesión (no por el editor). La calidad `maxima` SÍ se verificó con el clip de 20 s: pasa todo el control de calidad,
  pesa el doble que `final` y sale en H.264 nivel 5.0 (usar `final` para proyectores viejos).
- **Subtítulos en otros idiomas con caracteres fuera del latín** (árabe, chino): las métricas de fuentes solo cubren
  letras latinas; otros caracteres se estiman como anchos (1,2 em) y podrían quedar con más margen del necesario.
- **Compatibilidad en un TV/proyector real y al subir a TikTok/WhatsApp**: se verificó el formato (H.264 High 4.2,
  yuv420p, bt709, AAC 48 kHz, faststart, 60 fps), pero no se reprodujo en esos aparatos.

## Decisiones que quedaron para después
- **Recorte vertical que sigue la cara**: el seguimiento de cara mueve los zooms; el recorte de `reel`/`recorte` sigue
  siendo fijo (centrado en la posición promedio de la cara). Hacerlo dinámico exige recortar en Remotion en vez de
  ffmpeg y volver a medir rendimiento; con 8 GB de RAM no convenía.
- **Identidad de git**: resuelto. Todos los commits en GitHub usan `Pablo <350574886+ilelaty2009@users.noreply.github.com>`,
  el correo privado de tu cuenta ilelaty2009 (sale tu foto y tu perfil). Tu Mac ya está configurado con ese correo.
- **Del reel de referencia, lo que NO es edición**: las animaciones 3D, las figuras de palitos y la vista "explotada" del
  teclado se generan con otras herramientas (skills de animación); el editor las puede USAR como b-roll (`dividida` o
  `broll` con `archivo`), pero no las crea.
- **Pantalla dividida con la vista previa de Remotion Studio**: el pitido de la censura solo existe en la mezcla final
  (`scripts/mezcla.py`); en `npm run studio` se oye la palabra sin tapar.
- **Animación 3D realista tipo "Zack D Films"** (la 1.ª de las 6 skills del reel): no se puede gratis y sin internet; esas
  animaciones se hacen con generadores de video/3D con IA (de pago). Alternativas incluidas: /palitos y /minimalista.
- **Mapa real**: /mapa-ruta dibuja una ciudad ilustrada, no las calles reales. Para el mapa real, usar una captura propia.
- **Voces de la narración**: son las de macOS (`say`). Apple permite usarlas para tus propios proyectos; para videos de
  TikTok con fines comerciales revisa la licencia de macOS (no verificado para uso comercial).

- **Recorte de la persona (títulos detrás, fondo nuevo)**: con paredes muy claras queda un borde claro fino alrededor
  del pelo (el modelo incluye algo de pared en el contorno). Se redujo afinando y adelgazando la máscara; quitarlo del
  todo requiere "descontaminar" el color del borde (pendiente). Tarda ~4,5 s por cada segundo recortado (M2): por eso
  solo se recorta donde hay títulos detrás o fondo nuevo.

## Ronda 4 (reel + guía Claude × Remotion + comparación)
- **No copiado de la competencia (por costo o por necesitar tus cuentas)**: publicar directo en TikTok/Instagram/YouTube,
  corregir la mirada a cámara, doblaje con tu voz, b-roll generado con IA, 3D realista, transcripción con risas/aplausos
  y "quién habla". Detalle y fuentes en COMPARACION.md.
- **HyperFrames**: integrado con UN efecto de ejemplo (`tarjeta3d`). "Vidrio líquido" real y transiciones con shaders del
  catálogo de HyperFrames no se agregaron (el vidrio se hizo en Remotion como banner `vidrio`; glitch como transición).
  Necesita internet al renderizar un efecto (GSAP se carga de un CDN). Probado solo en vertical dentro del editor.
- **Exportar a DaVinci (EDL)**: el archivo se genera y su formato se prueba, pero NO lo abrí en DaVinci/Premiere.
- **Brand Lab**: genera 22 muestras con el video de demostración; "rehacer los Maybe con tus notas" lo hace Claude a
  mano leyendo `respuestas.json` (no hay un botón automático).
- **Grabaciones de pantalla**: probado con una grabación sintética; falta una grabación real de Pablo. No dibuja un
  cursor suavizado (Screen Studio sí): solo hace el zoom.
- **Marca desde una web**: probado con una sola página (milleemd.com). En páginas que cargan sus estilos con JavaScript
  puede no encontrar colores.
- **Clips de un video largo**: probado con la transcripción de 69 s de la entrevista; falta un video realmente largo.
- **Storyboard en celular**: la página se probó en el navegador del computador, no en el teléfono.

