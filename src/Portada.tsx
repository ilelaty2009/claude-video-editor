// PORTADA / MINIATURA (como las de YouTube): la mejor foto de la cara + texto gigante.
// La arma scripts/portada.py (escoge el fotograma) y se dibuja con:
//   npx remotion still src/index.ts Portada salida/X_portada.jpg
import React from "react";
import { AbsoluteFill, Img, staticFile, useVideoConfig } from "remotion";
import { fuenteEscenas } from "./fuentes";

export type PortadaData = {
  imagen: string; // dentro de public/
  ancho: number;
  alto: number;
  foco?: { x: number; y: number };
  arriba?: string;
  lineas: { texto: string; color?: string }[];
  lado?: "izq" | "der";
  etiqueta?: string; // cajita de color, p. ej. "HISTORIA" o "EP. 2"
};

export const portadaVacia: PortadaData = { imagen: "", ancho: 1280, alto: 720, lineas: [{ texto: "PORTADA" }] };

export const Portada: React.FC<{ data: PortadaData }> = ({ data }) => {
  const { width, height } = useVideoConfig();
  const vertical = height > width;
  const k = vertical ? width / 1080 : width / 1280;
  const lado = data.lado ?? ((data.foco?.x ?? 0.5) > 0.5 ? "izq" : "der"); // el texto va donde NO está la cara
  const largo = Math.max(1, ...data.lineas.map((l) => l.texto.length));
  const tam = Math.min(vertical ? 150 : 128, ((vertical ? 980 : 640) / (largo * 0.58))) * k;
  return (
    <AbsoluteFill style={{ background: "#0d1024" }}>
      {data.imagen ? (
        <Img
          src={staticFile(data.imagen)}
          style={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
            filter: "contrast(1.1) saturate(1.2) brightness(1.03)",
          }}
        />
      ) : null}
      {/* oscurece el lado del texto para que se lea */}
      <AbsoluteFill
        style={{
          background: vertical
            ? "linear-gradient(to bottom, rgba(5,7,16,0.9) 0%, rgba(5,7,16,0.5) 32%, transparent 55%)"
            : `linear-gradient(${lado === "izq" ? "to right" : "to left"}, rgba(5,7,16,0.9) 0%, rgba(5,7,16,0.55) 38%, transparent 62%)`,
        }}
      />
      <AbsoluteFill
        style={{
          justifyContent: vertical ? "flex-start" : "center",
          alignItems: vertical ? "center" : lado === "izq" ? "flex-start" : "flex-end",
          padding: vertical ? `${200 * k}px ${60 * k}px 0` : `0 ${56 * k}px`,
          fontFamily: fuenteEscenas,
          textAlign: vertical ? "center" : lado === "izq" ? "left" : "right",
        }}
      >
        {data.etiqueta ? (
          <div style={{ background: "#FF3B5C", color: "white", fontWeight: 900, fontSize: 30 * k, padding: `${6 * k}px ${16 * k}px`, borderRadius: 8 * k, marginBottom: 14 * k, transform: "rotate(-2deg)" }}>
            {data.etiqueta.toUpperCase()}
          </div>
        ) : null}
        {data.arriba ? (
          <div style={{ fontWeight: 800, fontSize: 36 * k, color: "rgba(255,255,255,0.92)", textTransform: "uppercase", marginBottom: 4 * k, textShadow: "0 3px 12px rgba(0,0,0,0.8)" }}>
            {data.arriba}
          </div>
        ) : null}
        {data.lineas.map((l, i) => (
          <div
            key={i}
            style={{
              fontWeight: 900,
              fontSize: tam,
              lineHeight: 0.95,
              letterSpacing: -2 * k,
              textTransform: "uppercase",
              color: l.color ?? "white",
              WebkitTextStroke: `${3 * k}px rgba(0,0,0,0.85)`,
              paintOrder: "stroke fill",
              textShadow: `0 ${8 * k}px ${24 * k}px rgba(0,0,0,0.7)`,
            }}
          >
            {l.texto}
          </div>
        ))}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
