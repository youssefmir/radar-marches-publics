// Agrégation côté navigateur du cube de mesures additives, puis calcul des ratios
// définis dans la couche sémantique (metrics.json, généré depuis semantic/metrics.yml).
import type { Catalog } from "./data";

export type Row = Record<string, string | number | null>;
export type Filters = Partial<Record<string, (string | number)[]>>;
export type Sums = Record<string, number>;

export const DIMS = ["annee", "departement", "division_cpv", "procedure", "categorie_acheteur", "type_marche"] as const;

export function matches(row: Row, filters: Filters, regionOf?: (dep: string) => string): boolean {
  for (const [dim, values] of Object.entries(filters)) {
    if (!values || values.length === 0) continue;
    const v = dim === "region" ? regionOf?.(String(row.departement)) : row[dim];
    if (!values.map(String).includes(String(v))) return false;
  }
  return true;
}

export function aggregate(
  rows: Row[],
  measures: string[],
  filters: Filters = {},
  groupBy?: (row: Row) => string,
  regionOf?: (dep: string) => string,
): Map<string, Sums> {
  const out = new Map<string, Sums>();
  for (const row of rows) {
    if (!matches(row, filters, regionOf)) continue;
    const key = groupBy ? groupBy(row) : "*";
    let s = out.get(key);
    if (!s) {
      s = Object.fromEntries(measures.map((m) => [m, 0]));
      out.set(key, s);
    }
    for (const m of measures) s[m] += Number(row[m] ?? 0);
  }
  return out;
}

export function metric(catalog: Catalog, name: string, sums: Sums | undefined): number | null {
  const def = catalog.metrics[name];
  if (!def || def.type !== "ratio" || !sums) return null;
  const num = sums[def.numerator!];
  if (!def.denominator) return num;
  const den = sums[def.denominator];
  return den > 0 ? num / den : null;
}

export async function loadCube(url: string): Promise<Row[]> {
  const { parquetRead } = await import("hyparquet");
  const buf = await (await fetch(url)).arrayBuffer();
  return new Promise((resolve, reject) => {
    parquetRead({ file: buf, rowFormat: "object", onComplete: (rows) => resolve(rows as unknown as Row[]) }).catch(reject);
  });
}
