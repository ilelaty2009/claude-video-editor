// Movimientos de cámara del video de fondo: miniatura (el video se encoge a un lado) y zoom lento.
// Recibe el tiempo en cuadros de diseño (ver src/tiempo.ts).
import { Easing, interpolate, spring } from "remotion";
import { clamp, curvas } from "../tiempo";
const ms2f = (ms: number, fps: number) => Math.round((ms / 1000) * fps);
import type { Escena } from "./tipos";

type Punto = { x: number; y: number };

// Cómo se mueve el video en este frame (miniatura y zoom).
export const estadoVideo = (frame: number, fps: number, escenas: Escena[], width: number, height: number) => {
  let escala = 1;
  let x = 0;
  let y = 0;
  let radio = 0;
  let mini = 0;
  for (const e of escenas) {
    const a = ms2f(e.desdeMs, fps);
    const b = ms2f(e.hastaMs, fps);
    if (frame < a || frame > b) continue;
    if (e.tipo === "miniatura") {
      const ent = spring({ frame: frame - a, fps, config: { damping: 16, stiffness: 140 } });
      const sal = interpolate(frame, [b - 9, b], [1, 0], { ...clamp, easing: Easing.inOut(Easing.cubic) });
      const t = Math.min(ent, sal);
      mini = Math.max(mini, t);
      const lado = e.lado ?? "der"; // texto a la derecha => video a la izquierda
      escala = interpolate(t, [0, 1], [1, 0.5]);
      x = interpolate(t, [0, 1], [0, (lado === "izq" ? 1 : -1) * width * 0.2]);
      y = interpolate(t, [0, 1], [0, -height * 0.03]);
      radio = interpolate(t, [0, 1], [0, 26]);
    } else if (e.tipo === "zoom") {
      const t = interpolate(frame, [a, b], [0, 1], { ...clamp, easing: Easing.inOut(Easing.sin) });
      const z = interpolate(t, [0, 1], [1.0, e.escala ?? 1.3]);
      const sal = interpolate(frame, [b - 8, b], [1, 0], { ...clamp, easing: curvas.cambia });
      escala = 1 + (z - 1) * sal;
      x = (0.5 - (e.x ?? 0.5)) * width * (escala - 1);
      y = (0.5 - (e.y ?? 0.4)) * height * (escala - 1);
    }
  }
  return { escala, x, y, radio, mini };
};

/** Dónde está la cara en este cuadro (seguimiento de cara); si no hay recorrido, el foco fijo. */
export const focoEn = (frame: number, data: { foco?: Punto; focoRuta?: (Punto & { f: number })[] }): { x: number; y: number } => {
  const fijo = data.foco ?? { x: 0.5, y: 0.45 };
  const r = data.focoRuta;
  if (!r || r.length < 2) return fijo;
  if (frame <= r[0].f) return r[0];
  if (frame >= r[r.length - 1].f) return r[r.length - 1];
  let lo = 0;
  let hi = r.length - 1;
  while (hi - lo > 1) {
    const m = (lo + hi) >> 1;
    if (r[m].f <= frame) lo = m;
    else hi = m;
  }
  const a = r[lo];
  const b = r[hi];
  const t = curvas.cambia((frame - a.f) / Math.max(1, b.f - a.f));
  return { x: a.x + (b.x - a.x) * t, y: a.y + (b.y - a.y) * t };
};
