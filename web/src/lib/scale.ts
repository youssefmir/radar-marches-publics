/** Seuils de classes par quantiles (k classes -> k-1 seuils). */
export function quantileBreaks(values: number[], k = 6): number[] {
  const v = values.filter((x) => Number.isFinite(x)).sort((a, b) => a - b);
  if (!v.length) return [];
  return Array.from({ length: k - 1 }, (_, i) => v[Math.floor(((i + 1) / k) * (v.length - 1))]);
}

export function classOf(x: number, breaks: number[]): number {
  let i = 0;
  while (i < breaks.length && x > breaks[i]) i++;
  return i;
}
