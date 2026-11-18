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

// ---------- PANTALLA DIVIDIDA ----------
export type Rect = { x: number; y: number; w: number; h: number };
export type ModoDividida = "apilada" | "lado" | "pip";

/** Dónde va el contenido (panel) y dónde la persona en cada modo, en píxeles. */
export const rectsDividida = (modo: ModoDividida, W: number, H: number, lado: "izq" | "der" = "izq") => {
  if (modo === "pip") {
    const d = Math.round(Math.min(W, H) * (W > H ? 0.3 : 0.34)); // círculo con la cara
    const m = Math.round(W * 0.07); // dentro del margen seguro (TV: 5 %, vertical: 6 %)
    return {
      panel: { x: 0, y: 0, w: W, h: H },
      // ARRIBA a un lado: abajo van los subtítulos (y en vertical, la descripción de la app)
      persona: { x: lado === "izq" ? m : W - d - m, y: Math.round(H * (W > H ? 0.08 : 0.13)), w: d, h: d },
    };
  }
  if (modo === "lado") {
    const wp = Math.round(W * 0.58);
    const panel = { x: lado === "der" ? W - wp : 0, y: 0, w: wp, h: H };
    return { panel, persona: { x: lado === "der" ? 0 : wp, y: 0, w: W - wp, h: H } };
  }
  const hp = Math.round(H / 2);
  return { panel: { x: 0, y: 0, w: W, h: hp }, persona: { x: 0, y: hp, w: W, h: H - hp } };
};

/** Cómo mover y escalar el cuadro completo para que la imagen de la cámara (área A) LLENE la región R con la cara
 *  (punto F, en píxeles del cuadro) lo más centrada posible, sin dejar bordes vacíos. Devuelve escala y corrimiento
 *  del cuadro completo relativo a la esquina de R. */
export const encuadrarEn = (R: Rect, A: Rect, F: { x: number; y: number }, extra = 1.05) => {
  const s = Math.max(R.w / A.w, R.h / A.h) * extra;
  const centrar = (r: number, f: number, a0: number, a: number) => {
    const ideal = r / 2 - f * s; // la cara en el centro de la región
    const max = -a0 * s; // el borde izquierdo/superior del área no puede entrar a la región
    const min = r - (a0 + a) * s; // ni el derecho/inferior
    return Math.min(max, Math.max(min, ideal));
  };
  return { escala: s, x: centrar(R.w, F.x, A.x, A.w), y: centrar(R.h, F.y, A.y, A.h) };
};

/** Estado de la pantalla dividida en este momento (frame y fps en cuadros de diseño): t = 0 nada, 1 dividida. */
export const estadoDividida = (frame: number, fps: number, escenas: Escena[]) => {
  for (const e of escenas) {
    if (e.tipo !== "dividida") continue;
    const a = ms2f(e.desdeMs, fps);
    const b = ms2f(e.hastaMs, fps);
    if (frame < a || frame > b) continue;
    const ent = spring({ frame: frame - a, fps, config: { damping: 18, stiffness: 120 } });
    const sal = interpolate(frame, [b - 10, b], [1, 0], { ...clamp, easing: curvas.cambia });
    return { t: Math.min(ent, sal), escena: e };
  }
  return { t: 0, escena: null as Escena | null };
};

const mezclar = (a: number, b: number, t: number) => a + (b - a) * t;
export const mezclarRect = (a: Rect, b: Rect, t: number): Rect => ({
  x: mezclar(a.x, b.x, t), y: mezclar(a.y, b.y, t), w: mezclar(a.w, b.w, t), h: mezclar(a.h, b.h, t),
});

// ---------- PERSONA RECORTADA ----------
/** Qué pedazos de la persona recortada hay que mostrar en cada segmento (cuadros relativos al segmento). */
export const tramosPersona = (
  seg: { trimBefore: number; durationInFrames: number; from: number },
  ventanas: { a: number; b: number }[],
  personas: { archivo: string; desde: number; hasta: number }[],
  fps: number,
) => {
  const fuera: { desde: number; hasta: number; archivo: string; trim: number }[] = [];
  for (const v of ventanas) {
    const s0 = Math.max(v.a, seg.from);
    const s1 = Math.min(v.b, seg.from + seg.durationInFrames);
    if (s1 <= s0) continue;
    const segundo = (seg.trimBefore + (s0 - seg.from)) / fps; // segundo del video preparado
    const p = personas.find((q) => segundo >= q.desde - 0.05 && segundo < q.hasta);
    if (!p) continue;
    fuera.push({ desde: s0 - seg.from, hasta: s1 - seg.from, archivo: p.archivo, trim: Math.max(0, Math.round((segundo - p.desde) * fps)) });
  }
  return fuera;
};

// ---------- GRABACIÓN DE PANTALLA ----------
/** Dónde mira la cámara en el segundo `seg` de una grabación de pantalla (recorrido de scripts/pantalla.py). */
export const camaraPantalla = (zooms: { t: number; x: number; y: number; z: number }[], seg: number, transicion = 0.8) => {
  if (!zooms.length) return { x: 0.5, y: 0.5, z: 1 };
  let i = 0;
  while (i + 1 < zooms.length && zooms[i + 1].t <= seg) i++;
  const a = i > 0 ? zooms[i - 1] : zooms[0];
  const b = zooms[i];
  const p = interpolate(seg, [b.t, b.t + transicion], [0, 1], { ...clamp, easing: curvas.cambia });
  return { x: a.x + (b.x - a.x) * p, y: a.y + (b.y - a.y) * p, z: a.z + (b.z - a.z) * p };
};
