#!/usr/bin/env node

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createSVGWindow } from "svgdom";
import rough from "roughjs";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(scriptDir, "..");
const summaryPath = path.join(
  repoRoot,
  "docs/benchmarks/usage-routing-v1/live-v6-summary.json",
);
const outputDir = path.join(repoRoot, "docs/assets");
const svgNamespace = "http://www.w3.org/2000/svg";
const summary = JSON.parse(fs.readFileSync(summaryPath, "utf8"));
const candidates = [
  { key: "luna", label: "Luna", color: "#0f8f9b" },
  { key: "terra", label: "Terra", color: "#a8b1bd" },
  { key: "sol", label: "Sol", color: "#4d5e73" },
];

const locales = {
  en: {
    suffix: "",
    weightedTitle: "Weighted token usage",
    weightedSubtitle: "Per 12-trial cohort · lower is better when quality is comparable",
    weightedDesc: "Weighted token usage across twelve trials for Luna, Terra, and Sol.",
    costTitle: "Equivalent cost",
    costSubtitle: "Per 12-trial cohort · model-specific native rollout pricing",
    costDesc: "Equivalent native rollout cost across twelve trials for Luna, Terra, and Sol.",
    timeTitle: "Median wall time",
    timeSubtitle: "Across 12 trials per candidate · lower is faster",
    timeDesc: "Median wall time across twelve trials for Luna, Terra, and Sol.",
    note: `Native rollout proxy · cohort ${summary.cohort}`,
    weightedName: "weighted-tokens",
    costName: "equivalent-cost",
    timeName: "median-wall-time",
  },
  "zh-TW": {
    suffix: "-zh-TW",
    weightedTitle: "加權 token 使用量",
    weightedSubtitle: "每組 12 次試驗 · 品質相近時越低越好",
    weightedDesc: "Luna、Terra 與 Sol 各執行 12 次試驗的加權 token 使用量。",
    costTitle: "等效成本",
    costSubtitle: "每組 12 次試驗 · 依 model 計算的 native rollout pricing",
    costDesc: "Luna、Terra 與 Sol 各執行 12 次試驗的等效 native rollout 成本。",
    timeTitle: "中位 wall time",
    timeSubtitle: "每個候選者 12 次試驗 · 越低越快",
    timeDesc: "Luna、Terra 與 Sol 各執行 12 次試驗的中位 wall time。",
    note: `Native rollout proxy · ${summary.cohort} cohort`,
    weightedName: "weighted-tokens",
    costName: "equivalent-cost",
    timeName: "median-wall-time",
  },
  "zh-CN": {
    suffix: "-zh-CN",
    weightedTitle: "加权 token 使用量",
    weightedSubtitle: "每组 12 次试验 · 质量相近时越低越好",
    weightedDesc: "Luna、Terra 与 Sol 各执行 12 次试验的加权 token 使用量。",
    costTitle: "等效成本",
    costSubtitle: "每组 12 次试验 · 按 model 计算的 native rollout pricing",
    costDesc: "Luna、Terra 与 Sol 各执行 12 次试验的等效 native rollout 成本。",
    timeTitle: "中位 wall time",
    timeSubtitle: "每个候选者 12 次试验 · 越低越快",
    timeDesc: "Luna、Terra 与 Sol 各执行 12 次试验的中位 wall time。",
    note: `Native rollout proxy · ${summary.cohort} cohort`,
    weightedName: "weighted-tokens",
    costName: "equivalent-cost",
    timeName: "median-wall-time",
  },
};

const style = `
  .bg { fill: #fffdf8; }
  .grid { stroke: #d8d2c6; stroke-width: 1; }
  .axis { stroke: #4d5968; stroke-width: 1.6; }
  .title { fill: #202a38; font: 700 29px ui-sans-serif, system-ui, sans-serif; letter-spacing: -0.5px; }
  .subtitle { fill: #697586; font: 400 15px ui-sans-serif, system-ui, sans-serif; }
  .tick { fill: #697586; font: 400 13px ui-sans-serif, system-ui, sans-serif; }
  .name { fill: #263243; font: 600 16px ui-sans-serif, system-ui, sans-serif; }
  .value { fill: #202a38; font: 700 18px ui-sans-serif, system-ui, sans-serif; }
  .note { fill: #697586; font: 400 12px ui-sans-serif, system-ui, sans-serif; }
`;

function createSvg(width, height, title, description, seed) {
  const window = createSVGWindow();
  const document = window.document;
  const svg = document.createElementNS(svgNamespace, "svg");
  svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
  svg.setAttribute("role", "img");
  svg.setAttribute("aria-labelledby", "title desc");

  for (const [tag, id, content] of [
    ["title", "title", title],
    ["desc", "desc", description],
  ]) {
    const element = document.createElementNS(svgNamespace, tag);
    element.setAttribute("id", id);
    element.textContent = content;
    svg.appendChild(element);
  }

  const styleElement = document.createElementNS(svgNamespace, "style");
  styleElement.textContent = style;
  svg.appendChild(styleElement);

  const background = document.createElementNS(svgNamespace, "rect");
  background.setAttribute("class", "bg");
  background.setAttribute("width", width);
  background.setAttribute("height", height);
  svg.appendChild(background);

  return { document, svg, rough: rough.svg(svg, { seed }) };
}

function appendText(document, svg, value, x, y, className, attributes = {}) {
  const element = document.createElementNS(svgNamespace, "text");
  element.setAttribute("x", x);
  element.setAttribute("y", y);
  element.setAttribute("class", className);
  for (const [key, attrValue] of Object.entries(attributes)) {
    element.setAttribute(key, attrValue);
  }
  element.textContent = value;
  svg.appendChild(element);
}

function appendLine(chart, x1, y1, x2, y2, options = {}) {
  chart.svg.appendChild(
    chart.rough.line(x1, y1, x2, y2, {
      roughness: 0.8,
      bowing: 1.2,
      stroke: "#d8d2c6",
      strokeWidth: 1,
      seed: options.seed ?? 1,
      ...options,
    }),
  );
}

function appendBar(chart, x, y, width, height, color, seed) {
  chart.svg.appendChild(
    chart.rough.rectangle(x, y, width, height, {
      roughness: 1.1,
      bowing: 1.4,
      stroke: color,
      strokeWidth: 1.8,
      fill: color,
      fillStyle: "hachure",
      hachureAngle: 60,
      hachureGap: 8,
      fillWeight: 1.1,
      seed,
    }),
  );
}

function writeChart(svg, fileName) {
  fs.writeFileSync(path.join(outputDir, fileName), `${svg.outerHTML}\n`);
}

function createWeightedTokensChart(locale) {
  const chart = createSvg(960, 480, locale.weightedTitle, locale.weightedDesc, 1101);
  const max = 800000;
  appendText(chart.document, chart.svg, locale.weightedTitle, 72, 58, "title");
  appendText(chart.document, chart.svg, locale.weightedSubtitle, 72, 84, "subtitle");
  appendLine(chart, 112, 390, 900, 390, { stroke: "#4d5968", strokeWidth: 1.6, seed: 1102 });
  for (const [index, value] of [0, 200000, 400000, 600000, 800000].entries()) {
    const y = 390 - (value / max) * 272;
    if (value > 0) appendLine(chart, 112, y, 900, y, { seed: 1103 + index });
    appendText(chart.document, chart.svg, value === 0 ? "0" : `${value / 1000}k`, 96, y + 4, "tick", { "text-anchor": "end" });
  }
  candidates.forEach((candidate, index) => {
    const value = summary.candidate_aggregates[candidate.key].weighted_tokens;
    const height = (value / max) * 272;
    const x = 214 + index * 200;
    appendBar(chart, x, 390 - height, 132, height, candidate.color, 1110 + index);
    appendText(chart.document, chart.svg, `${Math.round(value / 1000)}k`, x + 66, 390 - height - 16, "value", { "text-anchor": "middle" });
    appendText(chart.document, chart.svg, candidate.label, x + 66, 424, "name", { "text-anchor": "middle" });
  });
  appendText(chart.document, chart.svg, locale.note, 112, 458, "note");
  writeChart(chart.svg, `v6-${locale.weightedName}${locale.suffix}.svg`);
}

function createCostChart(locale) {
  const chart = createSvg(960, 480, locale.costTitle, locale.costDesc, 1201);
  const max = 3;
  appendText(chart.document, chart.svg, locale.costTitle, 72, 58, "title");
  appendText(chart.document, chart.svg, locale.costSubtitle, 72, 84, "subtitle");
  appendLine(chart, 112, 390, 900, 390, { stroke: "#4d5968", strokeWidth: 1.6, seed: 1202 });
  for (const [index, value] of [0, 1, 2, 3].entries()) {
    const y = 390 - (value / max) * 264;
    if (value > 0) appendLine(chart, 112, y, 900, y, { seed: 1203 + index });
    appendText(chart.document, chart.svg, `$${value}`, 96, y + 4, "tick", { "text-anchor": "end" });
  }
  candidates.forEach((candidate, index) => {
    const value = summary.candidate_aggregates[candidate.key].equivalent_cost_usd;
    const height = (value / max) * 264;
    const x = 214 + index * 200;
    appendBar(chart, x, 390 - height, 132, height, candidate.color, 1210 + index);
    appendText(chart.document, chart.svg, `$${value.toFixed(2)}`, x + 66, 390 - height - 16, "value", { "text-anchor": "middle" });
    appendText(chart.document, chart.svg, candidate.label, x + 66, 424, "name", { "text-anchor": "middle" });
  });
  appendText(chart.document, chart.svg, locale.note, 112, 458, "note");
  writeChart(chart.svg, `v6-${locale.costName}${locale.suffix}.svg`);
}

function createTimeChart(locale) {
  const chart = createSvg(960, 420, locale.timeTitle, locale.timeDesc, 1301);
  const min = 25;
  const max = 45;
  const xFor = (value) => 210 + ((value - min) / (max - min)) * 630;
  appendText(chart.document, chart.svg, locale.timeTitle, 72, 58, "title");
  appendText(chart.document, chart.svg, locale.timeSubtitle, 72, 84, "subtitle");
  appendLine(chart, 210, 136, 840, 136, { stroke: "#4d5968", strokeWidth: 1.6, seed: 1302 });
  for (const [index, value] of [25, 30, 35, 40, 45].entries()) {
    const x = xFor(value);
    if (value > 25) appendLine(chart, x, 136, x, 322, { seed: 1303 + index });
    appendText(chart.document, chart.svg, `${value}s`, x, 118, "tick", { "text-anchor": "middle" });
  }
  candidates.forEach((candidate, index) => {
    const y = 176 + index * 62;
    const value = summary.candidate_aggregates[candidate.key].median_wall_seconds;
    appendText(chart.document, chart.svg, candidate.label, 92, y + 6, "name");
    appendLine(chart, 210, y, 840, y, { seed: 1310 + index });
    chart.svg.appendChild(
      chart.rough.ellipse(xFor(value), y, 20, 20, {
        roughness: 1.1,
        stroke: candidate.color,
        strokeWidth: 1.8,
        fill: candidate.color,
        fillStyle: "solid",
        seed: 1320 + index,
      }),
    );
    appendText(chart.document, chart.svg, `${value.toFixed(2)}s`, xFor(value) + 20, y + 6, "value");
  });
  appendText(chart.document, chart.svg, locale.note, 72, 382, "note");
  writeChart(chart.svg, `v6-${locale.timeName}${locale.suffix}.svg`);
}

for (const locale of Object.values(locales)) {
  createWeightedTokensChart(locale);
  createCostChart(locale);
  createTimeChart(locale);
}
