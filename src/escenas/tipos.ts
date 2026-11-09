// Tipos de las escenas animadas (lo que se escribe en los extras -> "escenas").
export type Linea = { texto: string; color?: string; enMs?: number };
export type Tarjeta = { texto: string; tipo?: "si" | "no" | "neutro"; enMs?: number };
export type TipoEscena =
  | "titular"
  | "chat"
  | "miniatura"
  | "engranajes"
  | "tarjetas"
  | "iconos"
  | "zoom"
  | "nombre"
  | "cita"
  | "numero"
  | "lista"
  | "linea_tiempo"
  | "broll";
export type Item = { texto: string; detalle?: string; enMs?: number };
export type Escena = {
  tipo: TipoEscena;
  desdeMs: number;
  hastaMs: number;
  // titular (también lo usan miniatura, engranajes, iconos)
  arriba?: string;
  lineas?: Linea[];
  lado?: "izq" | "der" | "centro";
  vertical?: "arriba" | "centro" | "abajo";
  fondo?: boolean;
  // chat
  texto?: string;
  etiqueta?: string;
  // tarjetas
  titulo?: string;
  tarjetas?: Tarjeta[];
  // iconos
  centro?: string;
  iconos?: string[];
  robots?: number;
  // zoom
  escala?: number;
  x?: number;
  y?: number;
  // nombre / cita / numero / lista / linea_tiempo
  rol?: string;
  autor?: string;
  valor?: number;
  decimales?: number;
  prefijo?: string;
  sufijo?: string;
  items?: Item[];
  // transición de entrada para escenas de pantalla completa
  entrada?: "suave" | "barrido" | "zoom" | "luz";
  // broll (fotos o videos de apoyo, en public/broll/)
  archivo?: string;
  efecto?: "acercar" | "alejar" | "paneo";
  credito?: string;
  desdeSeg?: number; // para videos: segundo del clip donde empieza
  completo?: boolean; // true = no recorta la foto (rellena los lados difuminados)
  auto?: boolean; // agregado solo por el ritmo automático
  sonido?: boolean; // false = esta escena sin efectos de sonido
};
