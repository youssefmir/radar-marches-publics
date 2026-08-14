// Décomposition du score en barre empilée : un segment par composante, coloré par famille,
// séparés par un filet de 2 px ; les segments se construisent de gauche à droite.
import { motion } from "motion/react";
import { famille, FAMILLES, LIBELLES, type Composante } from "../lib/radar";
import { EASE } from "./Motion";
import { useReducedMotion } from "../lib/theme";

const ORDER = FAMILLES.flatMap((f) => f.comps);

export function ScoreLegend() {
  return (
    <div className="legend" aria-label="Légende de la décomposition du score">
      {FAMILLES.map((f) => <span key={f.id}><i style={{ background: f.color }} />{f.label}</span>)}
    </div>
  );
}

export default function ScoreBar({ composantes, delay = 0 }: { composantes: Record<string, Composante>; delay?: number }) {
  const reduced = useReducedMotion();
  const desc = ORDER.map((k) => `${LIBELLES[k]} ${composantes[k]?.contribution ?? 0} points`).join(", ");
  return (
    <div className="decomp" role="img" aria-label={`Décomposition du score : ${desc}`}>
      {ORDER.map((k, i) => {
        const c = composantes[k];
        if (!c || c.contribution <= 0) return null;
        return (
          <motion.span
            key={k}
            title={`${LIBELLES[k]} : ${c.contribution} pts (valeur ${c.valeur.toFixed(2)} × poids ${c.poids})`}
            style={{ width: `${c.contribution}%`, background: famille(k).color }}
            initial={reduced ? false : { scaleX: 0 }}
            animate={{ scaleX: 1 }}
            transition={{ duration: 0.35, ease: EASE, delay: delay + i * 0.06 }}
          />
        );
      })}
    </div>
  );
}
