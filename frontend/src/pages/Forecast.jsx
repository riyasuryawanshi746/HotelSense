// Forecast.jsx - future forecast with its calibrated 80% range (from /api/forecast),
// plus the decision-support panel (from /api/decision).
import { useEffect, useState } from "react";
import { useApi } from "../api.js";
import { useSelection } from "../selection.jsx";
import { MODEL_COLORS, fmtNum, fmtValue } from "../format.js";
import Chart from "../components/Chart.jsx";
import Controls from "../components/Controls.jsx";
import DecisionPanel from "../components/DecisionPanel.jsx";
import { Async, Badge, Card } from "../components/ui.jsx";

// Builds the chart traces: recent history, the 80% band, the chosen model and (optionally) the others.
function forecastTraces(f, showOthers) {
  const chosen = f.models[f.chosen_model];
  const color = MODEL_COLORS[f.chosen_model] || "#0d9488";
  const traces = [
    { type: "scatter", mode: "lines", name: "Published (last 36 months)", x: f.history.dates, y: f.history.values, line: { color: "#334155", width: 2 } },
    // The band is two lines: the lower edge (invisible) and the upper edge filled down to it.
    { type: "scatter", mode: "lines", name: "80% lower", x: chosen.dates, y: chosen.lower, line: { width: 0 }, showlegend: false, hoverinfo: "skip" },
    {
      type: "scatter", mode: "lines", name: "80% range", x: chosen.dates, y: chosen.upper, fill: "tonexty",
      fillcolor: "rgba(13,148,136,0.18)", line: { width: 0 }, hoverinfo: "skip",
    },
    { type: "scatter", mode: "lines+markers", name: `${f.chosen_model} forecast`, x: chosen.dates, y: chosen.mean, line: { color, width: 3 } },
  ];
  if (showOthers) {
    for (const [name, m] of Object.entries(f.models)) {
      if (name === f.chosen_model) continue;
      traces.push({ type: "scatter", mode: "lines", name, x: m.dates, y: m.mean, line: { color: MODEL_COLORS[name], dash: "dot", width: 1.5 } });
    }
  }
  return traces;
}

function ReliabilityNote({ r }) {
  const low = r.level === "baseline-level";
  return (
    <div className={`headline ${low ? "headline-warn" : "headline-good"}`}>
      <Badge tone={low ? "warn" : "good"}>{low ? "No better than last year" : "Model-supported"}</Badge>
      <p>{r.text}</p>
    </div>
  );
}

function ForecastTable({ f, metric }) {
  const m = f.models[f.chosen_model];
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr><th>Month</th><th className="num">Forecast</th><th className="num">80% low</th><th className="num">80% high</th></tr>
        </thead>
        <tbody>
          {m.dates.map((d, i) => (
            <tr key={d}>
              <td>{d}</td>
              <td className="num">{fmtValue(m.mean[i], metric)}</td>
              <td className="num">{fmtValue(m.lower[i], metric)}</td>
              <td className="num">{fmtValue(m.upper[i], metric)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function Forecast() {
  const { segment, metric, horizon } = useSelection();
  const [model, setModel] = useState("best");
  const [showOthers, setShowOthers] = useState(false);
  const state = useApi("forecast", { segment, metric, horizon, model });

  // Go back to the recommended model whenever the series changes.
  useEffect(() => setModel("best"), [segment, metric]);

  return (
    <>
      <h1>Forecast</h1>
      <p className="lead">
        Forecast for {segment}, starting the month after the last published data. The shaded band is an 80% range
        built from the model's past backtest errors.
      </p>
      <Controls showHorizon />

      <Async state={state}>
        {(f) => (
          <Card title={`${f.label}: next ${f.horizon} months`}>
            <div className="controls">
              <label>
                Model
                <select value={model} onChange={(e) => setModel(e.target.value)}>
                  <option value="best">Best in backtest ({f.best_model})</option>
                  {Object.keys(f.models).map((name) => (
                    <option key={name} value={name}>{name}</option>
                  ))}
                </select>
              </label>
              <label className="check">
                <input type="checkbox" checked={showOthers} onChange={(e) => setShowOthers(e.target.checked)} />
                Show other models
              </label>
            </div>

            <ReliabilityNote r={f.reliability} />
            <Chart data={forecastTraces(f, showOthers)} layout={{ yaxis: { title: f.label } }} height={400} />
            <p className="muted small">
              Last published month: {f.last_observed}. Interval: {f.interval_method}. Backtest MAPE of the best model at
              this horizon: {fmtNum(f.reliability.mape)}%.
              {f.chosen_model !== f.best_model && ` You are viewing ${f.chosen_model}; the backtest winner is ${f.best_model}.`}
            </p>
            <ForecastTable f={f} metric={metric} />
          </Card>
        )}
      </Async>

      <DecisionPanel segment={segment} metric={metric} horizon={horizon} />
    </>
  );
}
