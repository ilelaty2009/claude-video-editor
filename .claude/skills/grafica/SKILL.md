---
name: grafica
description: Convierte números en una gráfica animada que se construye sola, con un contador grande y voz narrada (línea o barras, fondo claro u oscuro). Úsala cuando Pablo escriba /grafica o /graph, o pida "una gráfica", "mostrar cómo creció" o comparar números.
---

# /grafica — tus números se vuelven una gráfica que se construye sola

Receta: `{"tipo": "grafica", "grafica": "linea|barras", "tema": "claro|oscuro", "etiqueta": "Seguidores", "valores": [88, 900, 99385], "etiquetas": ["Ene", "Feb", "Mar"], "prefijo": "$", "sufijo": " min", "decimales": 0, "pasos": [{"texto": "..."}]}`
- Los números tienen que ser de Pablo o de una fuente real que verificaste (dila en `etiqueta`, p. ej. "Población (DANE 2018)").
  Si son de ejemplo, pon "(ejemplo)" en `etiqueta`.
- `linea` para algo que cambia en el tiempo; `barras` para comparar cosas. El eje se redondea solo (80, 40, 0).

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
