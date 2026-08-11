// Carte choroplèthe des départements (métropole), révélée région par région.
// Couleur séquentielle à une teinte (sable -> vert-bleu profond), classes par quantiles + légende.
import { motion } from "motion/react";
import { useMemo, useRef, useState } from "react";
import type { Carte } from "../lib/data";
import { EASE } from "./Motion";
import { useReducedMotion } from "../lib/theme";
import { classOf, quantileBreaks } from "../lib/scale";

const STEPS = ["--seq-0", "--seq-1", "--seq-2", "--seq-3", "--seq-4", "--seq-5"];

export interface Balise { dep: string; n: number; label: string }

export default function FranceMap({
  carte, values, regionOf, format, label, balises = [], onSelect, selected,
}: {
  carte: Carte;
  values: Record<string, number | null>;
  regionOf: (dep: string) => string;
  format: (x: number) => string;
  label: string;
  balises?: Balise[];
  onSelect?: (dep: string) => void;
  selected?: string | null;
}) {
  const reduced = useReducedMotion();
  const wrap = useRef<HTMLDivElement>(null);
  const [tip, setTip] = useState<{ x: number; y: number; text: string } | null>(null);
  const breaks = useMemo(() => quantileBreaks(Object.values(values).filter((x): x is number => x != null), STEPS.length), [values]);
  // Ordre de révélation : régions triées d'ouest en est (centre de gravité des départements).
  const regionOrder = useMemo(() => {
    const acc = new Map<string, { x: number; n: number }>();
    for (const [code, d] of Object.entries(carte.departements)) {
      const r = regionOf(code);
      const a = acc.get(r) ?? { x: 0, n: 0 };
      acc.set(r, { x: a.x + d.cx, n: a.n + 1 });
    }
    return [...acc.entries()].sort((a, b) => a[1].x / a[1].n - b[1].x / b[1].n).map(([r]) => r);
  }, [carte, regionOf]);

  const show = (e: React.MouseEvent | React.FocusEvent, code: string) => {
    const box = wrap.current!.getBoundingClientRect();
    const t = (e.target as SVGPathElement).getBoundingClientRect();
    const v = values[code];
    setTip({
      x: Math.min(t.left - box.left + t.width / 2, box.width - 160),
      y: t.top - box.top - 8,
      text: `${carte.departements[code].nom} (${code}) : ${v == null ? "donnée insuffisante" : format(v)}`,
    });
  };

  return (
    <div className="map" ref={wrap} style={{ position: "relative" }}>
      <svg viewBox={`0 0 ${carte.width} ${carte.height}`} role="img" aria-label={label}>
        {Object.entries(carte.departements).map(([code, d]) => {
          const v = values[code];
          const cls = v == null ? -1 : classOf(v, breaks);
          const delay = reduced ? 0 : 0.08 * regionOrder.indexOf(regionOf(code));
          return (
            <motion.path
              key={code}
              className="dep"
              d={d.d}
              tabIndex={0}
              role="button"
              aria-label={`${d.nom} : ${v == null ? "donnée insuffisante" : format(v)}`}
              aria-pressed={selected === code}
              style={{ fill: cls < 0 ? "var(--paper-2)" : `var(${STEPS[cls]})`, cursor: onSelect ? "pointer" : "default" }}
              initial={reduced ? false : { opacity: 0 }}
              animate={{ opacity: selected && selected !== code ? 0.45 : 1 }}
              transition={{ duration: 0.4, ease: EASE, delay }}
              onMouseMove={(e) => show(e, code)}
              onFocus={(e) => show(e, code)}
              onMouseLeave={() => setTip(null)}
              onBlur={() => setTip(null)}
              onClick={() => onSelect?.(code)}
              onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && onSelect?.(code)}
            />
          );
        })}
        {balises.map((b, i) => {
          const d = carte.departements[b.dep];
          if (!d) return null;
          const r = 4 + Math.min(6, Math.sqrt(b.n) * 2);
          return (
            <g key={b.dep} aria-hidden="true">
              {!reduced && (
                <motion.circle
                  className="balise-ring"
                  cx={d.cx} cy={d.cy} r={r}
                  initial={{ scale: 1, opacity: 0.8 }}
                  animate={{ scale: 2.6, opacity: 0 }}
                  transition={{ duration: 1.6, ease: "easeOut", delay: 0.6 + i * 0.05, repeat: 2, repeatDelay: 0.4 }}
                  style={{ transformOrigin: `${d.cx}px ${d.cy}px` }}
                />
              )}
              <motion.circle
                className="balise-core"
                cx={d.cx} cy={d.cy} r={r}
                initial={reduced ? false : { scale: 0, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ duration: 0.35, ease: EASE, delay: reduced ? 0 : 0.5 + i * 0.05 }}
                style={{ transformOrigin: `${d.cx}px ${d.cy}px` }}
              >
                <title>{b.label}</title>
              </motion.circle>
            </g>
          );
        })}
      </svg>
      {tip && (
        <div className="map-tip" style={{ left: Math.max(0, tip.x - 80), top: Math.max(0, tip.y - 34) }}>{tip.text}</div>
      )}
      {breaks.length > 0 && (
        <div className="scale" aria-hidden="true">
          <span>{format(Math.min(...Object.values(values).filter((x): x is number => x != null)))}</span>
          <span className="ramp">{STEPS.map((s) => <i key={s} style={{ background: `var(${s})` }} />)}</span>
          <span>{format(Math.max(...Object.values(values).filter((x): x is number => x != null)))}</span>
          <span style={{ marginLeft: 10, display: "inline-flex", alignItems: "center", gap: 4 }}>
            <i style={{ width: 10, height: 8, background: "var(--paper-2)", border: "1px solid var(--rule)" }} /> insuffisant
          </span>
        </div>
      )}
    </div>
  );
}
