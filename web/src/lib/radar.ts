export interface Composante { valeur: number; poids: number; contribution: number }
export interface GoNoGo { critere: string; statut: "ok" | "attention" | "risque" | "info" | "inconnu"; detail: string }
export interface Resultat {
  idweb: string; url: string; objet: string; acheteur: string; departements: string[];
  date_limite: string; date_parution: string; procedure: string | null; type_marche: string | null;
  cpv: { code: string; libelle: string }[]; montant_estime: number | null; nb_lots: number; score: number;
  composantes: Record<string, Composante>;
  historique: Record<string, string | number | null>;
  go_no_go: GoNoGo[]; verdict: string; extrait: string;
}
export interface Profil {
  id: string; nom: string; fictif: boolean; secteur?: string; effectif?: number; ville?: string; description: string;
  cpv: string[]; departements: string[]; montant_min: number | null; montant_max: number | null;
}
export interface RadarRun { snapshot_date: string; profil: Profil; resultats: Resultat[] }
export interface RadarIndex {
  snapshot_date: string; nb_avis: number; poids: Record<string, number>; composantes: Record<string, string>;
  profils: { id: string; nom: string; secteur: string; effectif: number; ville: string; fictif: boolean }[];
}

/** Trois familles de composantes, chacune portée par une couleur de série validée. */
export const FAMILLES: { id: string; label: string; color: string; comps: string[] }[] = [
  { id: "pertinence", label: "Pertinence (sens, mots-clés, CPV)", color: "var(--viz-1)", comps: ["semantique", "lexical", "cpv"] },
  { id: "faisabilite", label: "Faisabilité (territoire, taille)", color: "var(--viz-2)", comps: ["geographie", "taille"] },
  { id: "opportunite", label: "Opportunité (concurrence, sortant)", color: "var(--viz-3)", comps: ["concurrence", "sortant"] },
];

export const LIBELLES: Record<string, string> = {
  semantique: "Sémantique", lexical: "Mots-clés", cpv: "CPV", geographie: "Géographie", taille: "Taille",
  concurrence: "Concurrence", sortant: "Titulaire sortant",
};

export function famille(comp: string) {
  return FAMILLES.find((f) => f.comps.includes(comp))!;
}

export function joursRestants(dateLimite: string, snapshot: string): number {
  const a = new Date(dateLimite).getTime();
  const b = new Date(`${snapshot}T00:00:00Z`).getTime();
  return Math.floor((a - b) / 86_400_000);
}
