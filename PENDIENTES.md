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
- **Identidad de git**: el primer commit dice `Pablo <pablo@users.noreply.github.com>` (correo que no es de tu
  cuenta). Los commits nuevos usan `350574886+ilelaty2009@users.noreply.github.com`, el correo privado de tu cuenta
  ilelaty2009. En tu Mac: `git config user.email 350574886+ilelaty2009@users.noreply.github.com`.
