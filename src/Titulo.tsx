import React from "react";
import { AbsoluteFill, Easing, interpolate } from "remotion";
import { salida, useConfigDiseno, useCuadro } from "./tiempo";
import { estilo } from "./estilo";
import { fontFamily } from "./fuentes";

// Gancho/título que aparece arriba al inicio del video.
export const Titulo: React.FC<{ texto: string; top?: number }> = ({ texto, top = 220 }) => {
  const frame = useCuadro();
  const { fps } = useConfigDiseno();
  const total = Math.round(estilo.duracionTituloSeg * fps);
  const entra = interpolate(frame, [0, 8], [0, 1], { extrapolateRight: "clamp", easing: Easing.out(Easing.back(1.6)) });
  const sale = salida(frame, total, 6);
  return (
    <AbsoluteFill style={{ alignItems: "center" }}>
      <div
        style={{
          marginTop: top,
          maxWidth: "86%",
          padding: "18px 30px",
          borderRadius: 18,
          backgroundColor: estilo.colorFondoTitulo,
          color: estilo.colorTextoTitulo,
          fontFamily,
          fontWeight: 900,
          fontSize: estilo.tamanoTitulo,
          textAlign: "center",
          lineHeight: 1.1,
          opacity: sale,
          transform: `scale(${entra}) rotate(-2deg)`,
          boxShadow: "0 12px 30px rgba(0,0,0,0.35)",
        }}
      >
        {texto}
      </div>
    </AbsoluteFill>
  );
};
