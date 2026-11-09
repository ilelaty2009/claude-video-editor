// DÓNDE VAN LOS SUBTÍTULOS en cada formato (sin navegador: se prueba con `npm test`).
// Siempre dentro de la zona segura del formato (ver editor.config.json -> formatos -> zonaSegura).
import { escalaTexto, rectSeguro, Zona } from "../formatos";
import { EstiloSub } from "./estilos";

export const ALTO_LINEA = 1.18;

export type Ubicacion = {
  tam: number; // tamaño de letra en px
  izquierda: number; // borde izquierdo del área de subtítulos (px)
  ancho: number; // ancho del área (px)
  anchoMax: number; // ancho máximo de una línea de texto (px)
  y: number; // ancla vertical (px)
  ancla: "abajo" | "centro"; // "abajo" = el bloque termina en y; "centro" = el bloque se centra en y
  separacion: number; // espacio entre palabras (px)
  extraPorPalabra: number; // relleno + borde que agrega cada palabra (px)
  rellenoCaja: number; // relleno interno de la caja (px), 0 si no hay caja
};

export const ubicar = (e: EstiloSub, ancho: number, alto: number, zona?: Zona, encuadre?: string): Ubicacion => {
  const k = escalaTexto(ancho, alto);
  const tam = (ancho > alto ? e.tamTV : e.tamVertical) * k;
  const r = rectSeguro(ancho, alto, zona);
  const rellenoCaja = e.caja ? tam * e.caja.rellenoEm : 0;
  const borde = e.borde ? tam * e.borde.grosorEm : 0;
  const extraPorPalabra = (e.pastilla ? tam * 0.36 : 0) + borde + tam * 0.12;
  const vertical = alto > ancho * 1.5; // 9:16: el bloque va un poco más arriba (encima de la descripción de TikTok)
  let y: number;
  let ancla: Ubicacion["ancla"];
  if (vertical) {
    ancla = "centro";
    y = alto * (encuadre === "relleno" ? 0.725 : e.centroVertical);
  } else {
    ancla = "abajo";
    y = r.y + r.alto;
  }
  return {
    tam,
    izquierda: r.x,
    ancho: r.ancho,
    anchoMax: r.ancho - 2 * rellenoCaja - 2 * borde,
    y,
    ancla,
    separacion: tam * 0.26,
    extraPorPalabra,
    rellenoCaja,
  };
};

/** Alto del bloque de subtítulos con n líneas (px). */
export const altoBloque = (u: Ubicacion, lineas: number, escala = 1): number =>
  lineas * u.tam * escala * ALTO_LINEA + 2 * u.rellenoCaja;

/** Borde de arriba del bloque (px), para poner encima los emojis. */
export const arribaBloque = (u: Ubicacion, lineas: number, escala = 1): number =>
  u.ancla === "abajo" ? u.y - altoBloque(u, lineas, escala) : u.y - altoBloque(u, lineas, escala) / 2;
