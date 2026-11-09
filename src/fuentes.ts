// Fuentes guardadas en public/fuentes, así el render funciona sin internet.
// Para agregar otra fuente: pon el .woff2 en public/fuentes y añádela aquí.
import { loadFont } from "@remotion/fonts";
import { staticFile } from "remotion";
import { estilo } from "./estilo";

const archivos: Record<string, { archivo: string; peso: string }[]> = {
  Montserrat: [
    { archivo: "montserrat-latin-700-normal.woff2", peso: "700" },
    { archivo: "montserrat-latin-900-normal.woff2", peso: "900" },
  ],
  Poppins: [
    { archivo: "poppins-latin-700-normal.woff2", peso: "700" },
    { archivo: "poppins-latin-900-normal.woff2", peso: "900" },
  ],
  Anton: [{ archivo: "anton-latin-400-normal.woff2", peso: "400" }],
  Inter: [
    { archivo: "inter-latin-700-normal.woff2", peso: "700" },
    { archivo: "inter-latin-900-normal.woff2", peso: "900" },
  ],
};

// Se cargan la fuente de los subtítulos, Inter (escenas y look "cine") y Montserrat (subtítulos "resaltado").
const cargar = new Set([estilo.fuente, "Inter", "Montserrat"]);
for (const familia of cargar) {
  for (const f of archivos[familia] ?? []) {
    loadFont({ family: familia, url: staticFile(`fuentes/${f.archivo}`), weight: f.peso });
  }
}

export const fontFamily = `"${estilo.fuente}", sans-serif`;
export const fuenteEscenas = `"Inter", sans-serif`;
