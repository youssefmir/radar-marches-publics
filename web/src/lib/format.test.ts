import { describe, expect, it } from "vitest";
import { dateFr, euros, pct, entier } from "./format";

const nbsp = (s: string) => s.replace(/[  ]/g, " ");

describe("formats français", () => {
  it("abrège les montants", () => {
    expect(nbsp(euros(1_234_000_000))).toBe("1,2 Md€");
    expect(nbsp(euros(340_000_000))).toBe("340 M€");
    expect(nbsp(euros(85_400))).toBe("85 k€");
  });
  it("écrit le premier du mois « 1er »", () => {
    expect(dateFr("2026-11-01")).toBe("1er novembre 2026");
    expect(dateFr("2026-11-13")).toBe("13 novembre 2026");
  });
  it("formate pourcentages et entiers", () => {
    expect(nbsp(pct(0.2366))).toBe("23,7 %");
    expect(nbsp(entier(1264114))).toBe("1 264 114");
    expect(pct(null)).toBe("–");
  });
});
