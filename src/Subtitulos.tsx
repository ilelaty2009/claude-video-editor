// SUBTÍTULOS palabra por palabra (karaoke): la palabra que se está diciendo se resalta en el instante exacto.
// Cómo se reparten en líneas: src/subtitulos/disposicion.ts. Dónde van: src/subtitulos/ubicacion.ts.
// Estilos (tiktok, cine, caja, resaltado): src/subtitulos/estilos.ts.
import React, { useMemo } from "react";
import { AbsoluteFill, Easing, interpolate, Sequence, useVideoConfig } from "remotion";
import type { Caption } from "@remotion/captions";
import { clamp, useCuadro, useConfigDiseno } from "./tiempo";
import { Zona } from "./formatos";
import { claveFuente, EstiloSub, estilosSub, NombreEstiloSub } from "./subtitulos/estilos";
import { Pagina, paginar, textoVisible } from "./subtitulos/disposicion";
import { ALTO_LINEA, arribaBloque, Ubicacion, ubicar } from "./subtitulos/ubicacion";

// Una palabra del subtítulo. color/emoji/zoom vienen de "destacadas" en los extras.
export type Palabra = Caption & { color?: string; destacada?: boolean; emoji?: string; zoom?: boolean };

export const armarPaginas = (captions: Palabra[], e: EstiloSub, u: Ubicacion): Pagina[] =>
  paginar(captions, {
    anchoMax: u.anchoMax,
    tam: u.tam,
    fuente: claveFuente(e),
    mayusculas: e.mayusculas,
    separacion: u.separacion,
    extraPorPalabra: u.extraPorPalabra,
    maxLineas: e.maxLineas,
    maxPalabras: e.maxPalabras,
    escalaDestacada: e.escalaDestacada,
  });

const PaginaVista: React.FC<{ pagina: Pagina; palabras: Palabra[]; e: EstiloSub; u: Ubicacion }> = ({ pagina, palabras, e, u }) => {
  const frame = useCuadro();
  const { fps } = useConfigDiseno();
  const ahoraMs = pagina.startMs + (frame / fps) * 1000;
  const tam = u.tam * pagina.escala;

  // entrada de la página: pop con rebote (tiktok/resaltado) o fundido que sube (cine/caja)
  const t = interpolate(frame, [0, e.pop ? 5 : 4], [0, 1], { ...clamp, easing: e.pop ? Easing.out(Easing.back(2)) : Easing.out(Easing.cubic) });
  const escalaEntrada = e.pop ? interpolate(t, [0, 1], [0.86, 1]) : 1;
  const opacidad = e.pop ? 1 : 0.4 + 0.6 * t; // se ve desde el primer cuadro (karaoke en sincronía) y termina de aparecer suave
  const subir = e.pop ? 0 : (1 - t) * tam * 0.15;

  // la palabra activa = la última que ya empezó
  let activa = -1;
  for (let i = pagina.inicio; i < pagina.fin; i++) if (palabras[i].startMs <= ahoraMs) activa = i;

  const borde = e.borde ? tam * e.borde.grosorEm : 0;
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <div
        style={{
          position: "absolute",
          left: u.izquierda,
          width: u.ancho,
          top: u.y,
          transform: `translateY(${u.ancla === "abajo" ? "-100%" : "-50%"}) translateY(${subir}px) scale(${escalaEntrada})`,
          transformOrigin: "center bottom",
          display: "flex",
          justifyContent: "center",
          opacity: opacidad,
        }}
      >
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            padding: e.caja ? `${u.rellenoCaja * 0.7}px ${u.rellenoCaja}px` : 0,
            borderRadius: e.caja ? tam * e.caja.radioEm : 0,
            background: e.caja ? hexA(e.caja.color, e.caja.opacidad) : undefined,
            fontFamily: `"${e.familia}", sans-serif`,
            fontWeight: e.peso,
            fontSize: tam,
            lineHeight: ALTO_LINEA,
          }}
        >
          {pagina.lineas.map((linea, li) => (
            <div key={li} style={{ display: "flex", flexWrap: "nowrap", whiteSpace: "nowrap", columnGap: u.separacion * pagina.escala, alignItems: "center" }}>
              {linea.map((i) => {
                const p = palabras[i];
                const esActiva = i === activa;
                const futura = i > activa;
                const desde = ahoraMs - p.startMs;
                const pop = esActiva && e.pop ? interpolate(desde, [0, 110], [p.destacada ? 1.16 : 1.1, 1.03], { ...clamp, easing: Easing.out(Easing.cubic) }) : 1;
                const giro = p.destacada && esActiva && e.pop ? interpolate(desde, [0, 140], [-6, -2], { ...clamp, easing: Easing.out(Easing.cubic) }) : 0;
                const enPastilla = esActiva && e.pastilla;
                const color = enPastilla ? e.pastilla!.texto : esActiva ? p.color ?? e.colorActiva : p.color ?? e.colorTexto;
                return (
                  <span
                    key={i}
                    style={{
                      display: "inline-block",
                      padding: `0 ${tam * (p.destacada && e.pop ? 0.12 : 0.06) + (e.pastilla ? tam * 0.12 : 0)}px`,
                      fontSize: p.destacada ? tam * e.escalaDestacada : undefined,
                      color,
                      opacity: futura ? e.opacidadFuturas : 1,
                      background: enPastilla ? e.pastilla!.color : undefined,
                      borderRadius: e.pastilla ? tam * 0.18 : undefined,
                      WebkitTextStroke: borde && !enPastilla ? `${borde}px ${e.borde!.color}` : undefined,
                      paintOrder: "stroke fill",
                      transform: `scale(${pop}) rotate(${giro}deg)`,
                      textShadow: enPastilla ? "none" : p.destacada && e.pop ? `0 0 28px ${p.color ?? e.colorActiva}88, ${e.sombra}` : e.sombra,
                      boxShadow: enPastilla ? `0 ${tam * 0.08}px ${tam * 0.25}px rgba(0,0,0,0.35)` : undefined,
                    }}
                  >
                    {textoVisible(p.text, e.mayusculas)}
                  </span>
                );
              })}
            </div>
          ))}
        </div>
      </div>
    </AbsoluteFill>
  );
};

const hexA = (hex: string, a: number) => {
  const n = parseInt(hex.replace("#", ""), 16);
  return `rgba(${(n >> 16) & 255},${(n >> 8) & 255},${n & 255},${a})`;
};

export const Subtitulos: React.FC<{
  captions: Palabra[];
  estilo: NombreEstiloSub;
  zona?: Zona;
  encuadre?: string;
}> = ({ captions, estilo, zona, encuadre }) => {
  const { fps, width, height } = useVideoConfig();
  const e = estilosSub[estilo] ?? estilosSub.tiktok;
  const u = useMemo(() => ubicar(e, width, height, zona, encuadre), [e, width, height, zona, encuadre]);
  const paginas = useMemo(() => armarPaginas(captions, e, u), [captions, e, u]);
  return (
    <AbsoluteFill>
      {e.banda ? (
        // banda oscura suave detrás: se leen aunque el fondo sea una pared o una camisa blanca
        <AbsoluteFill
          style={{
            top: arribaBloque(u, 2) - u.tam * 1.2,
            background: "linear-gradient(to bottom, transparent 0%, rgba(0,0,0,0.38) 55%, rgba(0,0,0,0.5) 100%)",
          }}
        />
      ) : null}
      {paginas.map((p, i) => {
        const from = Math.round((p.startMs / 1000) * fps);
        const dur = Math.max(1, Math.round((p.endMs / 1000) * fps) - from);
        return (
          <Sequence key={i} from={from} durationInFrames={dur} layout="none">
            <PaginaVista pagina={p} palabras={captions} e={e} u={u} />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};

/** Dónde empieza (arriba) el bloque de subtítulos, como fracción del alto: ahí se ponen los emojis. */
export const useArribaSubtitulos = (estilo: NombreEstiloSub, zona?: Zona, encuadre?: string): number => {
  const { width, height } = useVideoConfig();
  const e = estilosSub[estilo] ?? estilosSub.tiktok;
  return arribaBloque(ubicar(e, width, height, zona, encuadre), 1) / height;
};
