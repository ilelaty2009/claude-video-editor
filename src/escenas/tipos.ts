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
  | "broll"
  | "dividida"
  | "grafica"
  | "mapa"
  | "cta"
  | "fondo"
  | "pantalla"
  | "cinetica"
  | "diagrama"
  | "ventana"
  | "collage"
  | "anotacion"
  | "capa";
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
  entrada?: "suave" | "barrido" | "zoom" | "luz" | "glitch";
  // broll (fotos o videos de apoyo, en public/broll/)
  archivo?: string;
  efecto?: "acercar" | "alejar" | "paneo";
  credito?: string;
  desdeSeg?: number; // para videos: segundo del clip donde empieza
  completo?: boolean; // true = no recorta la foto (rellena los lados difuminados)
  auto?: boolean; // agregado solo por el ritmo automático
  idExtra?: number; // posición en los extras (para el storyboard)
  detras?: boolean; // true = va DETRÁS de la persona (títulos detrás de la cabeza); necesita el recorte de la persona
  color?: string; // fondo: color liso (si no hay archivo)
  zooms?: { t: number; x: number; y: number; z: number }[]; // pantalla: recorrido de cámara (scripts/pantalla.py)
  palabras?: { texto: string; enMs?: number }[]; // cinetica (las llena plan_edit.py con lo que se dice)
  destacar?: string[]; // cinetica: palabras de color
  nodos?: { icono: string; texto: string; enMs?: number }[]; // diagrama
  archivos?: string[]; // collage
  forma?: "circulo" | "flecha" | "subrayado" | "x"; // anotacion
  ancho?: number; // anotacion: tamaño (0-1)
  alto?: number;
  etiqueta2?: string; // ventana: texto de la barra de progreso
  sonido?: boolean; // false = esta escena sin efectos de sonido
  // dividida (pantalla dividida): contenido en un panel y la persona en el otro
  modo?: "apilada" | "lado" | "pip"; // apilada = arriba/abajo (vertical), lado = izquierda/derecha (TV), pip = cara en círculo
  // grafica
  grafica?: "linea" | "barras";
  valores?: number[];
  etiquetas?: string[];
  // mapa
  origen?: string;
  destino?: string;
  // cta (llamada a la acción)
  usuario?: string;
  palabra?: string; // la palabra que se escribe en el comentario
};
