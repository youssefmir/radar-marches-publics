// Fabriques d'options ECharts conformes aux règles de visualisation du projet :
// une seule série par graphique (une couleur), un seul axe, filets fins, infobulle au survol.
import type { EChartsCoreOption } from "echarts/core";
import { axisStyle, baseOption, type ChartTokens } from "./Chart";

export interface Datum { label: string; value: number | null; note?: string }

export function hbar(t: ChartTokens, data: Datum[], fmt: (x: number) => string, color = t.viz1, labelWidth = 210): EChartsCoreOption {
  const d = [...data].reverse();
  const ax = axisStyle(t);
  return {
    ...baseOption(t),
    tooltip: { ...(baseOption(t).tooltip as object), trigger: "item",
      formatter: (p: { name: string; value: number }) => `<b style="font-family:${t.mono}">${fmt(p.value)}</b><br/><span style="color:${t.muted}">${p.name}</span>` },
    grid: { left: 8, right: 56, top: 4, bottom: 4, containLabel: true },
    // Valeurs portées par les étiquettes directes : pas de graduations chiffrées sur l'axe.
    xAxis: { type: "value", ...ax, axisLabel: { show: false }, splitNumber: 3 },
    yAxis: { type: "category", data: d.map((x) => x.label), ...ax, splitLine: { show: false },
      axisLabel: { color: t.ink2, fontFamily: t.sans, fontSize: 12, width: labelWidth, overflow: "truncate" } },
    series: [{
      type: "bar", data: d.map((x) => x.value), barMaxWidth: 14, itemStyle: { color, borderRadius: [0, 2, 2, 0] },
      emphasis: { itemStyle: { color: t.ink } },
      label: { show: true, position: "right", color: t.muted, fontFamily: t.mono, fontSize: 11, formatter: (p: { value: number }) => fmt(p.value) },
    }],
  };
}

export function vbar(t: ChartTokens, data: Datum[], fmt: (x: number) => string, color = t.viz1, markBefore?: string): EChartsCoreOption {
  const ax = axisStyle(t);
  return {
    ...baseOption(t),
    tooltip: { ...(baseOption(t).tooltip as object), axisPointer: { type: "shadow", shadowStyle: { color: t.rule, opacity: 0.4 } },
      formatter: (ps: { name: string; value: number }[]) => `<b style="font-family:${t.mono}">${fmt(ps[0].value)}</b><br/><span style="color:${t.muted}">${ps[0].name}</span>` },
    xAxis: { type: "category", data: data.map((x) => x.label), ...ax, splitLine: { show: false } },
    yAxis: { type: "value", ...ax, axisLabel: { ...ax.axisLabel, formatter: (v: number) => fmt(v) }, splitNumber: 4 },
    series: [{
      type: "bar", data: data.map((x) => x.value), barMaxWidth: 30, itemStyle: { color, borderRadius: [2, 2, 0, 0] },
      emphasis: { itemStyle: { color: t.ink } },
      markArea: markBefore ? { silent: true, itemStyle: { color: t.rule, opacity: 0.35 },
        label: { color: t.muted, fontFamily: t.mono, fontSize: 10, position: "insideTop" },
        data: [[{ name: "Nb d'offres peu renseigné", xAxis: data[0]?.label }, { xAxis: markBefore }]] } : undefined,
    }],
  };
}

export function line(t: ChartTokens, data: Datum[], fmt: (x: number) => string, color = t.viz1, markBefore?: string): EChartsCoreOption {
  const ax = axisStyle(t);
  return {
    ...baseOption(t),
    tooltip: { ...(baseOption(t).tooltip as object),
      formatter: (ps: { name: string; value: number }[]) => `<b style="font-family:${t.mono}">${fmt(ps[0].value)}</b><br/><span style="color:${t.muted}">${ps[0].name}</span>` },
    xAxis: { type: "category", data: data.map((x) => x.label), ...ax, splitLine: { show: false }, boundaryGap: false },
    yAxis: { type: "value", ...ax, axisLabel: { ...ax.axisLabel, formatter: (v: number) => fmt(v) }, splitNumber: 4 },
    series: [{
      type: "line", data: data.map((x) => x.value), lineStyle: { width: 2, color }, itemStyle: { color, borderColor: t.paper, borderWidth: 2 },
      symbol: "circle", symbolSize: 8, showSymbol: true,
      markArea: markBefore ? { silent: true, itemStyle: { color: t.rule, opacity: 0.35 },
        label: { color: t.muted, fontFamily: t.mono, fontSize: 10, position: "insideTop" },
        data: [[{ name: "Nb d'offres peu renseigné", xAxis: data[0]?.label }, { xAxis: markBefore }]] } : undefined,
    }],
  };
}
