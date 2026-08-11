// Graphique ECharts (import modulaire) relié aux tokens CSS du thème courant.
import { useEffect, useRef } from "react";
import * as echarts from "echarts/core";
import { BarChart, LineChart } from "echarts/charts";
import { GridComponent, TooltipComponent, MarkLineComponent, MarkAreaComponent } from "echarts/components";
import { SVGRenderer } from "echarts/renderers";
import type { EChartsCoreOption } from "echarts/core";
import { cssVar, useReducedMotion, useTheme } from "../lib/theme";

echarts.use([BarChart, LineChart, GridComponent, TooltipComponent, MarkLineComponent, MarkAreaComponent, SVGRenderer]);

export interface ChartTokens {
  ink: string; ink2: string; muted: string; rule: string; paper: string;
  viz1: string; viz2: string; viz3: string; single: string; beacon: string;
  mono: string; sans: string;
}

export function tokens(): ChartTokens {
  return {
    ink: cssVar("--ink"), ink2: cssVar("--ink-2"), muted: cssVar("--muted"), rule: cssVar("--rule"),
    paper: cssVar("--paper"), viz1: cssVar("--viz-1"), viz2: cssVar("--viz-2"), viz3: cssVar("--viz-3"),
    single: cssVar("--single"), beacon: cssVar("--beacon"),
    mono: "Spline Sans Mono, monospace", sans: "Public Sans, sans-serif",
  };
}

/** Options communes : grille et axes en filets fins, infobulle sobre (valeur en premier). */
export function baseOption(t: ChartTokens): EChartsCoreOption {
  return {
    textStyle: { fontFamily: t.sans, color: t.ink2 },
    grid: { left: 8, right: 16, top: 16, bottom: 8, containLabel: true },
    tooltip: {
      trigger: "axis",
      axisPointer: { type: "line", lineStyle: { color: t.muted, width: 1 } },
      backgroundColor: t.paper, borderColor: t.ink, borderWidth: 1, padding: [6, 9],
      textStyle: { color: t.ink, fontFamily: t.sans, fontSize: 12 },
      extraCssText: "border-radius:0;box-shadow:none;",
    },
  };
}

export function axisStyle(t: ChartTokens) {
  return {
    axisLine: { lineStyle: { color: t.rule } },
    axisTick: { show: false },
    axisLabel: { color: t.muted, fontFamily: t.mono, fontSize: 11 },
    splitLine: { lineStyle: { color: t.rule, width: 1 } },
  };
}

export default function Chart({
  build, deps, className = "chart", label,
}: {
  build: (t: ChartTokens) => EChartsCoreOption;
  deps: unknown[];
  className?: string;
  label: string;
}) {
  const el = useRef<HTMLDivElement>(null);
  const inst = useRef<echarts.ECharts | null>(null);
  const [theme] = useTheme();
  const reduced = useReducedMotion();

  useEffect(() => {
    if (!el.current) return;
    inst.current = echarts.init(el.current, undefined, { renderer: "svg" });
    const ro = new ResizeObserver(() => inst.current?.resize());
    ro.observe(el.current);
    return () => {
      ro.disconnect();
      inst.current?.dispose();
    };
  }, []);

  useEffect(() => {
    const opt = build(tokens()) as Record<string, unknown>;
    inst.current?.setOption(
      { animation: !reduced, animationDuration: 500, animationEasing: "cubicOut", animationDurationUpdate: 300, ...opt },
      { notMerge: true },
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [theme, reduced, ...deps]);

  return <div ref={el} className={className} role="img" aria-label={label} />;
}
