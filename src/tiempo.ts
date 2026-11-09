// TIEMPO Y MOVIMIENTO — base de todas las animaciones.
//
// Las animaciones se diseñaron contando cuadros a 30 fps ("entra en 7 cuadros", "la segunda línea 8 cuadros
// después"). El video ahora sale a 60 fps. Para que todo dure lo mismo EN SEGUNDOS pero se vea el doble de suave,
// las animaciones leen el tiempo en "cuadros de diseño" (siempre a 30 por segundo, con decimales):
//   a 60 fps, el cuadro real 15 es el cuadro de diseño 7.5.
// Los resortes (spring) de Remotion aceptan cuadros con decimales, así que el movimiento queda continuo.
import { Easing, interpolate, useCurrentFrame, useVideoConfig } from "remotion";

export const FPS_DISENO = 30;

/** Cuadro actual en cuadros de diseño (30 por segundo, con decimales). */
export const useCuadro = (): number => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return (frame * FPS_DISENO) / fps;
};

/** useVideoConfig() pero con fps y duración en cuadros de diseño. `fpsReal` es el del video (60). */
export const useConfigDiseno = () => {
  const c = useVideoConfig();
  const k = FPS_DISENO / c.fps;
  return { ...c, fps: FPS_DISENO, durationInFrames: c.durationInFrames * k, fpsReal: c.fps };
};

/** Pasa cuadros de diseño a cuadros reales del video (para <Sequence from / durationInFrames>). */
export const aReal = (cuadrosDiseno: number, fpsReal: number): number => Math.round((cuadrosDiseno * fpsReal) / FPS_DISENO);

export const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

// Curvas de movimiento (nada lineal): salir rápido y frenar suave al llegar, como un objeto real.
export const curvas = {
  entra: Easing.out(Easing.cubic), // aparece rápido y se acomoda
  sale: Easing.in(Easing.cubic), // arranca suave y se va rápido
  cambia: Easing.inOut(Easing.cubic), // de un estado a otro
  camara: Easing.inOut(Easing.sin), // movimientos lentos de cámara
};

/** 0→1 al entrar, durante `dur` cuadros de diseño, empezando en `desde`. */
export const entrada = (frame: number, dur = 8, desde = 0): number =>
  interpolate(frame, [desde, desde + dur], [0, 1], { ...clamp, easing: curvas.entra });

/** 1→0 al salir: termina justo en `total` (menos `adelanto`), dura `dur` cuadros de diseño. */
export const salida = (frame: number, total: number, dur = 7, adelanto = 0): number =>
  interpolate(frame, [total - adelanto - dur, total - adelanto], [1, 0], { ...clamp, easing: curvas.sale });

/** Salida escalonada: se van en el orden en que entraron; cada uno `paso` cuadros antes que el siguiente. */
export const salidaEscalonada = (frame: number, total: number, i: number, n: number, paso = 2, dur = 7): number =>
  salida(frame, total, dur, (n - 1 - i) * paso);
