// frontend/src/components/visualizations/ForecastChart.tsx
//
// HNDL Exposure Forecast Chart — Chart.js P10/P50/P90 bands.
//
// Renders three migration scenarios with fill-between band shading:
//   • Do Nothing      — steep upward trend (red family)
//   • Phased          — moderate growth then plateau (orange)
//   • Emergency       — rapid drop to nearly zero (green)
//
// Fill-between shading is achieved via Chart.js filler plugin with
// dataset stacking: P10 fills to P90 background, P50 is the median line.
//
// Uses Chart.js v4 with react-chartjs-2 wrapper.

import {
  CategoryScale,
  Chart as ChartJS,
  Filler,
  Legend,
  LinearScale,
  LineElement,
  PointElement,
  Title,
  Tooltip,
} from "chart.js";
import annotationPlugin from "chartjs-plugin-annotation";
import React, { useMemo, useRef, useState } from "react";
import { Line } from "react-chartjs-2";
import type { ForecastScenario } from "../../types";

// Register Chart.js plugins
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  annotationPlugin,
);

// ── Scenario configs ──────────────────────────────────────────────────────────

interface ScenarioConfig {
  id:         string;
  label:      string;
  baseColor:  string;   // CSS hex/rgba — used for borders
  fillColor:  string;   // rgba with alpha for band fill
  lineStyle:  "solid" | "dashed";
  description: string;
}

const SCENARIOS: ScenarioConfig[] = [
  {
    id:          "do_nothing",
    label:       "Do Nothing",
    baseColor:   "rgb(239,68,68)",
    fillColor:   "rgba(239,68,68,0.12)",
    lineStyle:   "solid",
    description: "No PQC migration; HNDL exposure grows as CRQC arrival approaches",
  },
  {
    id:          "phased",
    label:       "Phased Migration",
    baseColor:   "rgb(249,115,22)",
    fillColor:   "rgba(249,115,22,0.12)",
    lineStyle:   "dashed",
    description: "Systematic hybrid KEM rollout over 3–5 years",
  },
  {
    id:          "emergency",
    label:       "Emergency Migration",
    baseColor:   "rgb(34,197,94)",
    fillColor:   "rgba(34,197,94,0.12)",
    lineStyle:   "dashed",
    description: "Accelerated full PQC migration within 18 months",
  },
];

// ── Props ─────────────────────────────────────────────────────────────────────

interface ForecastChartProps {
  scenarios: ForecastScenario[];   // Actual forecast data from the API
  /** Vertical threshold line — e.g., P50 CRQC arrival year */
  crqcArrivalYear?: number;
  /** Risk threshold — horizontal line at this HNDL score */
  riskThreshold?: number;
  height?: number;
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function generateSyntheticScenario(
  id: string,
  bandCount: number,
  startYear: number,
): ForecastScenario["bands"] {
  return Array.from({ length: bandCount }, (_, i) => {
    const year  = startYear + Math.floor(i / 4);
    const month = ((i % 4) * 3 + 1).toString().padStart(2, "0");
    const date  = `${year}-${month}-01`;

    let p50: number;
    if (id === "do_nothing") {
      // Exponential growth
      p50 = Math.min(10, 3.5 + i * 0.22);
    } else if (id === "phased") {
      // Slow growth then plateau
      p50 = Math.min(7, 4.0 + i * 0.10 - Math.max(0, i - 12) * 0.08);
    } else {
      // Emergency — rapid decline
      p50 = Math.max(0.5, 5.5 - i * 0.28);
    }
    return {
      date,
      p10: Math.max(0, Math.round((p50 - 0.8) * 100) / 100),
      p50: Math.round(p50 * 100) / 100,
      p90: Math.min(10, Math.round((p50 + 1.2) * 100) / 100),
    };
  });
}

// ── Main Component ────────────────────────────────────────────────────────────

export default function ForecastChart({
  scenarios,
  crqcArrivalYear = 2033,
  riskThreshold   = 7.0,
  height          = 420,
}: ForecastChartProps) {
  const [activeScenarios, setActiveScenarios] = useState<Set<string>>(
    new Set(SCENARIOS.map((s) => s.id))
  );

  // Use provided scenarios; fall back to synthetic if empty
  const effectiveScenarios = useMemo<ForecastScenario[]>(() => {
    if (scenarios && scenarios.length > 0) return scenarios;
    const startYear = new Date().getFullYear();
    return SCENARIOS.map((sc) => ({
      label:  sc.label,
      color:  sc.baseColor,
      bands:  generateSyntheticScenario(sc.id, 20, startYear),
    }));
  }, [scenarios]);

  // Build Chart.js datasets
  const { labels, datasets } = useMemo(() => {
    const allDates = effectiveScenarios[0]?.bands.map((b) => {
      const d = new Date(b.date);
      return d.toLocaleDateString("en-US", { month: "short", year: "numeric" });
    }) ?? [];

    const ds: ChartJS["data"]["datasets"] = [];

    effectiveScenarios.forEach((scenario, idx) => {
      const sc = SCENARIOS[idx] ?? SCENARIOS[0];
      if (!activeScenarios.has(sc.id)) return;

      const p10 = scenario.bands.map((b) => b.p10);
      const p50 = scenario.bands.map((b) => b.p50);
      const p90 = scenario.bands.map((b) => b.p90);

      const dash = sc.lineStyle === "dashed" ? [6, 3] : [];

      // P90 upper band (filled down to P10)
      ds.push({
        label:           `${sc.label} — P90`,
        data:            p90,
        borderColor:     sc.baseColor,
        borderWidth:     1,
        borderDash:      dash,
        backgroundColor: sc.fillColor,
        fill:            `+1`,          // Fill to next dataset (P10)
        pointRadius:     0,
        tension:         0.4,
      } as any);

      // P10 lower band (invisible line; provides fill boundary)
      ds.push({
        label:           `${sc.label} — P10`,
        data:            p10,
        borderColor:     "transparent",
        borderWidth:     0,
        backgroundColor: "transparent",
        fill:            false,
        pointRadius:     0,
        tension:         0.4,
      } as any);

      // P50 median line (prominent)
      ds.push({
        label:       `${sc.label} — P50 (median)`,
        data:        p50,
        borderColor: sc.baseColor,
        borderWidth: 2.5,
        borderDash:  dash,
        backgroundColor: "transparent",
        fill:        false,
        pointRadius: (ctx: any) => (ctx.dataIndex % 4 === 0 ? 3 : 0),
        pointBackgroundColor: sc.baseColor,
        tension:     0.4,
      } as any);
    });

    return { labels: allDates, datasets: ds };
  }, [effectiveScenarios, activeScenarios]);

  // Chart.js options
  const options = useMemo(
    () => ({
      responsive:          true,
      maintainAspectRatio: false,
      interaction: {
        mode:      "index" as const,
        intersect: false,
      },
      scales: {
        x: {
          grid:     { color: "rgba(255,255,255,0.05)" },
          ticks:    { color: "#6b7280", font: { size: 11 }, maxRotation: 0 },
          border:   { color: "#374151" },
        },
        y: {
          min:  0,
          max:  10.5,
          grid: { color: "rgba(255,255,255,0.05)" },
          ticks: {
            color: "#6b7280",
            font:  { size: 11 },
            callback: (v: number) => `${v.toFixed(1)}`,
          },
          border: { color: "#374151" },
          title: {
            display: true,
            text:    "HNDL Exposure Score",
            color:   "#9ca3af",
            font:    { size: 12 },
          },
        },
      },
      plugins: {
        legend: {
          position: "top" as const,
          labels: {
            color:    "#d1d5db",
            boxWidth: 20,
            font:     { size: 11 },
            filter:   (item: { text: string }) => item.text.includes("P50"),
          },
        },
        tooltip: {
          backgroundColor: "rgba(17,24,39,0.95)",
          borderColor:     "#374151",
          borderWidth:     1,
          titleColor:      "#f9fafb",
          bodyColor:       "#9ca3af",
          callbacks: {
            label: (ctx: any) => {
              if (!ctx.dataset.label?.includes("P50")) return null;
              const i = ctx.dataIndex;
              const p50 = ctx.raw as number;
              return ` ${ctx.dataset.label.split("—")[0].trim()}: ${p50.toFixed(2)}`;
            },
          },
        },
        annotation: {
          annotations: {
            // Vertical line at CRQC arrival year
            crqcLine: {
              type:        "line",
              scaleID:     "x",
              value:       labels.find((l: string) => l.includes(String(crqcArrivalYear))),
              borderColor: "rgba(167,139,250,0.7)",
              borderWidth: 2,
              borderDash:  [4, 4],
              label: {
                display:         true,
                content:         `CRQC P50 (${crqcArrivalYear})`,
                color:           "#a78bfa",
                backgroundColor: "rgba(17,24,39,0.9)",
                font:            { size: 10, weight: "bold" as const },
                position:        "start",
              },
            },
            // Horizontal risk threshold line
            riskLine: {
              type:        "line",
              scaleID:     "y",
              value:       riskThreshold,
              borderColor: "rgba(252,165,165,0.6)",
              borderWidth: 1.5,
              borderDash:  [3, 3],
              label: {
                display:         true,
                content:         `Risk threshold (${riskThreshold})`,
                color:           "#fca5a5",
                backgroundColor: "rgba(17,24,39,0.9)",
                font:            { size: 9 },
                position:        "end",
              },
            },
          },
        },
      },
    }),
    [labels, crqcArrivalYear, riskThreshold]
  );

  function toggleScenario(id: string) {
    setActiveScenarios((prev) => {
      const next = new Set(prev);
      if (next.has(id) && next.size > 1) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  return (
    <div className="flex flex-col w-full bg-gray-900 rounded-2xl border border-gray-800 overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-3 border-b border-gray-800">
        <div>
          <h3 className="text-sm font-bold text-white">📈 HNDL Exposure Forecast</h3>
          <p className="text-xs text-gray-500 mt-0.5">P10 / P50 / P90 bands · Shaded = uncertainty range</p>
        </div>
        {/* Scenario toggles */}
        <div className="flex gap-2">
          {SCENARIOS.map((sc) => (
            <button
              key={sc.id}
              onClick={() => toggleScenario(sc.id)}
              className={`px-3 py-1 text-xs rounded-full font-semibold border transition ${
                activeScenarios.has(sc.id)
                  ? "border-transparent text-white"
                  : "border-gray-700 text-gray-500 bg-transparent"
              }`}
              style={
                activeScenarios.has(sc.id)
                  ? { background: sc.baseColor + "33", borderColor: sc.baseColor, color: sc.baseColor }
                  : {}
              }
              title={sc.description}
            >
              {sc.label}
            </button>
          ))}
        </div>
      </div>

      {/* Chart */}
      <div className="px-5 py-4" style={{ height }}>
        <Line data={{ labels, datasets }} options={options as any} />
      </div>

      {/* Legend footnotes */}
      <div className="px-5 pb-4 flex flex-wrap gap-4 text-xs text-gray-500">
        <span>
          <span className="text-purple-400">━ ━</span> CRQC median arrival ({crqcArrivalYear})
        </span>
        <span>
          <span className="text-red-300">─ ─</span> Risk threshold ({riskThreshold})
        </span>
        <span>Shaded bands = P10–P90 uncertainty interval</span>
      </div>
    </div>
  );
}
