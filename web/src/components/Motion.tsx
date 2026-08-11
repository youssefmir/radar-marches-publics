// Animations sobres : apparition au défilement et compteur incrémenté une seule fois.
// Uniquement opacité / translation, 150 à 600 ms, ease-out, désactivées si prefers-reduced-motion.
import { animate, motion, useInView } from "motion/react";
import { useEffect, useRef, useState, type ReactNode } from "react";
import { useReducedMotion } from "../lib/theme";

export const EASE = [0.22, 1, 0.36, 1] as const;

export function Reveal({ children, delay = 0, className, as = "div" }: {
  children: ReactNode; delay?: number; className?: string; as?: "div" | "section" | "li" | "article";
}) {
  const reduced = useReducedMotion();
  const M = motion[as];
  if (reduced) return <M className={className}>{children}</M>;
  return (
    <M
      className={className}
      initial={{ opacity: 0, y: 14 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-40px" }}
      transition={{ duration: 0.5, ease: EASE, delay }}
    >
      {children}
    </M>
  );
}

export function CountUp({ value, format }: { value: number | null; format: (x: number) => string }) {
  const ref = useRef<HTMLSpanElement>(null);
  const inView = useInView(ref, { once: true });
  const reduced = useReducedMotion();
  const [shown, setShown] = useState<number | null>(reduced ? value : null);
  useEffect(() => {
    if (value == null) return;
    if (reduced || !inView) {
      if (reduced) setShown(value);
      return;
    }
    const c = animate(0, value, { duration: 0.6, ease: EASE, onUpdate: setShown });
    return () => c.stop();
  }, [value, inView, reduced]);
  return (
    <span ref={ref} aria-label={value == null ? undefined : format(value)}>
      <span aria-hidden="true">{shown == null ? (value == null ? "–" : format(0)) : format(shown)}</span>
    </span>
  );
}
