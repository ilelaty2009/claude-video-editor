# Estilo de los videos de Pablo

Este archivo es la "memoria de estilo". Claude lo lee antes de editar y lo actualiza cada vez que Pablo corrige algo.
Los valores técnicos viven en `src/estilo.ts`; aquí van las reglas en palabras, con números concretos (nada de "dinámico" o "bonito").

## Formato
- Por defecto **TV**: horizontal 1920x1080, 60 fps, imagen completa (para presentar en clase). También 9:16, 1:1 y 4:5.
- Reel vertical 1080x1920 solo si Pablo lo pide. Siempre preguntar antes.
- Idioma principal: español (Colombia). A veces inglés para clases en inglés.

## Cortes
- Cortar pausas de más de 0.3 s.
- Margen: 0.08 s antes de hablar y 0.15 s después, para que no suene cortado.
- Zoom alterno en cada corte: 100% / 108%, con un empujón suave de 0.2 s al empezar el clip.
- Quitar muletillas solo si Pablo lo pide (eh, este, o sea, ¿sí?).

## Subtítulos
- Fuente Montserrat Black (900), MAYÚSCULAS, 78 px.
- Blanco con borde negro de 10 px y sombra suave.
- Palabra actual en amarillo #FFD400 con un "pop" pequeño.
- 3 palabras por bloque.
- Posición: 68% de la altura (encima de los botones de TikTok/IG).

## Efectos "pro" (desde el video de prueba de Ibn Khaldun)
- Palabras clave: 30% más grandes, de color, con emoji que rebota encima y zoom de golpe (1.12) en el video.
- Colores de destacadas: amarillo #FFD400, verde #39FF88, azul #4FD6FF, rosa #FF5FA2.
- Capítulos: etiqueta negra con borde amarillo que entra desde la izquierda, 2.8 s.
- Barra de progreso amarilla arriba. Flash blanco suave (22%) en cada corte.
- Color: contraste +7%, saturación +18%, viñeta suave en los bordes.
- Sonidos: "pop" en cada emoji, "whoosh" en título y capítulos (volumen bajo).
- Videos horizontales: "relleno" = video centrado (alto 880 px) sobre el mismo video difuminado.

## Título / gancho
- Recuadro amarillo #FFD400 con texto negro, arriba, los primeros 2.5 s, levemente inclinado.

## Correcciones de Pablo (Claude agrega aquí cada vez que Pablo pide un cambio)
- 2026-10-21: le encantó el estilo del video de Ibn Khaldun. Casi siempre necesita formato TV con la imagen completa para que los profes lo vean; preguntar el formato antes de editar, no pasar a reel solo.

## Look "cine" (escenas animadas)
- Subtítulos: Inter Black, MAYÚSCULAS, 62 px (en 1080 de alto = 5,7 %; antes 46 px = 4,3 %, chico para el fondo del salón),
  abajo dentro de la zona segura, hasta 2 líneas y 7 palabras, borde negro fino (7 % de la letra) para el contraste.
  Lo ya dicho en blanco, palabra actual en rojo #FF3B5C, lo que viene al 45% de opacidad. Sin borde, sombra suave.
- Fondo de escenas: azul noche degradado (#1d2447 → #07080f).
- Titulares: línea pequeña arriba (Inter Bold 40 px, blanco 88%) + líneas gigantes (Inter Black hasta 120 px), cada una entra con rebote cuando se dice.
- Colores: azul #5CC8FF, amarillo #FFC94D, rojo #FF3B5C; una palabra de color por escena.
- Entrada de escenas de pantalla completa: fundido + zoom 105%→100% en 7 cuadros; salida fundido en 6. Whoosh suave.
- Miniatura: el video se encoge al 50%, esquinas redondeadas, va al lado contrario del texto.
- Sin barra de progreso ni flash en los cortes.

## Mejoras "editor profesional" (2026-11-07, investigadas en GitHub: video-use, auto-editor, claude-code-video-toolkit, Submagic)
- Audio: highpass 80 Hz, reducción de ruido, compresor 3:1, +2 dB en 3.5 kHz, volumen final -14 LUFS (estándar de YouTube/TikTok).
  El video de Ibn Khaldun estaba en -31 LUFS: se oía muy bajito en el TV del salón.
- Quitar falsos comienzos y repeticiones (se queda la última versión de la frase).
- Zooms apuntando a la cara (`foco`), no al centro.
- Revisión de fotogramas antes del render completo (`revisar.sh`).
- Transiciones variadas: suave, barrido, zoom, luz.
- Música solo si Pablo la pone, y siempre con ducking (más baja cuando hablan).

## Ronda 3 (2026-11-08): métodos de editores pro (Premiere, DaVinci, Descript, MrBeast)
- Color automático con look (DaVinci Auto Color): balance de blancos "mundo gris" + exposición solo si está muy oscuro (<85) o quemado (>175).
  No bajar la exposición por una pared blanca: oscurece las caras.
- Caras: detector UltraFace (MIT). Cara principal = la que más aparece, cerca del centro, no cortada en el borde.
- Gancho al inicio (cold open) de 3–6 s con destello de luz.
- Ritmo: máximo 5 s sin cambio visual; si no, acercamiento lento automático (1.12x).
- Diseño de sonido por escena, todo sintetizado por nosotros (public/sfx): impacto, riser, ding, tecla, tick, brillo, whoosh_corto.
- B-roll con efecto Ken Burns (la foto nunca quieta) y crédito de licencia; fuente libre: Wikimedia Commons.
- Subtítulos cine con banda oscura suave detrás (se leen sobre paredes y camisas blancas); palabras que vienen al 62%.

## Ronda 4 (2026-11-08)
- Estilos de un solo nombre: clase, tiktok, youtube, documental (ver CLAUDE.md, paso 0).
- Música original compuesta por el editor (calma 72 bpm, lofi 80, energía 118, épica 88); graves < 40 Hz cortados para TV.
  En "clase" va muy bajita (0.12 / 0.035 cuando hablan).
- Tarjeta de cierre de 3 s con partículas y destello.
- Portada tipo YouTube: cara ~45% del alto a un lado, texto gigante con borde negro al otro; en vertical, texto arriba.
- Control de calidad final y subtítulos .srt automáticos.

## Ronda 5 (2026-11-08): sonido profesional (reel "Claude es horrible editando videos a menos que…")
- Las 3 herramientas del reel: Openverse (sonidos reales CC0), earshot (escuchar y escoger), Real SFX (al cuadro exacto).
- earshot de verdad pide Python 3.10+, PyTorch y 1.1 GB de modelos: hicimos `oido.py` (numpy, Python 3.9, sin descargas).
- Cada efecto se alinea por su GOLPE (pico), no por su inicio. Efectos 25 % más bajos cuando alguien habla.
- No amontonar: dos efectos a < 3 cuadros -> queda el más fuerte.
- Limitador final a -1 dB (masterización).

## Videos de referencia estudiados
- 2026-11-07 — TikTok "Raw footage vs Edited with Opus 5.5" (entrevista a Mark Cuban, 29 s, 16:9).
  Cada 3–5 s cambia algo: titular grande, chat que se escribe solo, documento + robots, tarjetas RIGHT/WRONG, miniatura con texto,
  engranajes girando. ~55% del tiempo hay una escena encima. Subtítulos de una línea con palabra actual en rojo. → look "cine".

## Ronda 6 (2026-11-09): nivel profesional (rama mejoras-pro)
- Todo a 60 fps. Las animaciones se miden en tiempo (cuadros de diseño a 30), así duran lo mismo y se ven el doble de suaves.
- Formatos: tv 16:9, reel 9:16, cuadrado 1:1, retrato 4:5, con zonas seguras (TV: 5 % a los lados; TikTok: 12 % arriba,
  20 % abajo, 13 % a la derecha por los botones).
- Subtítulos: máximo 2 líneas medidas con el ancho real de la fuente, nunca se corta una palabra, líneas equilibradas.
  Estilos: cine, tiktok, caja (el más legible en proyector), resaltado. Letra mínima: 5,5 % del alto en TV.
- Salidas escalonadas (las líneas se van en el orden en que entraron) con curvas; nada lineal salvo barra de progreso,
  giro de engranajes y la escritura del chat (ritmo constante a propósito).
- Audio: la mezcla final (voz + música + efectos) se masteriza a -14 LUFS y pico real ≤ -1 dBTP medido en el archivo final.
  Voz: además de lo anterior, -1,5 dB en 250 Hz (menos "encierro") y de-esser suave (las "s" no silban).
- Zooms que siguen la cara si la persona se mueve (recorrido suavizado de la cara principal).

