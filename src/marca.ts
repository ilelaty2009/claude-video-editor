// HOJA DE MARCA (brand/marca.json): colores y fuentes de Pablo. Todo el editor los toma de aquí.
// Para cambiarla: edita brand/marca.json o pídele a Claude "pon mi marca con los colores de mi página web".
import marcaJson from "../brand/marca.json";
import lista from "./subtitulos/fuentes_lista.json";

export type Marca = {
  nombre: string;
  colores: { azul: string; amarillo: string; rojo: string; verde: string; fondo: string[] };
  fuentes: { escenas: string; subtitulos: string };
  subtitulos?: { colorActiva?: string };
};

export const marca = marcaJson as Marca;

/** Fuentes que hay en public/fuentes (las mide scripts/medir_fuentes.mjs). */
export const fuentesDisponibles = lista as Record<string, { archivo: string; peso: string }[]>;

/** La familia pedida si existe en public/fuentes; si no, la de respaldo (nunca se rompe el render). */
export const familiaSegura = (pedida: string, respaldo: string) => (fuentesDisponibles[pedida] ? pedida : respaldo);
