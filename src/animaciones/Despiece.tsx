// /despiece — un producto que se separa en sus piezas ("vista explotada"), cada una con su nombre y detalle.
// Dibujado en isométrico (como los planos técnicos): capas que se levantan una por una y etiquetas numeradas.
import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { clamp, curvas, FPS_DISENO } from "../tiempo";
import { fuenteEscenas } from "../fuentes";
import { AnimacionData, Capa, escalaDe, iso } from "./comun";
import { Leyenda } from "./Leyenda";

const oscurecer = (hex: string, f: number) => {
  const n = parseInt(hex.replace("#", ""), 16);
  const c = (v: number) => Math.round(v * f);
  return `rgb(${c((n >> 16) & 255)},${c((n >> 8) & 255)},${c(n & 255)})`;
};
const COLORES = ["#ECE7DD", "#B9BDC6", "#8A8F99", "#2E8B57", "#E9DFC4", "#5A5F6B"];

export const Despiece: React.FC<{ data: AnimacionData }> = ({ data }) => {
  const frame = useCurrentFrame();
  const { width: W, height: H, fps } = useVideoConfig();
  const k = escalaDe(W, H);
  const t = (frame * FPS_DISENO) / fps;
  const capas: Capa[] = data.capasDespiece?.length ? data.capasDespiece : [{ nombre: "Pieza" }];
  const n = capas.length;
  const vertical = H > W;
  const esc = Math.min(W, H) * (vertical ? 0.00145 : 0.0017);
  const A = 300; // ancho de cada capa (unidades del dibujo)
  const B = 120; // fondo
  const grosor = 16;
  const hueco = 70;
  const centro = { x: W * (vertical ? 0.36 : 0.36), y: H * (vertical ? 0.44 : 0.5) };
  // cuántas capas están separadas en cada paso: el campo "capas" del paso o, si no, repartido
  // (el 1.er paso se ve armado y en el último ya están todas separadas)
  const objetivoDe = (j: number) => data.pasos[j].capas ?? Math.round((j / Math.max(1, data.pasos.length - 1)) * n);
  const separacion = (i: number) => {
    // en qué paso le toca a esta capa: se anima DESDE ese momento (escalonada con las otras del mismo paso)
    const j = data.pasos.findIndex((_, x) => objetivoDe(x) > i);
    if (j < 0) return 0;
    const antes = j > 0 ? objetivoDe(j - 1) : 0;
    const inicio = (data.pasos[j].desdeMs / 1000) * FPS_DISENO + 8 + (i - antes) * 7;
    return spring({ frame: t - inicio, fps: FPS_DISENO, config: { damping: 16, stiffness: 80 } });
  };
  const flota = Math.sin(t / 25) * 4;
  const zDe = (i: number) => (n - 1 - i) * grosor + (n - 1 - i) * hueco * separacion(i) + flota;
  const P = (x: number, y: number, z: number) => {
    const q = iso(x - A / 2, y - B / 2, z - ((n - 1) * (grosor + hueco)) / 2, esc);
    return { x: centro.x + q.x, y: centro.y + q.y };
  };
  const poli = (pts: { x: number; y: number }[]) => pts.map((q) => `${q.x},${q.y}`).join(" ");
  const entra = interpolate(t, [0, 14], [0, 1], { ...clamp, easing: curvas.entra });
  return (
    <AbsoluteFill style={{ background: "radial-gradient(ellipse at 40% 45%, #2a2c31 0%, #141518 70%)" }}>
      <div style={{ position: "absolute", top: H * (vertical ? 0.1 : 0.07), left: W * 0.07, fontFamily: fuenteEscenas, fontWeight: 700, fontSize: 24 * k, letterSpacing: 8 * k, color: "rgba(255,255,255,0.75)", textTransform: "uppercase", opacity: entra }}>
        {data.producto ?? "Producto"} <span style={{ opacity: 0.45 }}>· vista explotada</span>
      </div>
      <svg width={W} height={H} style={{ position: "absolute", inset: 0, opacity: entra }}>
        {capas
          .map((c, i) => ({ c, i }))
          .reverse()
          .map(({ c, i }) => {
            const z = zDe(i);
            const col = c.color ?? COLORES[i % COLORES.length];
            const arriba = [P(0, 0, z + grosor), P(A, 0, z + grosor), P(A, B, z + grosor), P(0, B, z + grosor)];
            const der = [P(A, 0, z + grosor), P(A, B, z + grosor), P(A, B, z), P(A, 0, z)];
            const frente = [P(0, B, z + grosor), P(A, B, z + grosor), P(A, B, z), P(0, B, z)];
            const patron: React.ReactNode[] = [];
            if (c.patron === "teclas" || c.patron === "puntos") {
              const cols = 14;
              const filas = 5;
              for (let fi = 0; fi < filas; fi++) {
                for (let co = 0; co < cols; co++) {
                  const x0 = 12 + co * ((A - 24) / cols);
                  const y0 = 12 + fi * ((B - 24) / filas);
                  const w = (A - 24) / cols - 4;
                  const h = (B - 24) / filas - 4;
                  if (c.patron === "puntos") {
                    const q = P(x0 + w / 2, y0 + h / 2, z + grosor);
                    patron.push(<circle key={`${fi}-${co}`} cx={q.x} cy={q.y} r={2.2 * esc * 3} fill="rgba(0,0,0,0.45)" />);
                  } else {
                    const alto = 8;
                    const especial = fi === 0 && co === cols - 1;
                    patron.push(
                      <polygon key={`${fi}-${co}`} points={poli([P(x0, y0, z + grosor + alto), P(x0 + w, y0, z + grosor + alto), P(x0 + w, y0 + h, z + grosor + alto), P(x0, y0 + h, z + grosor + alto)])} fill={especial ? "#E8674A" : oscurecer(col, 1.03)} stroke="rgba(0,0,0,0.25)" strokeWidth={1} />,
                    );
                  }
                }
              }
            }
            if (c.patron === "circuito") {
              for (let j = 0; j < 7; j++) {
                const a = P(20 + j * 40, 15, z + grosor);
                const b = P(20 + j * 40, B - 15, z + grosor);
                patron.push(<line key={j} x1={a.x} y1={a.y} x2={b.x} y2={b.y} stroke="rgba(255,255,255,0.25)" strokeWidth={1.5} />);
              }
              const chip = [P(A / 2 - 25, B / 2 - 15, z + grosor + 1), P(A / 2 + 25, B / 2 - 15, z + grosor + 1), P(A / 2 + 25, B / 2 + 15, z + grosor + 1), P(A / 2 - 25, B / 2 + 15, z + grosor + 1)];
              patron.push(<polygon key="chip" points={poli(chip)} fill="#1b1d22" />);
            }
            return (
              <g key={i}>
                <polygon points={poli(frente)} fill={oscurecer(col, 0.72)} />
                <polygon points={poli(der)} fill={oscurecer(col, 0.55)} />
                <polygon points={poli(arriba)} fill={col} />
                {patron}
              </g>
            );
          })}
        {/* etiquetas numeradas a la derecha, con su línea */}
        {capas.map((c, i) => {
          const s = separacion(i);
          if (s < 0.05) return null;
          const z = zDe(i);
          const desde = P(A, B / 2, z + grosor / 2);
          const xEt = W * (vertical ? 0.62 : 0.64);
          return (
            <g key={`et${i}`} opacity={interpolate(s, [0.3, 1], [0, 1], clamp)}>
              <circle cx={desde.x} cy={desde.y} r={6 * k} fill="#E8674A" />
              <line x1={desde.x} y1={desde.y} x2={xEt - 16 * k} y2={desde.y} stroke="rgba(255,255,255,0.35)" strokeWidth={2 * k} />
              <text x={xEt} y={desde.y + 4 * k} fill="#E8674A" fontSize={18 * k} fontFamily={fuenteEscenas} fontWeight={700}>
                {String(i + 1).padStart(2, "0")}
              </text>
              <text x={xEt + 40 * k} y={desde.y + 8 * k} fill="white" fontSize={34 * k} fontFamily={fuenteEscenas} fontWeight={800}>
                {c.nombre}
              </text>
              {c.detalle ? (
                <text x={xEt + 40 * k} y={desde.y + 34 * k} fill="rgba(255,255,255,0.55)" fontSize={18 * k} fontFamily={fuenteEscenas} fontWeight={700} letterSpacing={1}>
                  {c.detalle}
                </text>
              ) : null}
            </g>
          );
        })}
      </svg>
      <Leyenda data={data} />
    </AbsoluteFill>
  );
};
