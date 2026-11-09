// DISPOSICIÓN DE SUBTÍTULOS (sin navegador: se puede probar con `npm test`).
//
// Reglas de un subtitulador profesional:
//  - Máximo 2 líneas a la vez (o 1, según el estilo). Nunca se corta una palabra.
//  - El ancho se calcula con el tamaño REAL de cada letra de la fuente (src/subtitulos/metricas.json,
//    medido con scripts/medir_fuentes.mjs), no "a ojo" por número de palabras.
//  - Se cambia de "página" al terminar una frase, en una pausa, o si ya no cabe.
//  - Si son 2 líneas, se equilibran (que no quede una línea larga y otra con una sola palabra).
//  - Si UNA palabra sola no cabe (muy larga), esa página se achica un poco en vez de cortarla.
import metricas from "./metricas.json";

export type PalabraBase = { text: string; startMs: number; endMs: number; destacada?: boolean };

export type Pagina = {
  inicio: number; // índice de la primera palabra
  fin: number; // índice después de la última
  lineas: number[][]; // índices de palabras por línea
  anchos: number[]; // ancho de cada línea en px (a escala 1)
  escala: number; // 1 = normal; < 1 si una palabra no cabía
  startMs: number;
  endMs: number;
};

export type OpcionesDisposicion = {
  anchoMax: number; // px disponibles (ancho de la zona segura menos márgenes)
  tam: number; // tamaño de letra en px
  fuente: string; // clave de metricas.json, ej. "Inter-900"
  mayusculas: boolean;
  espaciado?: number; // letter-spacing en px
  separacion: number; // espacio entre palabras en px
  extraPorPalabra?: number; // relleno + borde de cada palabra en px
  maxLineas: number;
  maxPalabras: number;
  escalaDestacada?: number; // las destacadas son más grandes (ej. 1.3)
  pausaMs?: number; // una pausa más larga que esto cierra la página
};

type Metricas = Record<string, { anchos: Record<string, number>; porDefecto: number }>;
const M = metricas as Metricas;

/** Ancho en px de un texto en una fuente (sin kerning; con 3 % de margen de seguridad). */
export const anchoTexto = (texto: string, fuente: string, tam: number, espaciado = 0): number => {
  const m = M[fuente];
  const porDefecto = m?.porDefecto ?? 0.8;
  let em = 0;
  let n = 0;
  for (const c of texto) {
    n++;
    const a = m?.anchos[c];
    // emojis y símbolos que la fuente no tiene: se dibujan con otra fuente, más o menos cuadrados
    em += a !== undefined ? a : (c.codePointAt(0) ?? 0) > 0x2000 ? 1.2 : porDefecto;
  }
  return em * tam * 1.03 + espaciado * Math.max(0, n - 1);
};

export const textoVisible = (t: string, mayusculas: boolean): string => {
  const limpio = t.trim();
  return mayusculas ? limpio.toLocaleUpperCase("es") : limpio;
};

const finDeFrase = (t: string) => /[.?!…]["”»)]?$/.test(t.trim());

/** Agrupa las palabras en páginas que caben en `maxLineas` líneas de `anchoMax` px. */
export const paginar = (palabras: PalabraBase[], o: OpcionesDisposicion): Pagina[] => {
  const pausa = o.pausaMs ?? 350;
  const extra = o.extraPorPalabra ?? 0;
  const ancho = (i: number) => {
    const p = palabras[i];
    const tam = o.tam * (p.destacada ? o.escalaDestacada ?? 1 : 1);
    return anchoTexto(textoVisible(p.text, o.mayusculas), o.fuente, tam, o.espaciado) + extra;
  };

  // 1) cortes de página "naturales" + por capacidad (llenado de líneas, sin equilibrar todavía)
  const grupos: number[][] = [];
  let actual: number[] = [];
  let lineas = 1;
  let anchoLinea = 0;
  const cerrar = () => {
    if (actual.length) grupos.push(actual);
    actual = [];
    lineas = 1;
    anchoLinea = 0;
  };
  palabras.forEach((p, i) => {
    const w = ancho(i);
    const ant = palabras[i - 1];
    if (actual.length && (actual.length >= o.maxPalabras || (ant && p.startMs - ant.endMs > pausa))) cerrar();
    if (actual.length) {
      if (anchoLinea + o.separacion + w <= o.anchoMax) {
        anchoLinea += o.separacion + w;
      } else if (lineas < o.maxLineas) {
        lineas++;
        anchoLinea = w;
      } else {
        cerrar();
        anchoLinea = w;
      }
    } else {
      anchoLinea = w;
    }
    actual.push(i);
    const sig = palabras[i + 1];
    if (finDeFrase(p.text) || (p.destacada && !(sig && sig.destacada))) cerrar();
  });
  cerrar();

  // 2) repartir cada página en líneas equilibradas
  const paginas: Pagina[] = grupos.map((g) => {
    const ws = g.map(ancho);
    const total = (a: number, b: number) => ws.slice(a, b).reduce((s, x) => s + x, 0) + o.separacion * Math.max(0, b - a - 1);
    let mejor: { lineas: number[][]; anchos: number[] } = { lineas: [g], anchos: [total(0, g.length)] };
    if (mejor.anchos[0] > o.anchoMax && o.maxLineas >= 2 && g.length >= 2) {
      let peor = Infinity;
      for (let k = 1; k < g.length; k++) {
        const a = total(0, k);
        const b = total(k, g.length);
        // preferimos la primera línea igual o un poco más corta (forma de pirámide invertida suave)
        const costo = Math.max(a, b) + (a > b ? 1 : 0);
        if (costo < peor) {
          peor = costo;
          mejor = { lineas: [g.slice(0, k), g.slice(k)], anchos: [a, b] };
        }
      }
    }
    const masAncha = Math.max(...mejor.anchos);
    return {
      inicio: g[0],
      fin: g[g.length - 1] + 1,
      lineas: mejor.lineas,
      anchos: mejor.anchos,
      escala: masAncha > o.anchoMax ? o.anchoMax / masAncha : 1,
      startMs: palabras[g[0]].startMs,
      endMs: palabras[g[g.length - 1]].endMs,
    };
  });

  // 3) cada página se queda hasta que empieza la siguiente (máx. 0.6 s extra; la última 0.4 s)
  for (let i = 0; i < paginas.length; i++) {
    const sig = paginas[i + 1];
    paginas[i].endMs = sig ? Math.min(sig.startMs, paginas[i].endMs + 600) : paginas[i].endMs + 400;
  }
  return paginas;
};

/** Contraste WCAG entre dos colores "#RRGGBB" (1 = igual, 21 = blanco sobre negro). */
export const contraste = (a: string, b: string): number => {
  const lum = (hex: string) => {
    const n = parseInt(hex.replace("#", "").slice(0, 6), 16);
    const canal = (v: number) => {
      const s = v / 255;
      return s <= 0.03928 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4;
    };
    return 0.2126 * canal((n >> 16) & 255) + 0.7152 * canal((n >> 8) & 255) + 0.0722 * canal(n & 255);
  };
  const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p);
  return (x + 0.05) / (y + 0.05);
};
