---
name: palitos
description: Convierte una idea o pregunta en una caricatura explicativa animada con monitos de palitos (stick figures), con voz narrada, fondos, objetos, poses y globos de diálogo. Úsala cuando Pablo escriba /palitos o pida explicar algo "con monitos", "en caricatura" o "con stick figures".
---

# /palitos — caricatura con monitos de palitos

Receta: `{"tipo": "palitos", "fondo": "barco|salon|ciudad|campo|espacio|liso", "pasos": [...]}`. Cada paso:
`{"texto": "lo que se dice y se ve arriba", "personajes": [{"x": 0.45, "pose": "...", "accesorio": "...", "mira": "der|izq", "dice": "globo opcional"}], "objetos": [...], "fondo": "(opcional, cambia el fondo en ese paso)"}`
- Poses: parado, camina (avanza por la escena), corre, saluda, senala, sorprendido, pensando.
- Accesorios: pirata (sombrero y parche), corona, lentes, gorra, birrete (graduación), ninguno. `color` cambia el del accesorio.
- Objetos: barril, cofre, mesa, arbol, libro, casa, sol.
- 1–2 personajes por paso (x entre 0.3 y 0.7); varía las poses entre pasos para que se sienta vivo.

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
