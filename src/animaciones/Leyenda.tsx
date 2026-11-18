// Texto del paso (lo que se narra) abajo, en una caja oscura que se lee sobre cualquier fondo.
import React from "react";
import { interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { clamp, curvas } from "../tiempo";
import { fuenteEscenas } from "../fuentes";
import { AnimacionData, escalaDe, pasoActual } from "./comun";

export const Leyenda: React.FC<{ data: AnimacionData; claro?: boolean }> = ({ data, claro }) => {
  const frame = useCurrentFrame();
  const { width: W, height: H } = useVideoConfig();
  const k = escalaDe(W, H);
  const { p, local, dur } = pasoActual(data, frame);
  if (!p.texto) return null;
  const o = Math.min(
    interpolate(local, [0, 6], [0, 1], { ...clamp, easing: curvas.entra }),
    interpolate(local, [dur - 5, dur], [1, 0], { ...clamp, easing: curvas.sale }),
  );
  return (
    <div style={{ position: "absolute", left: W * 0.07, right: W * 0.07, bottom: H * (H > W ? 0.22 : 0.08), display: "flex", justifyContent: "center", opacity: o }}>
      <div
        style={{
          padding: `${12 * k}px ${24 * k}px`,
          borderRadius: 16 * k,
          background: claro ? "rgba(255,255,255,0.92)" : "rgba(0,0,0,0.72)",
          color: claro ? "#111" : "white",
          fontFamily: fuenteEscenas,
          fontWeight: 700,
          fontSize: 44 * k,
          lineHeight: 1.2,
          textAlign: "center",
          boxShadow: claro ? `0 ${6 * k}px ${20 * k}px rgba(0,0,0,0.12)` : undefined,
        }}
      >
        {p.texto}
      </div>
    </div>
  );
};
