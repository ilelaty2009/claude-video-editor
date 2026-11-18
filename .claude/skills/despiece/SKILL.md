---
name: despiece
description: Convierte un producto u objeto en una animación de "vista explotada" que lo separa en sus piezas con nombre y detalle, con voz narrada. Úsala cuando Pablo escriba /despiece, /breakdown o pida mostrar "por dentro", "las partes de" o "cómo está hecho" algo.
---

# /despiece — el producto se separa en sus piezas

Receta: `{"tipo": "despiece", "producto": "Teclado mecánico", "capas": [{"nombre": "Teclas", "detalle": "plástico PBT", "color": "#ECE7DD", "patron": "teclas|puntos|circuito|liso"}], "pasos": [{"texto": "..."}]}`
- 3–6 capas, de ARRIBA hacia ABAJO. Nombres de 1–2 palabras; `detalle` corto (material, función o medida real).
- El primer paso se ve armado y en el último ya están todas separadas (o pon `"capas": N` en un paso para controlarlo).
- Sirve para ciencias (capas de la Tierra, partes de la célula como capas, la atmósfera), tecnología y objetos.
- Detalles técnicos solo si son reales (búscalos si no los sabes).

## Cómo se hace (siempre igual)
1. Entiende la idea de Pablo y pregunta SOLO si falta algo indispensable (por ejemplo los números de una gráfica).
   Pregunta también el formato si no lo dijo: `tv` (16:9, para el colegio) o `reel` (9:16, TikTok).
2. Escribe la receta en `trabajo/animaciones/NOMBRE.json` (ejemplo completo en `demo/animaciones/`). Textos en español,
   cortos (una idea por paso, máximo ~12 palabras): cada paso dura lo que tarda la voz en decirlo.
3. Revisa antes de renderizar: `bash scripts/animar.sh trabajo/animaciones/NOMBRE.json --solo-preparar` y mira 2–3
   cuadros con `npx remotion still src/index.ts Animacion trabajo/x.png --frame=N --scale=0.4` (N = segundo × 60).
4. Renderiza: `bash scripts/animar.sh trabajo/animaciones/NOMBRE.json [--formato reel] [--calidad preview]`.
   Queda en `salida/NOMBRE_FORMATO.mp4` con voz narrada (Paulina; en inglés `"idioma": "en"` usa Samantha),
   música original (`"musica": "calma|lofi|energia|epica"` o `false`) y audio a -14 LUFS.
   Para usarla DENTRO de un video editado agrega `--broll` y ponla en una escena `broll` o `dividida` con
   `"archivo": "broll/NOMBRE_FORMATO.mp4"`.
5. Nunca inventes datos: números, fechas y hechos solo si Pablo los dio o los verificaste. Si es una teoría, dilo
   ("una teoría popular dice…").
