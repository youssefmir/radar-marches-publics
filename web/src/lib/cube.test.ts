import { describe, expect, it } from "vitest";
import { aggregate, metric } from "./cube";
import type { Catalog } from "./data";

const catalog: Catalog = {
  periode: "",
  dimensions: {},
  measures: {},
  metrics: {
    nombre_marches: { label: "", type: "ratio", numerator: "nb_marches", format: "entier", definition: "" },
    taux_offre_unique: { label: "", type: "ratio", numerator: "nb_offre_unique", denominator: "nb_marches_offres", format: "pourcentage", definition: "" },
    montant_median: { label: "", type: "sql", format: "euros", definition: "" },
  },
};
const rows = [
  { annee: 2024, departement: "75", nb_marches: 10, nb_offre_unique: 2, nb_marches_offres: 8 },
  { annee: 2024, departement: "69", nb_marches: 5, nb_offre_unique: null, nb_marches_offres: 2 },
  { annee: 2025, departement: "75", nb_marches: 4, nb_offre_unique: 1, nb_marches_offres: 4 },
];
const measures = ["nb_marches", "nb_offre_unique", "nb_marches_offres"];

describe("agrégation du cube", () => {
  it("somme les mesures additives sans filtre", () => {
    const s = aggregate(rows, measures).get("*")!;
    expect(s.nb_marches).toBe(19);
    expect(metric(catalog, "taux_offre_unique", s)).toBeCloseTo(3 / 14);
  });
  it("applique les filtres et le regroupement", () => {
    const g = aggregate(rows, measures, { annee: [2024] }, (r) => String(r.departement));
    expect([...g.keys()].sort()).toEqual(["69", "75"]);
    expect(metric(catalog, "nombre_marches", g.get("75"))).toBe(10);
    expect(metric(catalog, "taux_offre_unique", g.get("69"))).toBe(0);
  });
  it("filtre par région via la table de correspondance", () => {
    const regionOf = (d: string) => (d === "75" ? "11" : "84");
    const s = aggregate(rows, measures, { region: ["84"] }, undefined, regionOf).get("*")!;
    expect(s.nb_marches).toBe(5);
  });
  it("renvoie null pour une métrique non additive ou un dénominateur nul", () => {
    expect(metric(catalog, "montant_median", { nb_marches: 1 })).toBeNull();
    expect(metric(catalog, "taux_offre_unique", { nb_offre_unique: 0, nb_marches_offres: 0 })).toBeNull();
  });
});
