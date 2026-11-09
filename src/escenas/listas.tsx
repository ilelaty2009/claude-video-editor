// Escenas de listas: lista con chulitos y línea de tiempo.
import React from "react";
import { AbsoluteFill, Easing, interpolate, spring } from "remotion";
import { clamp, salidaEscalonada, useConfigDiseno, useCuadro } from "../tiempo";
import { fuenteEscenas } from "../fuentes";
import { colores, Fondo, Icono, ms2f, useK } from "./base";
import type { Escena } from "./tipos";

// ---------- LISTA CON CHULITOS ----------
export const EscenaLista: React.FC<{ e: Escena }> = ({ e }) => {
  const frame = useCuadro();
  const { fps, durationInFrames } = useConfigDiseno();
  const k = useK();
  const items = e.items ?? [];
  const tit = spring({ frame, fps, config: { damping: 18 } });
  return (
    <Fondo entrada={e.entrada}>
      <AbsoluteFill style={{ justifyContent: "center", padding: `0 ${260 * k}px ${110 * k}px`, fontFamily: fuenteEscenas }}>
        {e.titulo ? (
          <div style={{ fontWeight: 900, fontSize: 88 * k, color: "white", textTransform: "uppercase", marginBottom: 44 * k, opacity: tit, letterSpacing: -1 }}>
            {e.titulo}
          </div>
        ) : null}
        {items.map((it, i) => {
          const inicio = it.enMs !== undefined ? ms2f(it.enMs - e.desdeMs, fps) : 8 + i * 12;
          const s = spring({ frame: frame - inicio, fps, config: { damping: 14, stiffness: 170 } });
          const check = spring({ frame: frame - inicio - 5, fps, config: { damping: 9, stiffness: 220 } });
          const fuera = salidaEscalonada(frame, durationInFrames, i, items.length, 2, 7);
          return (
            <div key={i} style={{ display: "flex", alignItems: "center", gap: 28 * k, marginBottom: 26 * k, opacity: Math.min(s, fuera), transform: `translateX(${((1 - s) * -50 + (1 - fuera) * 40) * k}px)` }}>
              <div style={{ transform: `scale(${check})` }}>
                <Icono tipo="si" tam={80 * k} />
              </div>
              <div>
                <div style={{ fontWeight: 800, fontSize: 74 * k, color: "white", lineHeight: 1.05 }}>{it.texto}</div>
                {it.detalle ? <div style={{ fontWeight: 600, fontSize: 30 * k, color: "rgba(255,255,255,0.6)", marginTop: 4 * k }}>{it.detalle}</div> : null}
              </div>
            </div>
          );
        })}
      </AbsoluteFill>
    </Fondo>
  );
};

// ---------- LÍNEA DE TIEMPO ----------
export const EscenaLineaTiempo: React.FC<{ e: Escena }> = ({ e }) => {
  const frame = useCuadro();
  const { fps, width } = useConfigDiseno();
  const k = useK();
  const items = e.items ?? [];
  const margen = 200 * k;
  const ancho = width - margen * 2;
  const linea = interpolate(frame, [2, 22], [0, 1], { ...clamp, easing: Easing.out(Easing.cubic) });
  const yLinea = 560 * k;
  return (
    <Fondo entrada={e.entrada}>
      {e.titulo ? (
        <div style={{ position: "absolute", top: 170 * k, width: "100%", textAlign: "center", fontFamily: fuenteEscenas, fontWeight: 900, fontSize: 66 * k, color: "white", textTransform: "uppercase" }}>
          {e.titulo}
        </div>
      ) : null}
      <div style={{ position: "absolute", left: margen, top: yLinea, width: ancho * linea, height: 6 * k, borderRadius: 4, background: "linear-gradient(90deg, #5CC8FF, #FFC94D)" }} />
      {items.map((it, i) => {
        const x = margen + (items.length === 1 ? ancho / 2 : (i / (items.length - 1)) * ancho);
        const inicio = it.enMs !== undefined ? ms2f(it.enMs - e.desdeMs, fps) : 12 + i * 12;
        const s = spring({ frame: frame - inicio, fps, config: { damping: 11, stiffness: 180 } });
        const arriba = i % 2 === 0;
        return (
          <div key={i} style={{ position: "absolute", left: x, top: yLinea + 3 * k, opacity: s }}>
            <div style={{ position: "absolute", left: -16 * k, top: -16 * k, width: 32 * k, height: 32 * k, borderRadius: 99, background: "#0d1024", border: `${6 * k}px solid ${colores.amarillo}`, transform: `scale(${s})` }} />
            <div
              style={{
                position: "absolute",
                left: -170 * k,
                width: 340 * k,
                textAlign: "center",
                top: arriba ? undefined : 40 * k,
                bottom: arriba ? 40 * k : undefined,
                transform: `translateY(${(1 - s) * (arriba ? 30 : -30) * k}px)`,
                fontFamily: fuenteEscenas,
              }}
            >
              <div style={{ fontWeight: 900, fontSize: 72 * k, color: colores.amarillo, lineHeight: 1 }}>{it.texto}</div>
              {it.detalle ? <div style={{ fontWeight: 700, fontSize: 36 * k, color: "white", marginTop: 8 * k, lineHeight: 1.15 }}>{it.detalle}</div> : null}
            </div>
          </div>
        );
      })}
    </Fondo>
  );
};
