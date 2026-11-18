# Auditoría del editor (estado original, commit `7c70455` en `main`)

Fecha: 2026-11-09. Todo lo que dice "medido" salió de correr el editor de verdad; lo demás es lectura del código.

## Qué hace
Pablo pone un video en `videos/` y Claude Code lo edita siguiendo `CLAUDE.md`:
1. `scripts/seguir_cara.py` busca la cara principal (detector UltraFace ONNX, MIT).
2. `scripts/color_auto.py` mide el color y arma un filtro de ffmpeg (balance de blancos + exposición + look).
3. `scripts/editar.sh` prepara `public/input.mp4` con ffmpeg (formato TV o reel, 30 fps) y limpia la voz
   (highpass, reducción de ruido, compresor, EQ, loudnorm a -14 LUFS).
4. `scripts/transcribe.py` transcribe con faster-whisper (palabra por palabra).
5. `scripts/plan_edit.py` corta silencios, aplica correcciones/destacadas/escenas/capítulos, estilo (clase,
   tiktok, youtube, documental), ritmo automático y escribe `public/edit.json`. `scripts/sonidos.py` coloca
   los efectos al cuadro exacto. `scripts/musica.py` compone música original.
6. Remotion (`src/`) renderiza: video recortado, zooms, subtítulos (look tiktok o cine), 13 tipos de escenas
   animadas, título, capítulos, cierre, efectos y música con ducking.
7. Limitador final, portada (`scripts/portada.py` + composición `Portada`), control de calidad y `.srt`.

## Estructura
```
CLAUDE.md, LEEME.md, estilo.md   reglas del editor y memoria de estilo (lo que Pablo corrigió)
instalar.command                 instalador de doble clic (Node portátil, .venv con Whisper e imageio-ffmpeg)
scripts/  (14 archivos, ~2.000 líneas)  bash + Python 3.9 + numpy
src/      (10 archivos, ~1.900 líneas)  Remotion 4.0.537 + React 19; Escenas.tsx tiene 1.032 líneas
public/   fuentes .woff2, efectos .wav sintetizados, b-roll de prueba
.claude/skills/  skills de Remotion (~300 archivos, de remotion-dev/skills)
```

## Dependencias
- Node 22 portátil (`.tools/node`), Remotion 4.0.537, React 19, TypeScript 5.
- Python 3.9 de Apple en `.venv`: faster-whisper 1.2.1, numpy, onnxruntime, imageio-ffmpeg.
- ffmpeg: el de `.venv/bin` y además hay `ffmpeg`/`ffprobe` de Homebrew en `/opt/homebrew/bin`
  (CLAUDE.md dice que no hay ffprobe; en este Mac sí hay, pero no se puede contar con él en otro Mac).

## Medición real (clip de 25 s de un video real de Pablo, `--formato tv --estilo clase`)
| Medida | Resultado |
|---|---|
| Tiempo total (caras + color + preparar + transcribir + render + portada + QC) | **96 s** para 18,6 s de video |
| Cuadros por segundo | **30 fps** (pedido: 60) |
| Resolución | 1920x1080, H.264 High nivel 4.0, yuv420p, ~4,3 Mb/s |
| Audio | AAC 48 kHz 192 kb/s, **-14,6 LUFS**, pico real **-1,4 dBTP** (cumple por poco; el -14 se ajusta solo a la voz, la mezcla final no se vuelve a normalizar) |
| Duración | 18,6 s = la del plan (el control de calidad lo verificó) |
| Subtítulos look cine | 46 px en 1080 de alto = **4,3 % del alto**: pequeños para leer desde el fondo de un salón |
| Control de calidad | "TODO BIEN" |

Lo que se vio en los fotogramas: el render funciona, las escenas se ven bien, pero los subtítulos de clase son chicos y
la palabra activa roja pierde contraste sobre fondos claros (se salva por la sombra).

## Qué funciona bien (no se toca sin razón medible)
- Cortes de silencio, correcciones, destacadas, gancho, capítulos, escenas, b-roll, cierre, portada, `.srt`.
- Detección de cara, color automático, música original, efectos alineados por su golpe.
- Mensajes en español y "planes B" cuando algo falla (sigue sin color, sin música…).

## Qué está roto o es frágil
1. **Todo a 30 fps.** `fps=30` está fijo en ffmpeg, en `plan_edit.py` y en ~70 animaciones que cuentan cuadros
   (`[0, 7]`, `4 + i * 8`…). Subir a 60 fps así nomás haría todas las animaciones el doble de rápidas.
   `sonidos.py` repite esos mismos números de cuadros: los efectos quedarían desfasados.
2. **Solo 2 formatos** (tv y reel). No hay 1:1 ni 4:5. Las posiciones de subtítulos/capítulos son números sueltos
   por formato (`top: 230`, `0.725`…), sin zonas seguras.
3. **Subtítulos sin control de largo**: se agrupan por número de palabras (3–5), no por ancho real. Una frase con
   palabras largas puede pasar a 3 líneas; no hay un máximo de 2 líneas garantizado.
4. **Volumen final no garantizado**: la voz se normaliza antes de agregar música y efectos; luego un limitador por
   muestra (`alimiter`, no mide el pico real) hace de techo. Hoy dio -14,6 LUFS / -1,4 dBTP, pero con música más
   fuerte o muchos efectos puede salir de rango sin que nada lo corrija.
5. **Sin caché real**: `--reusar` es manual y solo cubre la transcripción; caras, color y preparación se rehacen
   siempre. Si cambia el video pero tiene el mismo nombre, `--reusar` usa una transcripción vieja equivocada.
6. **Un render interrumpido se pierde entero**: no hay forma de reanudar.
7. **Exportación con valores por defecto**: no hay modo preview rápido ni modo máxima calidad; nivel H.264 4.0
   (1080p60 necesita 4.2); sin `faststart` garantizado en todos los caminos.
8. **Configuración repartida** en `editar.sh`, `plan_edit.py` (ESTILOS), `src/estilo.ts` y CLAUDE.md.
9. **Sin pruebas automáticas** ni chequeo de tipos en el flujo.
10. **No está listo para GitHub**: sin README para otros, sin LICENSE, `package.json` con scripts que no se usan
    (`render` escribe un archivo con nombre fijo), skills de terceros sin licencia visible dentro del repo.

## Deuda técnica
- `Escenas.tsx` de 1.032 líneas con 13 escenas, transiciones y lógica de cámara juntas.
- Lógica duplicada: leer ancho/alto con regex de `ffmpeg -i` está en `info_video.py`, `plan_edit.py` y `portada.py`.
- `plan_edit.py` mezcla imports en medio del archivo (`import re` después de constantes, `import subprocess` dentro de una función).
- Interpolaciones lineales en salidas (fundidos de títulos, subtítulos cine, escenas): se notan "mecánicas".
- `revisar.sh` asume 30 fps al imprimir los segundos.
- `EscenaBroll` usa `startFrom` (nombre viejo de Remotion; hoy es `trimBefore`).

## Los 10 problemas más grandes, por impacto
1. 30 fps fijo y animaciones atadas a cuadros (bloquea el pedido de 60 fps).
2. Volumen final no se mide ni se corrige sobre la mezcla final (riesgo de quedar bajo o de saturar).
3. Subtítulos pequeños en clase (4,3 % del alto) y sin límite real de 2 líneas.
4. Sin modo preview: probar algo cuesta un render completo (96 s para 18 s de video).
5. Sin caché por contenido: se repite trabajo y `--reusar` puede usar datos de otro video.
6. Renders interrumpidos no se pueden reanudar.
7. Solo 2 formatos y posiciones sin zonas seguras.
8. Configuración repartida en 4 lugares.
9. Cero pruebas automáticas.
10. Repo no publicable todavía (README, LICENSE, licencias de terceros, revisión de datos personales).
