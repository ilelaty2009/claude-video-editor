// Escenas de texto: chat que se escribe solo, cartel de nombre, cita, número que cuenta y miniatura.
import React from "react";
import { AbsoluteFill, Easing, interpolate, spring } from "remotion";
import { clamp, curvas, salida, useConfigDiseno, useCuadro } from "../tiempo";
import { fuenteEscenas } from "../fuentes";
import { colores, Fondo, Titular, useK } from "./base";
import type { Escena } from "./tipos";

// ---------- CHAT ----------
export const EscenaChat: React.FC<{ e: Escena }> = ({ e }) => {
  const frame = useCuadro();
  const { fps, durationInFrames } = useConfigDiseno();
  const k = useK();
  const texto = e.texto ?? "";
  const s = spring({ frame, fps, config: { damping: 15, stiffness: 170 } });
  const sale = salida(frame, durationInFrames, 7);
  const finEscritura = Math.max(10, Math.min(durationInFrames * 0.7, texto.length * 1.4 + 8));
  const n = Math.round(interpolate(frame, [6, finEscritura], [0, texto.length], clamp));
  const cursor = Math.floor(frame / 8) % 2 === 0 || n < texto.length;
  const enviado = frame > finEscritura + 6;
  const boton = spring({ frame: frame - finEscritura - 6, fps, config: { damping: 8, stiffness: 220 } });
  const lado = e.lado ?? "der";
  return (
    <AbsoluteFill
      style={{
        justifyContent: e.vertical === "centro" ? "center" : "flex-start",
        alignItems: lado === "izq" ? "flex-start" : lado === "centro" ? "center" : "flex-end",
        padding: `${190 * k}px ${130 * k}px`,
      }}
    >
      <div
        style={{
          width: 700 * k,
          minHeight: 220 * k,
          padding: `${26 * k}px ${32 * k}px`,
          borderRadius: 26 * k,
          background: "rgba(18,20,30,0.94)",
          border: "1px solid rgba(255,255,255,0.08)",
          boxShadow: "0 30px 70px rgba(0,0,0,0.55)",
          opacity: Math.min(s, sale),
          transform: `translateY(${(1 - s) * 40 * k}px) scale(${interpolate(s, [0, 1], [0.9, 1])})`,
          fontFamily: fuenteEscenas,
          position: "relative",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 9 * k, marginBottom: 18 * k }}>
          {["#FF5F57", "#FEBC2E", "#28C840"].map((c) => (
            <span key={c} style={{ width: 13 * k, height: 13 * k, borderRadius: 99, background: c }} />
          ))}
          <span style={{ marginLeft: 12 * k, color: "rgba(255,255,255,0.45)", fontWeight: 700, fontSize: 22 * k, letterSpacing: 3 }}>
            {(e.etiqueta ?? "PROMPT").toUpperCase()}
          </span>
        </div>
        <div style={{ color: "white", fontWeight: 700, fontSize: 44 * k, lineHeight: 1.25, paddingRight: 60 * k }}>
          {texto.slice(0, n)}
          <span style={{ opacity: cursor && !enviado ? 1 : 0, color: colores.amarillo }}>|</span>
        </div>
        <div
          style={{
            position: "absolute",
            right: 26 * k,
            bottom: 24 * k,
            width: 54 * k,
            height: 54 * k,
            borderRadius: 99,
            background: "#E8673C",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            transform: `scale(${enviado ? 1 + (1 - boton) * 0.3 : 1})`,
            boxShadow: enviado ? `0 0 ${30 * k}px #E8673C` : "none",
          }}
        >
          <svg width={26 * k} height={26 * k} viewBox="0 0 24 24">
            <path d="M12 19V5M5 12l7-7 7 7" stroke="white" strokeWidth={3} fill="none" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ---------- NOMBRE (lower third) ----------
export const EscenaNombre: React.FC<{ e: Escena }> = ({ e }) => {
  const frame = useCuadro();
  const { fps, durationInFrames } = useConfigDiseno();
  const k = useK();
  const barra = spring({ frame, fps, config: { damping: 16, stiffness: 160 } });
  const texto = spring({ frame: frame - 5, fps, config: { damping: 16, stiffness: 160 } });
  const sale = salida(frame, durationInFrames, 8);
  const der = e.lado === "der";
  return (
    <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: der ? "flex-end" : "flex-start", padding: `0 ${110 * k}px ${210 * k}px` }}>
      <div style={{ display: "flex", flexDirection: der ? "row-reverse" : "row", alignItems: "stretch", gap: 18 * k, opacity: sale }}>
        <div style={{ width: 10 * k, borderRadius: 6, background: colores.rojo, transform: `scaleY(${barra})`, transformOrigin: "bottom" }} />
        <div style={{ overflow: "hidden", padding: `${4 * k}px 0` }}>
          <div
            style={{
              transform: `translateX(${(1 - texto) * (der ? 60 : -60) * k}px)`,
              opacity: texto,
              fontFamily: fuenteEscenas,
              textAlign: der ? "right" : "left",
              textShadow: "0 4px 18px rgba(0,0,0,0.7)",
            }}
          >
            <div style={{ fontWeight: 900, fontSize: 62 * k, color: "white", lineHeight: 1, textTransform: "uppercase", letterSpacing: -1 }}>
              {e.texto ?? ""}
            </div>
            {e.rol ? (
              <div style={{ fontWeight: 700, fontSize: 30 * k, color: colores.amarillo, marginTop: 8 * k, textTransform: "uppercase", letterSpacing: 2 }}>
                {e.rol}
              </div>
            ) : null}
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ---------- CITA ----------
export const EscenaCita: React.FC<{ e: Escena }> = ({ e }) => {
  const frame = useCuadro();
  const { fps, durationInFrames } = useConfigDiseno();
  const k = useK();
  const palabras = (e.texto ?? "").split(/\s+/).filter(Boolean);
  const total = Math.max(1, Math.min(durationInFrames * 0.65, palabras.length * 4));
  const comillas = spring({ frame, fps, config: { damping: 10, stiffness: 160 } });
  const autor = spring({ frame: frame - Math.round(total) - 4, fps, config: { damping: 16 } });
  // tamaño según lo larga que sea la frase: corta = gigante, larga = más pequeña (pero siempre legible)
  const tam = Math.max(54, Math.min(100, 112 - (e.texto ?? "").length * 0.55)) * k;
  return (
    <Fondo entrada={e.entrada}>
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", padding: `0 ${220 * k}px ${80 * k}px` }}>
        <div style={{ fontFamily: "Georgia, serif", fontSize: 220 * k, lineHeight: 0.6, color: colores.amarillo, transform: `scale(${comillas})`, height: 110 * k }}>“</div>
        <div style={{ fontFamily: fuenteEscenas, fontWeight: 800, fontSize: tam, lineHeight: 1.18, color: "white", textAlign: "center" }}>
          {palabras.map((p, i) => {
            const o = interpolate(frame, [4 + (i * total) / palabras.length, 10 + (i * total) / palabras.length], [0, 1], { ...clamp, easing: curvas.entra });
            return (
              <span key={i} style={{ opacity: o, display: "inline-block", transform: `translateY(${(1 - o) * 14 * k}px)`, marginRight: tam * 0.28 }}>
                {p}
              </span>
            );
          })}
        </div>
        {e.autor ? (
          <div style={{ marginTop: 34 * k, fontFamily: fuenteEscenas, fontWeight: 700, fontSize: 34 * k, color: "rgba(255,255,255,0.7)", letterSpacing: 2, opacity: autor, textTransform: "uppercase" }}>
            — {e.autor}
          </div>
        ) : null}
      </AbsoluteFill>
    </Fondo>
  );
};

// ---------- NÚMERO QUE CUENTA ----------
export const EscenaNumero: React.FC<{ e: Escena }> = ({ e }) => {
  const frame = useCuadro();
  const { fps } = useConfigDiseno();
  const k = useK();
  const valor = e.valor ?? 0;
  const t = interpolate(frame, [4, 4 + fps * 1.1], [0, 1], { ...clamp, easing: Easing.out(Easing.cubic) });
  const dec = e.decimales ?? 0;
  const n = (valor * t).toFixed(dec);
  const conPuntos = dec === 0 && Math.abs(valor) >= 10000 ? Number(n).toLocaleString("es-CO") : n;
  const golpe = frame > 4 + fps * 1.1 ? spring({ frame: frame - Math.round(4 + fps * 1.1), fps, config: { damping: 8, stiffness: 260 } }) : 0;
  const etiqueta = spring({ frame: frame - 10, fps, config: { damping: 16 } });
  return (
    <Fondo entrada={e.entrada}>
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", paddingBottom: 90 * k, fontFamily: fuenteEscenas }}>
        {e.arriba ? (
          <div style={{ fontWeight: 700, fontSize: 40 * k, color: "rgba(255,255,255,0.85)", textTransform: "uppercase", letterSpacing: 2, marginBottom: 10 * k }}>{e.arriba}</div>
        ) : null}
        <div
          style={{
            fontWeight: 900,
            fontSize: 320 * k,
            lineHeight: 1,
            letterSpacing: -6 * k,
            color: e.lineas?.[0]?.color ?? colores.amarillo,
            fontVariantNumeric: "tabular-nums",
            transform: `scale(${1 + (golpe ? (1 - golpe) * 0.08 : 0)})`,
            textShadow: `0 0 ${60 * k}px ${(e.lineas?.[0]?.color ?? colores.amarillo)}55`,
          }}
        >
          {e.prefijo ?? ""}
          {conPuntos}
          {e.sufijo ?? ""}
        </div>
        {e.etiqueta ? (
          <div style={{ fontWeight: 800, fontSize: 48 * k, color: "white", textTransform: "uppercase", marginTop: 14 * k, opacity: etiqueta, transform: `translateY(${(1 - etiqueta) * 20 * k}px)` }}>
            {e.etiqueta}
          </div>
        ) : null}
      </AbsoluteFill>
    </Fondo>
  );
};

// ---------- MINIATURA (el titular; el video lo encoge Edit.tsx con estadoVideo) ----------
export const EscenaMiniatura: React.FC<{ e: Escena }> = ({ e }) => {
  const lado = e.lado ?? "der"; // lado del texto
  return <Titular e={{ ...e, lado: lado === "izq" ? "izq" : "der", vertical: e.vertical ?? "centro" }} ancho={640} />;
};
