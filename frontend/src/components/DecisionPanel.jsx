// DecisionPanel.jsx - shows the rule-based planning signals from /api/decision.
// All text and numbers are produced by backend/decision_support.py from the real forecasts.
import { useApi } from "../api.js";
import { Async, Badge, Card } from "./ui.jsx";

const AREA_LABEL = {
  forecast: "Outlook",
  capacity: "Capacity",
  staffing: "Staffing",
  pricing: "Pricing",
};

const METRIC_SHORT = { occupancy: "Occupancy", adr: "ADR", revpar: "RevPAR" };

// Labels for every status / reason the backend can return (decision_support.STATUSES / REASONS).
// scripts/06_test_decision_rules.py checks that these keys match the backend exactly.
const STATUS_LABEL = {
  increase: "Supported increase",
  decrease: "Supported decrease",
  inconclusive: "Inconclusive",
};
const REASON_LABEL = {
  supported: "larger than the uncertainty and the planning threshold",
  within_uncertainty: "within the forecast uncertainty",
  below_materiality: "beyond the uncertainty but below the planning threshold",
  baseline_forecast: "forecast is last year's values (no model beat the baseline)",
  missing_data: "missing data",
  zero_baseline: "last year's level is zero",
};

// Change of the forecast average vs the same months last year, for all three metrics.
function ChangeTable({ changes }) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Metric</th>
            <th className="num">Forecast avg</th>
            <th className="num">Same months last year</th>
            <th className="num">Change</th>
            <th className="num">± 80% uncertainty</th>
            <th className="num">Planning threshold</th>
            <th>Result</th>
          </tr>
        </thead>
        <tbody>
          {Object.entries(changes).map(([m, c]) => (
            <tr key={m}>
              <td>{METRIC_SHORT[m] || m}</td>
              <td className="num">{c.forecast_mean ?? "–"}</td>
              <td className="num">{c.last_year_mean ?? "–"}</td>
              <td className="num">{c.delta == null ? "–" : `${c.delta > 0 ? "+" : ""}${c.delta} ${c.unit}`}</td>
              <td className="num">{c.uncertainty == null ? "–" : `±${c.uncertainty} ${c.unit}`}</td>
              <td className="num">{`${c.materiality} ${c.unit}`}</td>
              <td>
                <Badge tone={c.status === "inconclusive" ? "neutral" : "warn"}>{STATUS_LABEL[c.status] || c.status}</Badge>{" "}
                <span className="muted small">{REASON_LABEL[c.reason] || c.reason}</span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function DecisionPanel({ segment, metric, horizon }) {
  const state = useApi("decision", { segment, metric, horizon });

  return (
    <Card
      title="Decision support"
      subtitle="Planning signals calculated from the forecasts below. They are prompts for discussion, not guaranteed decisions."
    >
      <Async state={state}>
        {(d) => {
          const lowConfidence = d.reliability.level === "baseline-level";
          return (
            <>
              <div className={`headline ${lowConfidence ? "headline-warn" : "headline-good"}`}>
                <Badge tone={lowConfidence ? "warn" : "good"}>
                  {lowConfidence ? "Low confidence" : "Model-supported"}
                </Badge>
                <p>{d.headline}</p>
              </div>

              <ul className="signals">
                {d.signals.map((s, i) => (
                  <li key={i} className={`signal signal-${s.level}`}>
                    <div className="signal-head">
                      <Badge tone={s.level === "watch" ? "warn" : "info"}>{AREA_LABEL[s.area] || s.area}</Badge>
                      <strong>{s.title}</strong>
                    </div>
                    <p>{s.text}</p>
                  </li>
                ))}
              </ul>

              <h3>Change vs the same months last year (average over the horizon)</h3>
              <ChangeTable changes={d.changes} />
              <p className="muted small">
                Uncertainty: {d.changes[d.metric]?.uncertainty_method}. A result is "supported" only if the change is
                larger than this uncertainty and at least the planning threshold.
              </p>

              <h3>Caveats</h3>
              <ul className="caveats">
                {d.caveats.map((c, i) => (
                  <li key={i}>{c}</li>
                ))}
              </ul>

              <p className="muted small">
                Models used:{" "}
                {Object.entries(d.models_used)
                  .map(([m, model]) => `${METRIC_SHORT[m] || m}: ${model}`)
                  .join(" · ")}
                . Occupancy normal range for this segment (P10–P90, excluding COVID months):{" "}
                {d.normal_range_occupancy.p10}% to {d.normal_range_occupancy.p90}%.
              </p>
            </>
          );
        }}
      </Async>
    </Card>
  );
}
