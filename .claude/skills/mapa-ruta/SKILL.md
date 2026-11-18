---
name: mapa-ruta
description: Crea un mapa 3D con la ruta animada entre dos lugares (como una app de mapas), con tiempo, distancia y voz narrada. Úsala cuando Pablo escriba /mapa-ruta o pida mostrar "cómo llegar", "el camino de X a Y", un recorrido o un viaje.
---

# /mapa-ruta — mapa 3D con la ruta animada

Receta: `{"tipo": "mapa", "origen": "Casa", "destino": "Colegio", "tiempo": "12 min", "distancia": "3,1 km", "calles": ["Calle 80", "Carrera 15"], "pasos": [{"texto": "..."}]}`
- El mapa es ilustrado (manzanas, parques, árboles): no es el mapa real de la ciudad. Si Pablo necesita el mapa real,
  díselo y usa una captura suya como b-roll.
- Tiempo y distancia solo si Pablo los dio (o calcúlalos con él); no los inventes.
- La ruta se dibuja mientras se narra y la cámara la sigue; el destino aparece con un pin rojo al llegar.

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
