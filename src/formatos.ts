// FORMATOS Y ZONAS SEGURAS — los mismos de editor.config.json (un solo lugar para los números).
// Zona segura = el rectángulo donde el texto no queda tapado: en TV/proyector, los bordes que algunos
// televisores recortan; en TikTok/Reels, los botones de la derecha, la descripción de abajo y la barra de arriba.
import config from "../editor.config.json";

export type NombreFormato = keyof typeof config.formatos;
export type Zona = { arriba: number; abajo: number; izquierda: number; derecha: number };
export type Rect = { x: number; y: number; ancho: number; alto: number };

export const formatos = config.formatos;

export const zonaPorDefecto = (ancho: number, alto: number): Zona =>
  ancho > alto ? config.formatos.tv.zonaSegura : config.formatos.reel.zonaSegura;

/** El rectángulo seguro en píxeles. */
export const rectSeguro = (ancho: number, alto: number, zona?: Zona): Rect => {
  const z = zona ?? zonaPorDefecto(ancho, alto);
  return {
    x: ancho * z.izquierda,
    y: alto * z.arriba,
    ancho: ancho * (1 - z.izquierda - z.derecha),
    alto: alto * (1 - z.arriba - z.abajo),
  };
};

/** Escala de diseño de textos: 1 = TV 1920x1080. Los formatos verticales/cuadrados usan el ancho de 1080. */
export const escalaTexto = (ancho: number, alto: number): number => (ancho > alto ? alto / 1080 : ancho / 1080);
