---
name: minimalista
description: Explica una idea o frase con gráficos minimalistas animados (formas simples, puntos que se mueven, líneas blancas sobre negro), con voz narrada. Úsala cuando Pablo escriba /minimalista o pida algo "minimalista", "con formas simples" o "estilo motivacional".
---

# /minimalista — formas simples, puntos y animaciones limpias

Receta: `{"tipo": "minimal", "pasos": [{"texto": "...", "visual": "barras|linea|puntos|circulo|numero", "valores": [..], "numero": N}]}`
- `barras`: barras de contorno que crecen y un punto con estela que salta por sus cimas (progreso, crecimiento).
- `linea`: una línea que se dibuja subiendo (tendencias). `puntos`: cuadrícula donde se encienden `numero` puntos (cantidades, días).
- `circulo`: círculo que se dibuja con un punto girando y `numero` en el centro (ciclos, uno solo).
- `numero`: un número grande que cuenta hasta `numero`.
- Frases cortas que se lean como una idea seguida ("Cada paso parece pequeño" → "hasta que miras hacia atrás").

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
