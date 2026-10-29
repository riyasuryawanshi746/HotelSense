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
