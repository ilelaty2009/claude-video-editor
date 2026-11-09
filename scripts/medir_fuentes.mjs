// Mide el ancho real de cada letra de las fuentes de public/fuentes (con fontkit) y lo guarda en
// src/subtitulos/metricas.json. Con eso los subtítulos saben cuánto mide una frase ANTES de dibujarla
// (para no pasarse de 2 líneas ni cortar palabras). Solo hay que correrlo si se agrega una fuente nueva:
//   node scripts/medir_fuentes.mjs
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import * as fontkit from "fontkit";

const raiz = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const carpeta = path.join(raiz, "public", "fuentes");
const letras =
  Array.from({ length: 95 }, (_, i) => String.fromCharCode(32 + i)).join("") +
  "ÁÉÍÓÚÑÜáéíóúñü¿¡«»“”‘’…–—°ºª€";
const salida = {};
for (const archivo of fs.readdirSync(carpeta).filter((a) => a.endsWith(".woff2")).sort()) {
  // montserrat-latin-900-normal.woff2 -> Montserrat-900
  const [nombre, , peso] = archivo.split("-");
  const clave = `${nombre[0].toUpperCase()}${nombre.slice(1)}-${peso}`;
  const fuente = fontkit.openSync(path.join(carpeta, archivo));
  const anchos = {};
  for (const c of letras) {
    const g = fuente.glyphForCodePoint(c.codePointAt(0));
    if (g && g.id !== 0) anchos[c] = Math.round((g.advanceWidth / fuente.unitsPerEm) * 1000) / 1000;
  }
  salida[clave] = { anchos, porDefecto: anchos["M"] ?? 0.8 };
}
const destino = path.join(raiz, "src", "subtitulos", "metricas.json");
fs.writeFileSync(destino, JSON.stringify(salida, null, 1) + "\n");
console.log(`OK: ${Object.keys(salida).length} fuentes medidas -> ${path.relative(raiz, destino)}`);
