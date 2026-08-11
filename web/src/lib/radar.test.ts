import { describe, expect, it } from "vitest";
import { FAMILLES, famille, joursRestants } from "./radar";

describe("radar", () => {
  it("chaque composante appartient à une seule famille", () => {
    const all = FAMILLES.flatMap((f) => f.comps);
    expect(new Set(all).size).toBe(all.length);
    expect(famille("cpv").id).toBe("pertinence");
    expect(famille("sortant").id).toBe("opportunite");
  });
  it("calcule les jours restants à partir de l'instantané", () => {
    expect(joursRestants("2026-11-13T12:00:00+00:00", "2026-11-01")).toBe(12);
  });
});
