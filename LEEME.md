# Cómo usar tu editor de videos con Claude

## Una sola vez: instalar
1. Abre esta carpeta (Películas → claude-video-editor).
2. Doble clic en **instalar.command**.
   - Si el Mac dice que no puede abrirlo: clic derecho → Abrir → Abrir.
   - No pide contraseña. Descarga ~1 GB (una sola vez).
   - Si sale una ventana de Apple pidiendo instalar "herramientas de línea de comandos": dale Instalar y luego abre instalar.command otra vez.
   - Tarda unos 5–15 minutos. Cuando diga **TODO LISTO**, ciérralo.
   - Si algo falla, el instalador dice qué fue. Tómale pantallazo y mándaselo a Claude. Puedes volver a correrlo sin problema.

## Cada vez que quieras editar un video
1. Pon tu video crudo en la carpeta **videos/** (por ejemplo, `videos/mi-video.mov`).
2. (Opcional) Pon un video cuyo estilo te guste en **referencias/**.
3. Abre la app de Claude → pestaña **Code** → elige esta carpeta.
4. Escríbele algo como:
   - "Edita videos/mi-video.mov para el colegio (TV)"
   - "Edita videos/mi-video.mov para TikTok"
   - "Estudia el estilo de referencias/ejemplo.mp4 y edita mi video igual"
   - "Haz los subtítulos más grandes y en verde"
5. Tu video queda en **salida/** (más la portada `_portada.jpg` y los subtítulos `.srt`).

## Si lo quieres correr tú mismo (sin Claude)
```
bash scripts/editar.sh videos/mi-video.mov --preset colegio-tv
bash scripts/editar.sh videos/mi-video.mov --preset tiktok
```
- `--calidad preview` = rápido y a media resolución, para ver cómo va. `--calidad maxima` = la mejor calidad (pesa más).
- `--formato tv | reel | cuadrado | retrato` = 16:9, 9:16, 1:1 o 4:5.
- `--subtitulos cine | tiktok | caja | resaltado` = estilo de subtítulos (`caja` es el más fácil de leer en proyector).
- Si se corta a la mitad (se cerró la ventana, se apagó el Mac): corre **el mismo comando** otra vez y sigue donde iba.
- Si algo falla, el mensaje dice **PROBLEMA** y **QUÉ HACER**.

## Qué hace solo
- Corta los silencios, las pausas y (si se lo pides) las muletillas y repeticiones.
- Subtítulos palabra por palabra, con la palabra que dices resaltada; máximo 2 líneas, nunca corta palabras.
- Zoom en los cortes que sigue tu cara, título/gancho, capítulos, escenas animadas, b-roll y tarjeta de cierre.
- Color automático, voz limpia, música original que baja sola cuando hablas, efectos de sonido.
- Todo a **60 fps** y con el volumen estándar de TikTok/YouTube (-14 LUFS), sin saturar.
- No repite trabajo: si el video es el mismo, no lo vuelve a transcribir.
- Aprende de tus correcciones (las guarda en `estilo.md`).

## Configuración
Todo está en **editor.config.json**: presets (`colegio-tv`, `tiktok`, `youtube`, `documental`), formatos con sus
zonas seguras (dónde no tapan los botones de TikTok ni recortan los televisores), calidades y volumen.
Lo más fácil es pedirle a Claude el cambio en español.
