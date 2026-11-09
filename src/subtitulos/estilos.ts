// ESTILOS DE SUBTÍTULOS intercambiables (en los extras: "subtitulos": "caja", o --subtitulos caja).
// Tamaños en px para un video de referencia: TV 1920x1080 (tamTV) o vertical/cuadrado de 1080 de ancho (tamVertical).
// Criterio de legibilidad para el salón: en TV la letra mide al menos 5,5 % del alto (≥ 60 px en 1080).
// Criterio de contraste: texto y palabra activa contra su borde o caja ≥ 4,5:1 (WCAG AA). Lo revisa `npm test`.
import { estilo } from "../estilo";

export type NombreEstiloSub = "tiktok" | "cine" | "caja" | "resaltado";

export type EstiloSub = {
  descripcion: string;
  familia: "Montserrat" | "Inter" | "Poppins" | "Anton";
  peso: 700 | 900;
  tamTV: number;
  tamVertical: number;
  mayusculas: boolean;
  maxLineas: number;
  maxPalabras: number;
  colorTexto: string;
  colorActiva: string;
  opacidadFuturas: number; // palabras que todavía no dice (1 = igual que las demás)
  borde?: { color: string; grosorEm: number }; // contorno de cada letra
  caja?: { color: string; opacidad: number; radioEm: number; rellenoEm: number }; // caja detrás del bloque
  pastilla?: { color: string; texto: string }; // la palabra activa va dentro de una pastilla de color
  sombra: string;
  pop: boolean; // la palabra activa crece un poquito
  escalaDestacada: number;
  banda?: boolean; // banda oscura suave en la parte de abajo
  centroVertical: number; // en formatos verticales, a qué altura va el centro del bloque (0-1)
};

export const estilosSub: Record<NombreEstiloSub, EstiloSub> = {
  // El de TikTok/Ibn Khaldun: grande, amarillo, borde negro grueso, emojis.
  tiktok: {
    descripcion: "Grande, mayúsculas, palabra actual en amarillo y borde negro (TikTok)",
    familia: estilo.fuente,
    peso: 900,
    tamTV: 74,
    tamVertical: estilo.tamanoSubtitulo,
    mayusculas: estilo.mayusculas,
    maxLineas: 2,
    maxPalabras: 4,
    colorTexto: estilo.colorTexto,
    colorActiva: estilo.colorPalabraActiva,
    opacidadFuturas: 1,
    borde: { color: estilo.colorBorde, grosorEm: estilo.grosorBorde / estilo.tamanoSubtitulo },
    sombra: "0 6px 18px rgba(0,0,0,0.45)",
    pop: estilo.animarPalabraActiva,
    escalaDestacada: 1.3,
    centroVertical: estilo.posicionVertical,
  },
  // El del TikTok de Mark Cuban: limpio, palabra actual en rojo, lo que viene tenue.
  cine: {
    descripcion: "Limpio, palabra actual en rojo y lo que viene tenue (look cine)",
    familia: "Inter",
    peso: 900,
    tamTV: 62,
    tamVertical: 60,
    mayusculas: true,
    maxLineas: 2,
    maxPalabras: 7,
    colorTexto: estilo.cine.colorTexto,
    colorActiva: estilo.cine.colorPalabraActiva,
    opacidadFuturas: estilo.cine.opacidadPalabrasQueVienen,
    borde: { color: "#000000", grosorEm: 0.07 },
    sombra: "0 3px 14px rgba(0,0,0,0.75), 0 1px 3px rgba(0,0,0,0.8)",
    pop: false,
    escalaDestacada: 1,
    banda: true,
    centroVertical: 0.7,
  },
  // Máxima lectura en proyector: caja negra detrás, letra normal (no todo en mayúsculas).
  caja: {
    descripcion: "Caja oscura detrás y palabra actual en amarillo (lo más legible en proyector)",
    familia: "Inter",
    peso: 700,
    tamTV: 64,
    tamVertical: 62,
    mayusculas: false,
    maxLineas: 2,
    maxPalabras: 9,
    colorTexto: "#FFFFFF",
    colorActiva: "#FFD400",
    opacidadFuturas: 1,
    caja: { color: "#000000", opacidad: 0.78, radioEm: 0.22, rellenoEm: 0.32 },
    sombra: "none",
    pop: false,
    escalaDestacada: 1,
    centroVertical: 0.7,
  },
  // Estilo "Hormozi/Submagic": la palabra actual dentro de una pastilla de color.
  resaltado: {
    descripcion: "Palabra actual dentro de una pastilla amarilla (estilo creadores)",
    familia: "Montserrat",
    peso: 900,
    tamTV: 72,
    tamVertical: 76,
    mayusculas: true,
    maxLineas: 2,
    maxPalabras: 4,
    colorTexto: "#FFFFFF",
    colorActiva: "#111111",
    opacidadFuturas: 1,
    borde: { color: "#000000", grosorEm: 0.11 },
    pastilla: { color: "#FFD400", texto: "#111111" },
    sombra: "0 6px 18px rgba(0,0,0,0.45)",
    pop: true,
    escalaDestacada: 1.15,
    centroVertical: 0.68,
  },
};

export const claveFuente = (e: EstiloSub) => `${e.familia}-${e.peso}`;
