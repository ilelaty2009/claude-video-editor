// /palitos — convierte una idea en una caricatura explicativa con monitos de palitos.
// Fondos (barco, salón, ciudad, campo, espacio, liso), objetos (barril, cofre, mesa, árbol, libro, casa, sol),
// personajes con poses (parado, camina, saluda, señala, sorprendido, pensando, corre) y accesorios
// (pirata, corona, lentes, gorra, birrete), globos de diálogo y el texto grande arriba, como los explicadores de TikTok.
import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { clamp, curvas, FPS_DISENO } from "../tiempo";
import { fontFamily, fuenteEscenas } from "../fuentes";
import { AnimacionData, azar, escalaDe, pasoActual, Personaje } from "./comun";

const TINTA = "#111111";

// ---------- fondos ----------
const Fondo: React.FC<{ tipo: string; W: number; H: number; k: number; f: number }> = ({ tipo, W, H, k, f }) => {
  const suelo = H * 0.74;
  const cielo = (
    <>
      <defs>
        <linearGradient id="cielo" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#4FA9EC" />
          <stop offset="100%" stopColor="#BFE4FF" />
        </linearGradient>
      </defs>
      <rect width={W} height={H} fill="url(#cielo)" />
      {[0.18, 0.62, 0.86].map((x, i) => {
        const cx = ((x * W + f * 0.6 * k * (i + 1)) % (W * 1.2)) - W * 0.1;
        return (
          <g key={i} fill="white" opacity={0.95}>
            <ellipse cx={cx} cy={H * (0.12 + i * 0.07)} rx={70 * k} ry={30 * k} />
            <ellipse cx={cx + 50 * k} cy={H * (0.12 + i * 0.07) - 18 * k} rx={50 * k} ry={30 * k} />
            <ellipse cx={cx - 50 * k} cy={H * (0.12 + i * 0.07) + 4 * k} rx={45 * k} ry={22 * k} />
          </g>
        );
      })}
    </>
  );
  if (tipo === "barco") {
    return (
      <svg width={W} height={H} style={{ position: "absolute", inset: 0 }}>
        {cielo}
        <rect y={H * 0.6} width={W} height={H * 0.14} fill="#2F7FC9" />
        {Array.from({ length: 12 }).map((_, i) => (
          <path key={i} d={`M${((i * 160 * k + f * 2 * k) % (W + 200)) - 100} ${H * 0.64 + (i % 3) * 22 * k} q ${20 * k} ${-10 * k} ${40 * k} 0`} stroke="#9DD3FF" strokeWidth={4 * k} fill="none" />
        ))}
        {/* barandilla */}
        <rect y={suelo - 70 * k} width={W} height={14 * k} fill="#8A5A2B" />
        {Array.from({ length: Math.ceil(W / (90 * k)) + 1 }).map((_, i) => (
          <rect key={i} x={i * 90 * k} y={suelo - 70 * k} width={12 * k} height={70 * k} fill="#7A4B22" />
        ))}
        {/* cubierta de madera */}
        <rect y={suelo} width={W} height={H - suelo} fill="#B9773D" />
        {Array.from({ length: 6 }).map((_, i) => (
          <line key={i} x1={0} x2={W} y1={suelo + (i + 1) * ((H - suelo) / 7)} y2={suelo + (i + 1) * ((H - suelo) / 7)} stroke="#8F5A2A" strokeWidth={4 * k} />
        ))}
        {/* mástil y vela */}
        <rect x={W * 0.82} y={H * 0.08} width={18 * k} height={suelo - H * 0.08} fill="#6B4320" />
        <path d={`M${W * 0.82 + 18 * k} ${H * 0.14} q ${W * 0.12} ${H * 0.12} 0 ${H * 0.3}`} fill="#F4EBD3" stroke="#D8C9A6" strokeWidth={3 * k} />
        <rect x={W * 0.82 + 18 * k} y={H * 0.08} width={70 * k} height={44 * k} fill={TINTA} />
        <circle cx={W * 0.82 + 53 * k} cy={H * 0.08 + 22 * k} r={10 * k} fill="white" />
      </svg>
    );
  }
  if (tipo === "salon") {
    return (
      <svg width={W} height={H} style={{ position: "absolute", inset: 0 }}>
        <rect width={W} height={H} fill="#F1E3C6" />
        <rect x={W * 0.12} y={H * 0.12} width={W * 0.76} height={H * 0.36} rx={10 * k} fill="#2F5D45" stroke="#8A5A2B" strokeWidth={16 * k} />
        <path d={`M${W * 0.2} ${H * 0.22} h ${W * 0.2} M${W * 0.2} ${H * 0.28} h ${W * 0.3} M${W * 0.2} ${H * 0.34} h ${W * 0.16}`} stroke="rgba(255,255,255,0.7)" strokeWidth={5 * k} strokeLinecap="round" />
        <rect y={suelo} width={W} height={H - suelo} fill="#C49A6C" />
      </svg>
    );
  }
  if (tipo === "ciudad") {
    return (
      <svg width={W} height={H} style={{ position: "absolute", inset: 0 }}>
        {cielo}
        {Array.from({ length: 9 }).map((_, i) => {
          const bw = W / 8;
          const bh = H * (0.25 + azar(i) * 0.3);
          return (
            <g key={i}>
              <rect x={i * bw - bw * 0.2} y={suelo - bh} width={bw * 0.9} height={bh} fill={["#7C8DB5", "#A3B1D1", "#6475A0"][i % 3]} />
              {Array.from({ length: 6 }).map((__, j) => (
                <rect key={j} x={i * bw - bw * 0.2 + bw * 0.15 + (j % 2) * bw * 0.35} y={suelo - bh + 30 * k + Math.floor(j / 2) * 60 * k} width={bw * 0.2} height={30 * k} fill="#FFF3B0" opacity={0.8} />
              ))}
            </g>
          );
        })}
        <rect y={suelo} width={W} height={H - suelo} fill="#6B6F78" />
        <line x1={0} x2={W} y1={suelo + (H - suelo) / 2} y2={suelo + (H - suelo) / 2} stroke="white" strokeWidth={6 * k} strokeDasharray={`${40 * k} ${30 * k}`} />
      </svg>
    );
  }
  if (tipo === "campo") {
    return (
      <svg width={W} height={H} style={{ position: "absolute", inset: 0 }}>
        {cielo}
        <circle cx={W * 0.82} cy={H * 0.16} r={60 * k} fill="#FFD84D" />
        <ellipse cx={W * 0.25} cy={suelo + 40 * k} rx={W * 0.6} ry={H * 0.16} fill="#7CC36A" />
        <ellipse cx={W * 0.85} cy={suelo + 60 * k} rx={W * 0.6} ry={H * 0.14} fill="#69B157" />
        <rect y={suelo} width={W} height={H - suelo} fill="#5FA34D" />
      </svg>
    );
  }
  if (tipo === "espacio") {
    return (
      <svg width={W} height={H} style={{ position: "absolute", inset: 0 }}>
        <rect width={W} height={H} fill="#0B1026" />
        {Array.from({ length: 70 }).map((_, i) => (
          <circle key={i} cx={azar(i) * W} cy={azar(i + 99) * H * 0.75} r={(1 + azar(i + 5) * 2.5) * k} fill="white" opacity={0.4 + 0.6 * Math.abs(Math.sin(f / 20 + i))} />
        ))}
        <circle cx={W * 0.8} cy={H * 0.2} r={90 * k} fill="#E07A5F" />
        <rect y={suelo} width={W} height={H - suelo} fill="#9AA0B5" />
      </svg>
    );
  }
  return (
    <svg width={W} height={H} style={{ position: "absolute", inset: 0 }}>
      <rect width={W} height={H} fill="#F3F4F6" />
      <line x1={0} x2={W} y1={suelo} y2={suelo} stroke={TINTA} strokeWidth={4 * k} />
    </svg>
  );
};

// ---------- objetos ----------
const Objeto: React.FC<{ tipo: string; x: number; y: number; s: number }> = ({ tipo, x, y, s }) => {
  const g = (hijos: React.ReactNode) => <g transform={`translate(${x} ${y}) scale(${s})`}>{hijos}</g>;
  switch (tipo) {
    case "barril":
      return g(
        <>
          <rect x={-55} y={-150} width={110} height={150} rx={30} fill="#9B5E2B" stroke={TINTA} strokeWidth={5} />
          <line x1={-55} x2={55} y1={-110} y2={-110} stroke={TINTA} strokeWidth={6} />
          <line x1={-55} x2={55} y1={-40} y2={-40} stroke={TINTA} strokeWidth={6} />
        </>,
      );
    case "cofre":
      return g(
        <>
          <rect x={-90} y={-110} width={180} height={110} fill="#6B3F1D" stroke={TINTA} strokeWidth={5} />
          <path d="M-90 -110 q 90 -60 180 0" fill="#7E4A22" stroke={TINTA} strokeWidth={5} />
          <rect x={-14} y={-90} width={28} height={36} fill="#E8B83A" stroke={TINTA} strokeWidth={4} />
        </>,
      );
    case "mesa":
      return g(
        <>
          <rect x={-130} y={-120} width={260} height={18} fill="#8A5A2B" stroke={TINTA} strokeWidth={4} />
          <rect x={-115} y={-102} width={14} height={102} fill="#7A4B22" />
          <rect x={101} y={-102} width={14} height={102} fill="#7A4B22" />
        </>,
      );
    case "arbol":
      return g(
        <>
          <rect x={-18} y={-160} width={36} height={160} fill="#7A4B22" />
          <circle cx={0} cy={-200} r={90} fill="#4CAF50" stroke={TINTA} strokeWidth={5} />
        </>,
      );
    case "libro":
      return g(
        <>
          <rect x={-70} y={-24} width={140} height={24} fill="#C0392B" stroke={TINTA} strokeWidth={4} />
          <rect x={-60} y={-46} width={120} height={22} fill="#2E86DE" stroke={TINTA} strokeWidth={4} />
        </>,
      );
    case "casa":
      return g(
        <>
          <rect x={-120} y={-170} width={240} height={170} fill="#F6E7C1" stroke={TINTA} strokeWidth={5} />
          <path d="M-140 -170 L0 -270 L140 -170 Z" fill="#C0392B" stroke={TINTA} strokeWidth={5} />
          <rect x={-30} y={-90} width={60} height={90} fill="#8A5A2B" />
        </>,
      );
    case "sol":
      return g(<circle cx={0} cy={-500} r={70} fill="#FFD84D" stroke={TINTA} strokeWidth={4} />);
    default:
      return null;
  }
};

// ---------- monito de palitos ----------
const angulos = (pose: Personaje["pose"], t: number) => {
  // ángulos en grados desde la vertical hacia abajo (positivo = hacia donde mira el monito):
  // [brazoAtrás, antebrazoAtrás, brazoAdelante, antebrazoAdelante, piernaAtrás, piernaAdelante]
  const paso = Math.sin(t / 4);
  switch (pose) {
    case "camina":
      return [-20 * paso, -10, 20 * paso, -10, 22 * paso, -22 * paso];
    case "corre":
      return [-45 * paso, -60, 45 * paso, -60, 38 * paso, -38 * paso];
    case "saluda":
      return [-18, -8, 140, 150 + 22 * Math.sin(t / 3), -10, 10];
    case "senala":
      return [-18, -8, 90, 90, -10, 10];
    case "sorprendido":
      return [-125, -150, 125, 150, -14, 14];
    case "pensando":
      return [-18, -8, 35, -158, -8, 8];
    default:
      return [-20, -8, 20, 8, -10, 10];
  }
};

const Monito: React.FC<{ p: Personaje; W: number; suelo: number; k: number; t: number; aparece: number; avance: number }> = ({ p, W, suelo, k, t, aparece, avance }) => {
  const [bi, ai, bd, ad, pi, pd] = angulos(p.pose, t);
  const rad = (g: number) => (g * Math.PI) / 180;
  const pt = (x: number, y: number, ang: number, l: number) => ({ x: x + Math.sin(rad(ang)) * l, y: y + Math.cos(rad(ang)) * l });
  const rebote = p.pose === "camina" || p.pose === "corre" ? Math.abs(Math.sin(t / 4)) * -8 : 0;
  const hombro = { x: 0, y: -255 + rebote };
  const cadera = { x: 0, y: -130 + rebote };
  const cabeza = { x: 0, y: -330 + rebote };
  const codoI = pt(hombro.x, hombro.y, bi, 62);
  const manoI = pt(codoI.x, codoI.y, ai, 58);
  const codoD = pt(hombro.x, hombro.y, bd, 62);
  const manoD = pt(codoD.x, codoD.y, ad, 58);
  const pieI = pt(cadera.x, cadera.y, pi, 130);
  const pieD = pt(cadera.x, cadera.y, pd, 130);
  const linea = (a: { x: number; y: number }, b: { x: number; y: number }) => <line x1={a.x} y1={a.y} x2={b.x} y2={b.y} stroke={TINTA} strokeWidth={11} strokeLinecap="round" />;
  const s = (suelo / 1000) * 1.15 * Math.max(0.8, k);
  const espejo = p.mira === "izq" ? -1 : 1;
  const parpadeo = Math.floor(t) % 90 < 4;
  return (
    <g transform={`translate(${p.x * W + avance * espejo} ${suelo}) scale(${s * espejo * aparece} ${s * aparece})`}>
      {linea(hombro, cadera)}
      {linea({ x: 0, y: -285 + rebote }, hombro)}
      {linea(hombro, codoI)}
      {linea(codoI, manoI)}
      {linea(hombro, codoD)}
      {linea(codoD, manoD)}
      {linea(cadera, pieI)}
      {linea(cadera, pieD)}
      <circle cx={cabeza.x} cy={cabeza.y} r={52} fill="white" stroke={TINTA} strokeWidth={10} />
      {/* cara */}
      <circle cx={-16} cy={cabeza.y - 8} r={parpadeo ? 2 : 6} fill={TINTA} />
      {p.accesorio === "pirata" ? (
        <>
          <circle cx={18} cy={cabeza.y - 8} r={15} fill={TINTA} />
          <line x1={-50} y1={cabeza.y - 30} x2={50} y2={cabeza.y + 5} stroke={TINTA} strokeWidth={5} />
        </>
      ) : (
        <circle cx={18} cy={cabeza.y - 8} r={parpadeo ? 2 : 6} fill={TINTA} />
      )}
      {p.pose === "sorprendido" ? (
        <ellipse cx={2} cy={cabeza.y + 22} rx={9} ry={13} fill={TINTA} />
      ) : (
        <path d={`M-16 ${cabeza.y + 16} q 18 16 36 0`} stroke={TINTA} strokeWidth={6} fill="none" strokeLinecap="round" />
      )}
      {/* accesorios */}
      {p.accesorio === "pirata" ? (
        <g>
          <path d={`M-80 ${cabeza.y - 38} q 80 -90 160 0 q -80 -20 -160 0`} fill={TINTA} />
          <circle cx={0} cy={cabeza.y - 62} r={10} fill="white" />
        </g>
      ) : null}
      {p.accesorio === "corona" ? <path d={`M-42 ${cabeza.y - 44} l0 -46 l21 24 l21 -34 l21 34 l21 -24 l0 46 z`} fill={p.color ?? "#F5C518"} stroke={TINTA} strokeWidth={5} /> : null}
      {p.accesorio === "lentes" ? (
        <g fill="none" stroke={TINTA} strokeWidth={5}>
          <circle cx={-18} cy={cabeza.y - 8} r={17} />
          <circle cx={20} cy={cabeza.y - 8} r={17} />
          <line x1={-1} y1={cabeza.y - 8} x2={3} y2={cabeza.y - 8} />
        </g>
      ) : null}
      {p.accesorio === "gorra" ? (
        <g>
          <path d={`M-52 ${cabeza.y - 18} a 52 50 0 0 1 104 0 z`} fill={p.color ?? "#E74C3C"} stroke={TINTA} strokeWidth={5} />
          <rect x={30} y={cabeza.y - 24} width={50} height={10} rx={5} fill={p.color ?? "#E74C3C"} stroke={TINTA} strokeWidth={4} />
        </g>
      ) : null}
      {p.accesorio === "birrete" ? (
        <g>
          <rect x={-40} y={cabeza.y - 64} width={80} height={22} fill={TINTA} />
          <path d={`M-75 ${cabeza.y - 64} L0 ${cabeza.y - 90} L75 ${cabeza.y - 64} L0 ${cabeza.y - 40} Z`} fill={TINTA} />
          <line x1={60} y1={cabeza.y - 66} x2={66} y2={cabeza.y - 20} stroke={p.color ?? "#F5C518"} strokeWidth={5} />
        </g>
      ) : null}
    </g>
  );
};

const Globo: React.FC<{ texto: string; x: number; y: number; k: number; aparece: number }> = ({ texto, x, y, k, aparece }) => (
  <div
    style={{
      position: "absolute",
      left: x,
      top: y,
      transform: `translate(-50%, -100%) scale(${aparece})`,
      transformOrigin: "50% 100%",
      maxWidth: 420 * k,
      padding: `${14 * k}px ${22 * k}px`,
      background: "white",
      border: `${5 * k}px solid ${TINTA}`,
      borderRadius: 26 * k,
      fontFamily: fuenteEscenas,
      fontWeight: 800,
      fontSize: 34 * k,
      color: TINTA,
      textAlign: "center",
    }}
  >
    {texto}
  </div>
);

export const Palitos: React.FC<{ data: AnimacionData }> = ({ data }) => {
  const frame = useCurrentFrame();
  const { width: W, height: H, fps } = useVideoConfig();
  const k = escalaDe(W, H);
  const t = (frame * FPS_DISENO) / fps;
  const { p, local, dur } = pasoActual(data, frame);
  const fondo = p.fondo ?? data.fondo ?? "liso";
  const suelo = H * 0.86;
  const aparece = spring({ frame: local, fps: FPS_DISENO, config: { damping: 12, stiffness: 160 } });
  const texto = spring({ frame: local, fps: FPS_DISENO, config: { damping: 14, stiffness: 200 } });
  const objetos = p.objetos ?? [];
  return (
    <AbsoluteFill style={{ background: "#fff" }}>
      <Fondo tipo={fondo} W={W} H={H} k={k} f={t} />
      <svg width={W} height={H} style={{ position: "absolute", inset: 0 }}>
        {objetos.map((o, i) => (
          <Objeto key={`${o}-${i}`} tipo={o} x={W * (i % 2 === 0 ? 0.14 + i * 0.05 : 0.72 - i * 0.03)} y={suelo} s={k * 0.95 * interpolate(aparece, [0, 1], [0.6, 1])} />
        ))}
        {(p.personajes ?? []).map((q, i) => (
          <Monito
            key={i}
            p={q}
            W={W}
            suelo={suelo}
            k={k}
            t={t}
            aparece={interpolate(aparece, [0, 1], [0.7, 1])}
            // quien camina o corre avanza de verdad por la escena (no se queda caminando en el mismo lugar)
            avance={q.pose === "camina" || q.pose === "corre" ? interpolate(local, [0, dur], [-0.12, 0.12]) * W * (q.pose === "corre" ? 1.8 : 1) : 0}
          />
        ))}
      </svg>
      {(p.personajes ?? []).map((q, i) =>
        q.dice ? <Globo key={`g${i}`} texto={q.dice} x={q.x * W} y={suelo - (suelo / 1000) * 1.15 * Math.max(0.8, k) * 420} k={k} aparece={interpolate(local, [6, 14], [0, 1], { ...clamp, easing: curvas.entra })} /> : null,
      )}
      <div
        style={{
          position: "absolute",
          top: H * (H > W ? 0.12 : 0.06),
          left: W * 0.06,
          right: W * 0.06,
          textAlign: "center",
          fontFamily,
          fontWeight: 900,
          fontSize: 66 * k,
          lineHeight: 1.12,
          color: "white",
          WebkitTextStroke: `${9 * k}px ${TINTA}`,
          paintOrder: "stroke fill",
          transform: `scale(${interpolate(texto, [0, 1], [0.85, 1])})`,
          opacity: texto,
        }}
      >
        {p.texto}
      </div>
    </AbsoluteFill>
  );
};
