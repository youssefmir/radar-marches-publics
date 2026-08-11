import { describe, expect, it } from "vitest";
import { classOf, quantileBreaks } from "./scale";

describe("classes de la carte", () => {
  it("découpe en 6 classes par quantiles", () => {
    const b = quantileBreaks(Array.from({ length: 60 }, (_, i) => i));
    expect(b).toHaveLength(5);
    expect(classOf(0, b)).toBe(0);
    expect(classOf(59, b)).toBe(5);
  });
  it("ignore les valeurs non finies", () => {
    expect(quantileBreaks([NaN, Infinity])).toEqual([]);
  });
});
