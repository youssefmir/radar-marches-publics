// Chargement des exports statiques (web/public/data), mis en cache en mémoire.
const cache = new Map<string, Promise<unknown>>();

export function dataUrl(path: string): string {
  return `${import.meta.env.BASE_URL}data/${path}`;
}

export function fetchJson<T>(path: string): Promise<T> {
  if (!cache.has(path)) {
    cache.set(
      path,
      fetch(dataUrl(path)).then((r) => {
        if (!r.ok) throw new Error(`${path} : ${r.status}`);
        return r.json();
      }),
    );
  }
  return cache.get(path) as Promise<T>;
}

export interface MetricDef {
  label: string;
  type: "ratio" | "sql";
  numerator?: string;
  denominator?: string;
  format: string;
  definition: string;
  grain?: string;
}
export interface Catalog {
  periode: string;
  dimensions: Record<string, string>;
  measures: Record<string, string>;
  metrics: Record<string, MetricDef>;
}
export interface Meta {
  decp: { version: string; url: string; date_max_notification: string };
  boamp: { snapshot_date: string; avis_instantane: number; avis_ouverts_retenus: number; par_type: Record<string, number> };
  cube_lignes: number;
  periode: string;
}
export interface Dimensions {
  departements: { code_departement: string; nom_departement: string; code_region: string; nom_region: string }[];
  regions: { code_region: string; nom_region: string }[];
  divisions_cpv: { code: string; libelle: string; type_cpv: string }[];
  procedures: { procedure_code: string; procedure_libelle: string; avec_publicite: boolean | null; ordre: number }[];
}
export interface CarteDep { nom: string; d: string; cx: number; cy: number }
export interface Carte { width: number; height: number; source: string; departements: Record<string, CarteDep> }
