// Formats français (espace insécable fine comme séparateur des milliers).
const nf0 = new Intl.NumberFormat("fr-FR", { maximumFractionDigits: 0 });
const nf1 = new Intl.NumberFormat("fr-FR", { minimumFractionDigits: 1, maximumFractionDigits: 1 });

export function entier(x: number | null | undefined): string {
  return x == null || !Number.isFinite(x) ? "–" : nf0.format(Math.round(x));
}

export function decimal(x: number | null | undefined, d = 1): string {
  if (x == null || !Number.isFinite(x)) return "–";
  return d === 1 ? nf1.format(x) : new Intl.NumberFormat("fr-FR", { maximumFractionDigits: d, minimumFractionDigits: d }).format(x);
}

export function pct(x: number | null | undefined, d = 1): string {
  return x == null || !Number.isFinite(x) ? "–" : `${decimal(100 * x, d)} %`;
}

/** Montant en euros abrégé : 1,2 Md€, 340 M€, 85 k€. */
export function euros(x: number | null | undefined): string {
  if (x == null || !Number.isFinite(x)) return "–";
  const a = Math.abs(x);
  const nb = "\u00a0"; // l'unité ne se sépare jamais du nombre
  if (a >= 1e9) return `${decimal(x / 1e9, a >= 1e11 ? 0 : 1)}${nb}Md€`;
  if (a >= 1e6) return `${decimal(x / 1e6, a >= 1e8 ? 0 : 1)}${nb}M€`;
  if (a >= 1e3) return `${entier(x / 1e3)}${nb}k€`;
  return `${entier(x)}${nb}€`;
}

export function format(x: number | null | undefined, kind: string): string {
  switch (kind) {
    case "euros": return euros(x);
    case "pourcentage": return pct(x);
    case "decimal": return decimal(x);
    default: return entier(x);
  }
}

export function dateFr(iso: string | null | undefined): string {
  if (!iso) return "–";
  const d = new Date(iso.length <= 10 ? `${iso}T12:00:00` : iso);
  if (Number.isNaN(d.getTime())) return iso;
  const s = d.toLocaleDateString("fr-FR", { day: "numeric", month: "long", year: "numeric" });
  return d.getDate() === 1 ? s.replace(/^1 /, "1er ") : s; // « 1er novembre »
}
