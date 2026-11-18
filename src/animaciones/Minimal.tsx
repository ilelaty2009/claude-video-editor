// /minimalista — explica una idea con formas simples, puntos que se mueven y animaciones limpias.
// Fondo negro, líneas blancas finas, un punto brillante que recorre las formas dejando una estela.
import React from "react";
import { AbsoluteFill, Easing, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { clamp, curvas, FPS_DISENO } from "../tiempo";
import { fuenteEscenas } from "../fuentes";
import { AnimacionData, azar, escalaDe, pasoActual } from "./comun";

const BLANCO = "#FFFFFF";

const Barras: React.FC<{ f: number; dur: number; valores: number[]; W: number; H: number; k: number }> = ({ f, dur, valores, W, H, k }) => {
  const n = valores.length;
  const max = Math.max(...valores, 1);
  const ancho = Math.min(W * 0.8, n * 150 * k);
  const x0 = (W - ancho) / 2;
  const base = H * 0.86;
  const altoMax = H * 0.45;
  const bw = (ancho / n) * 0.62;
  const tope = (i: number) => ({ x: x0 + (i + 0.5) * (ancho / n), y: base - (valores[i] / max) * altoMax });
  const crece = (i: number) => spring({ frame: f - 4 - i * 4, fps: FPS_DISENO, config: { damping: 16, stiffness: 120 } });
  // el punto recorre las cimas de las barras
  const viaje = interpolate(f, [n * 4 + 10, Math.max(n * 4 + 20, dur * 0.85)], [0, n - 1], { ...clamp, easing: Easing.inOut(Easing.cubic) });
  const i0 = Math.floor(viaje);
  const a = tope(i0);
  const b = tope(Math.min(n - 1, i0 + 1));
  const t = viaje - i0;
  const punto = { x: a.x + (b.x - a.x) * t, y: a.y + (b.y - a.y) * t - 26 * k - Math.sin(t * Math.PI) * 40 * k };
  const estela = Array.from({ length: 26 }).map((_, j) => {
    const v = viaje - j * 0.06;
    if (v < 0) return null;
    const m = Math.floor(v);
    const p = tope(m);
    const q = tope(Math.min(n - 1, m + 1));
    const s = v - m;
    return (
      <circle key={j} cx={p.x + (q.x - p.x) * s + (azar(j) - 0.5) * 30 * k} cy={p.y + (q.y - p.y) * s - 26 * k - Math.sin(s * Math.PI) * 40 * k + (azar(j + 9) - 0.5) * 30 * k} r={(2.6 - j * 0.07) * k} fill={BLANCO} opacity={1 - j / 26} />
    );
  });
  return (
    <svg width={W} height={H} style={{ position: "absolute", inset: 0 }}>
      {valores.map((v, i) => {
        const h = (v / max) * altoMax * crece(i);
        return <rect key={i} x={tope(i).x - bw / 2} y={base - h} width={bw} height={h} fill="none" stroke={BLANCO} strokeWidth={3 * k} />;
      })}
      {viaje > 0 ? (
        <>
          {estela}
          <circle cx={punto.x} cy={punto.y} r={22 * k} fill="none" stroke={BLANCO} strokeWidth={2 * k} opacity={0.7} />
          <circle cx={punto.x} cy={punto.y} r={11 * k} fill={BLANCO} />
        </>
      ) : null}
    </svg>
  );
};

const Circulo: React.FC<{ f: number; dur: number; W: number; H: number; k: number; numero?: number }> = ({ f, dur, W, H, k, numero }) => {
  const r = Math.min(W, H) * 0.22;
  const cx = W / 2;
  const cy = H * 0.6;
  const dibuja = interpolate(f, [4, 28], [0, 1], { ...clamp, easing: curvas.cambia });
  const ang = interpolate(f, [20, dur], [-Math.PI / 2, Math.PI * 1.6], clamp);
  const largo = 2 * Math.PI * r;
  return (
    <svg width={W} height={H} style={{ position: "absolute", inset: 0 }}>
      <circle cx={cx} cy={cy} r={r} fill="none" stroke={BLANCO} strokeWidth={3 * k} strokeDasharray={largo} strokeDashoffset={largo * (1 - dibuja)} transform={`rotate(-90 ${cx} ${cy})`} />
      {f > 20 ? <circle cx={cx + Math.cos(ang) * r} cy={cy + Math.sin(ang) * r} r={12 * k} fill={BLANCO} /> : null}
      {numero !== undefined ? (
        <text x={cx} y={cy + 30 * k} textAnchor="middle" fill={BLANCO} fontSize={90 * k} fontFamily={fuenteEscenas} fontWeight={700}>
          {numero > 10 ? Math.round(numero * dibuja) : numero /* los números chicos no "cuentan": se muestran tal cual */}
        </text>
      ) : null}
    </svg>
  );
};

const Puntos: React.FC<{ f: number; dur: number; W: number; H: number; k: number; numero?: number }> = ({ f, dur, W, H, k, numero }) => {
  const cols = 9;
  const filas = 5;
  const paso = Math.min(W * 0.8 / cols, 90 * k);
  const x0 = W / 2 - (paso * (cols - 1)) / 2;
  const y0 = H * 0.42;
  const destacar = numero ?? 5;
  return (
    <svg width={W} height={H} style={{ position: "absolute", inset: 0 }}>
      {Array.from({ length: cols * filas }).map((_, i) => {
        const c = i % cols;
        const fi = Math.floor(i / cols);
        const s = spring({ frame: f - 2 - (c + fi) * 1.2, fps: FPS_DISENO, config: { damping: 14 } });
        // se encienden uno por uno y terminan antes del final del paso
        const encendido = i < destacar && f > 16 + (i / Math.max(1, destacar)) * Math.max(10, dur * 0.7 - 16);
        return <circle key={i} cx={x0 + c * paso} cy={y0 + fi * paso} r={(encendido ? 13 : 6) * k * s} fill={encendido ? BLANCO : "rgba(255,255,255,0.35)"} />;
      })}
    </svg>
  );
};

const Linea: React.FC<{ f: number; dur: number; W: number; H: number; k: number; valores: number[] }> = ({ f, dur, W, H, k, valores }) => {
  const max = Math.max(...valores, 1);
  const pts = valores.map((v, i) => ({ x: W * 0.12 + (i / Math.max(1, valores.length - 1)) * W * 0.76, y: H * 0.85 - (v / max) * H * 0.42 }));
  const p = interpolate(f, [4, dur * 0.8], [0, 1], { ...clamp, easing: Easing.inOut(Easing.cubic) });
  const largo = pts.reduce((s, q, i) => (i ? s + Math.hypot(q.x - pts[i - 1].x, q.y - pts[i - 1].y) : 0), 0);
  let resto = p * largo;
  let punta = pts[0];
  for (let i = 1; i < pts.length; i++) {
    const d = Math.hypot(pts[i].x - pts[i - 1].x, pts[i].y - pts[i - 1].y);
    if (resto <= d) {
      punta = { x: pts[i - 1].x + ((pts[i].x - pts[i - 1].x) * resto) / d, y: pts[i - 1].y + ((pts[i].y - pts[i - 1].y) * resto) / d };
      break;
    }
    resto -= d;
    punta = pts[i];
  }
  return (
    <svg width={W} height={H} style={{ position: "absolute", inset: 0 }}>
      <polyline points={pts.map((q) => `${q.x},${q.y}`).join(" ")} fill="none" stroke={BLANCO} strokeWidth={3 * k} strokeDasharray={largo} strokeDashoffset={largo * (1 - p)} />
      <circle cx={punta.x} cy={punta.y} r={12 * k} fill={BLANCO} />
    </svg>
  );
};

export const Minimal: React.FC<{ data: AnimacionData }> = ({ data }) => {
  const frame = useCurrentFrame();
  const { width: W, height: H } = useVideoConfig();
  const k = escalaDe(W, H);
  const { p, local, dur } = pasoActual(data, frame);
  const entra = interpolate(local, [0, 9], [0, 1], { ...clamp, easing: curvas.entra });
  const sale = interpolate(local, [dur - 7, dur], [1, 0], { ...clamp, easing: curvas.sale });
  const visual = p.visual ?? "barras";
  const valores = p.valores?.length ? p.valores : [2, 3, 4, 5, 7];
  return (
    <AbsoluteFill style={{ background: "#000" }}>
      <AbsoluteFill style={{ opacity: Math.min(entra, sale), transform: `scale(${0.97 + 0.03 * entra})` }}>
        <div style={{ position: "absolute", top: H * (H > W ? 0.16 : 0.1), left: W * 0.08, right: W * 0.08, textAlign: "center", color: BLANCO, fontFamily: fuenteEscenas, fontWeight: 700, fontSize: 62 * k, lineHeight: 1.2, letterSpacing: 0.5 }}>
          {p.texto}
        </div>
        {visual === "barras" ? <Barras f={local} dur={dur} valores={valores} W={W} H={H} k={k} /> : null}
        {visual === "circulo" ? <Circulo f={local} dur={dur} W={W} H={H} k={k} numero={p.numero} /> : null}
        {visual === "puntos" ? <Puntos f={local} dur={dur} W={W} H={H} k={k} numero={p.numero} /> : null}
        {visual === "linea" ? <Linea f={local} dur={dur} W={W} H={H} k={k} valores={valores} /> : null}
        {visual === "numero" ? (
          <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", paddingTop: H * 0.12 }}>
            <div style={{ color: BLANCO, fontFamily: fuenteEscenas, fontWeight: 700, fontSize: 260 * k, fontVariantNumeric: "tabular-nums" }}>
              {Math.round((p.numero ?? 0) * interpolate(local, [4, dur * 0.7], [0, 1], { ...clamp, easing: curvas.entra })).toLocaleString("es-CO")}
            </div>
          </AbsoluteFill>
        ) : null}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
