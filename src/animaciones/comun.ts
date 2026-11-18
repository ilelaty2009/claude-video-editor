// ANIMACIONES EXPLICATIVAS (videos completos hechos desde cero, sin grabar nada): lo que comparten.
// Las arma scripts/animar.py desde una "receta" JSON (ver demo/animaciones/) y las dibuja src/animaciones/.
// Cada animación es una lista de PASOS: cada paso tiene un texto (lo que se narra/lee) y su tiempo.
import { FPS_DISENO } from "../tiempo";

export type TipoAnimacion = "minimal" | "palitos" | "despiece" | "mapa" | "grafica";

export type Personaje = {
  x: number; // 0-1 a lo ancho
  pose?: "parado" | "camina" | "saluda" | "senala" | "sorprendido" | "pensando" | "corre";
  accesorio?: "pirata" | "corona" | "lentes" | "gorra" | "birrete" | "ninguno";
  color?: string; // color del accesorio
  mira?: "izq" | "der";
  dice?: string; // globo de diálogo
};

export type Paso = {
  texto: string;
  desdeMs: number;
  hastaMs: number;
  // minimal
  visual?: "barras" | "puntos" | "circulo" | "linea" | "numero";
  valores?: number[];
  numero?: number;
  // palitos
  personajes?: Personaje[];
  objetos?: string[]; // barril, cofre, mesa, arbol, libro, tablero, sol, casa
  fondo?: string;
  // despiece: cuántas capas ya se separaron (si no, todas)
  capas?: number;
};

export type Capa = { nombre: string; detalle?: string; color?: string; patron?: "teclas" | "puntos" | "circuito" | "liso" };

export type AnimacionData = {
  tipo: TipoAnimacion;
  width: number;
  height: number;
  fps: number;
  durationInFrames: number;
  tema?: "claro" | "oscuro";
  titulo?: string;
  pasos: Paso[];
  fondo?: string; // palitos: barco, salon, ciudad, campo, espacio, liso
  producto?: string; // despiece
  capasDespiece?: Capa[];
  origen?: string; // mapa
  destino?: string;
  tiempo?: string;
  distancia?: string;
  calles?: string[];
  valores?: number[]; // grafica
  etiquetas?: string[];
  etiqueta?: string;
  prefijo?: string;
  sufijo?: string;
  decimales?: number;
  grafica?: "linea" | "barras";
};

/** Qué paso se está mostrando y cuánto lleva (en cuadros de diseño, a 30 por segundo). */
export const pasoActual = (data: AnimacionData, frameReal: number) => {
  const ms = (frameReal / data.fps) * 1000;
  let i = data.pasos.findIndex((p) => ms >= p.desdeMs && ms < p.hastaMs);
  if (i < 0) i = ms < (data.pasos[0]?.desdeMs ?? 0) ? 0 : data.pasos.length - 1;
  const p = data.pasos[i];
  const local = ((ms - p.desdeMs) / 1000) * FPS_DISENO;
  const dur = ((p.hastaMs - p.desdeMs) / 1000) * FPS_DISENO;
  return { i, p, local, dur, msTotal: ms };
};

/** Proyección isométrica (como los dibujos técnicos): x a la derecha-abajo, y a la izquierda-abajo, z hacia arriba. */
export const iso = (x: number, y: number, z: number, escala = 1) => ({
  x: (x - y) * Math.cos(Math.PI / 6) * escala,
  y: ((x + y) * Math.sin(Math.PI / 6) - z) * escala,
});

/** Número pseudoaleatorio repetible (mismo video siempre). */
export const azar = (n: number) => {
  const v = Math.sin(n * 127.1 + 311.7) * 43758.5453;
  return v - Math.floor(v);
};

export const escalaDe = (w: number, h: number) => (w > h ? h / 1080 : w / 1080);
