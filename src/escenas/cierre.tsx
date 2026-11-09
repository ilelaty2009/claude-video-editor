// Tarjeta de cierre (después de que termina de hablar): título, raya animada, partículas y destello.
import React from "react";
import { AbsoluteFill, Easing, interpolate, spring } from "remotion";
import { clamp, useConfigDiseno, useCuadro } from "../tiempo";
import { fuenteEscenas } from "../fuentes";
import { colores, useK } from "./base";
import { DestelloLuz } from "./base";

// ---------- CIERRE (tarjeta final, después de que termina de hablar) ----------
export const Cierre: React.FC<{ titulo: string; subtitulo?: string; linea?: string; sfx: boolean }> = ({ titulo, subtitulo, linea, sfx }) => {
  const frame = useCuadro();
  const { fps } = useConfigDiseno();
  const k = useK();
  const entra = interpolate(frame, [0, 10], [0, 1], { ...clamp, easing: Easing.out(Easing.cubic) });
  const t = spring({ frame: frame - 6, fps, config: { damping: 14, stiffness: 140 } });
  const st = spring({ frame: frame - 14, fps, config: { damping: 18 } });
  const raya = interpolate(frame, [10, 30], [0, 1], { ...clamp, easing: Easing.out(Easing.cubic) });
  // partículas suaves que suben (dan vida a la pantalla final)
  const particulas = Array.from({ length: 18 }).map((_, i) => {
    const sem = (i * 9301 + 49297) % 233280 / 233280;
    const x = ((i * 0.618) % 1) * 100;
    const y = 100 - (((frame / fps) * (6 + sem * 10) + sem * 100) % 110);
    return { x, y, r: 2 + sem * 4, o: 0.15 + sem * 0.35 };
  });
  return (
    <AbsoluteFill style={{ opacity: entra }}>
      <AbsoluteFill style={{ background: colores.fondo }} />
      {particulas.map((p, i) => (
        <div key={i} style={{ position: "absolute", left: `${p.x}%`, top: `${p.y}%`, width: p.r * k, height: p.r * k, borderRadius: 99, background: colores.amarillo, opacity: p.o, filter: "blur(1px)" }} />
      ))}
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", fontFamily: fuenteEscenas, textAlign: "center", padding: `0 ${120 * k}px` }}>
        <div style={{ fontWeight: 900, fontSize: Math.min(150, 2200 / Math.max(6, titulo.length)) * k, color: "white", letterSpacing: -3 * k, lineHeight: 1, transform: `scale(${interpolate(t, [0, 1], [0.85, 1])})`, opacity: t, textShadow: "0 10px 40px rgba(0,0,0,0.5)" }}>
          {titulo}
        </div>
        <div style={{ width: 260 * k * raya, height: 6 * k, borderRadius: 4, margin: `${26 * k}px 0`, background: "linear-gradient(90deg, #5CC8FF, #FFC94D)" }} />
        {subtitulo ? (
          <div style={{ fontWeight: 800, fontSize: 48 * k, color: colores.amarillo, opacity: st, transform: `translateY(${(1 - st) * 20 * k}px)`, textTransform: "uppercase", letterSpacing: 2 }}>
            {subtitulo}
          </div>
        ) : null}
        {linea ? (
          <div style={{ fontWeight: 600, fontSize: 32 * k, color: "rgba(255,255,255,0.7)", marginTop: 14 * k, opacity: st }}>{linea}</div>
        ) : null}
      </AbsoluteFill>
      <DestelloLuz duracion={24} />
    </AbsoluteFill>
  );
};
