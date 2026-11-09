// ESTILO DEL VIDEO — Claude cambia estos valores según estilo.md.
// (Si quieres otro look, pídeselo a Claude en español; no hace falta tocar esto a mano.)

export const estilo = {
  // Subtítulos
  fuente: "Montserrat" as "Montserrat" | "Poppins" | "Anton" | "Inter",
  pesoFuente: 900,
  tamanoSubtitulo: 78, // px en un video de 1080 de ancho
  mayusculas: true,
  palabrasPorBloque: 3, // cuántas palabras se ven a la vez
  colorTexto: "#FFFFFF",
  colorPalabraActiva: "#FFD400", // la palabra que estás diciendo
  colorBorde: "#000000",
  grosorBorde: 10,
  posicionVertical: 0.68, // 0 = arriba, 1 = abajo (0.68 evita los botones de TikTok/IG)
  animarPalabraActiva: true, // pequeño "pop" en la palabra actual
  posicionVerticalTV: 0.84, // en formato TV (horizontal) los subtítulos van abajo
  palabrasPorBloqueTV: 4, // en TV caben más palabras por línea

  // Cortes y movimiento
  zoomEnCortes: true, // alterna zoom en cada corte para que no se note el salto
  zoomMaximo: 1.08,
  fundidoAudioFrames: 2, // evita "clicks" de audio en los cortes
  zoomGolpe: 1.12, // zoom rápido en las palabras destacadas (1 = sin zoom)

  // Color y ambiente
  filtroColor: "contrast(1.07) saturate(1.18) brightness(1.03)", // "" para dejar el color original
  vineta: true, // oscurece un poco los bordes (look cine)

  // Título/gancho arriba al inicio (se pone en edit.json -> "titulo")
  tamanoTitulo: 72,
  colorFondoTitulo: "#FFD400",
  colorTextoTitulo: "#000000",
  duracionTituloSeg: 2.5,

  // LOOK "CINE" (extras -> "look": "cine"): subtítulos limpios de una línea, como el TikTok de Mark Cuban.
  // Se usa junto con las escenas animadas de src/Escenas.tsx.
  cine: {
    tamanoSubtitulo: 46, // px en un video de 1920 de ancho
    palabrasPorBloque: 5,
    colorTexto: "#FFFFFF",
    colorPalabraActiva: "#FF3B5C", // rojo
    opacidadPalabrasQueVienen: 0.62, // las palabras que todavía no dice se ven tenues
    posicionVertical: 0.9,
    filtroColor: "contrast(1.06) saturate(1.05) brightness(1.0)",
  },
};
