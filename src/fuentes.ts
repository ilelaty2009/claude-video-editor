// Fuentes guardadas en public/fuentes, así el render funciona sin internet.
// Para agregar una fuente de Google: .venv/bin/python scripts/fuente_google.py "Space Grotesk"
// (la baja, la mide y queda disponible; luego ponla en brand/marca.json).
import { loadFont } from "@remotion/fonts";
import { staticFile } from "remotion";
import { estilo } from "./estilo";
import { familiaSegura, fuentesDisponibles, marca } from "./marca";

const escenas = familiaSegura(marca.fuentes.escenas, "Inter");
// Se cargan: la de subtítulos, la de escenas (marca), Inter y Montserrat (las usan estilos fijos como "resaltado").
const cargar = new Set([estilo.fuente, escenas, "Inter", "Montserrat"]);
// Solo en el navegador (donde Remotion renderiza): en las pruebas (Node) no hay dónde cargar fuentes.
for (const familia of typeof document === "undefined" ? [] : cargar) {
  for (const f of fuentesDisponibles[familia] ?? []) {
    loadFont({ family: familia, url: staticFile(`fuentes/${f.archivo}`), weight: f.peso });
  }
}

export const fontFamily = `"${estilo.fuente}", sans-serif`;
export const fuenteEscenas = `"${escenas}", sans-serif`;
