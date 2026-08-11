import { useEffect, useMemo, useState } from "react";
import { fetchJson, dataUrl, type Catalog, type Carte, type Dimensions, type Meta } from "./data";
import { loadCube, type Row } from "./cube";

export function useAsync<T>(fn: () => Promise<T>, deps: unknown[] = []): { data: T | null; error: string | null } {
  const [state, setState] = useState<{ data: T | null; error: string | null }>({ data: null, error: null });
  useEffect(() => {
    let alive = true;
    fn().then(
      (data) => alive && setState({ data, error: null }),
      (e) => alive && setState({ data: null, error: String(e) }),
    );
    return () => {
      alive = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
  return state;
}

export interface Base { meta: Meta; catalog: Catalog; dims: Dimensions; carte: Carte }

export function useBase() {
  return useAsync<Base>(async () => {
    const [meta, catalog, dims, carte] = await Promise.all([
      fetchJson<Meta>("meta.json"), fetchJson<Catalog>("metrics.json"),
      fetchJson<Dimensions>("dimensions.json"), fetchJson<Carte>("carte_departements.json"),
    ]);
    return { meta, catalog, dims, carte };
  });
}

let cubePromise: Promise<Row[]> | null = null;
export function useCube() {
  return useAsync<Row[]>(() => (cubePromise ??= loadCube(dataUrl("cube.parquet"))));
}

export function useRegionOf(dims: Dimensions | undefined) {
  return useMemo(() => {
    const m = new Map((dims?.departements ?? []).map((d) => [d.code_departement, d.code_region]));
    return (dep: string) => m.get(dep) ?? "NR";
  }, [dims]);
}

export const MEASURES = [
  "nb_marches", "montant_total", "nb_marches_montant", "poids_pme", "poids_categorie_connue", "montant_pme",
  "montant_categorie_connue", "nb_marches_offres", "somme_offres", "nb_offre_unique", "nb_sans_publicite",
  "nb_procedure_connue",
];
