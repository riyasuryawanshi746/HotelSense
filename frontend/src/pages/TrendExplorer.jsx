// TrendExplorer.jsx - history, seasonality, STL decomposition and stationarity tests
// for one segment and metric (from /api/history and /api/decomposition).
import { useApi } from "../api.js";
import { useSelection } from "../selection.jsx";
import { MONTH_NAMES, fmtNum, fmtP, fmtSigned, fmtValue } from "../format.js";
import Chart from "../components/Chart.jsx";
import Controls from "../components/Controls.jsx";
import { Async, Card, Stat } from "../components/ui.jsx";

// Shaded rectangles for COVID and the World Cup, drawn behind the history line.
function eventShapes(events) {
  return events.map((e) => ({
    type: "rect", xref: "x", yref: "paper", x0: e.start, x1: e.end, y0: 0, y1: 1,
    fillcolor: e.label.startsWith("COVID") ? "rgba(239,68,68,0.10)" : "rgba(59,130,246,0.15)",
    line: { width: 0 }, layer: "below",
  }));
}

function eventLabels(events) {
  return events.map((e) => ({
    x: e.start, xref: "x", y: 1, yref: "paper", text: e.label, showarrow: false,
    xanchor: "left", yanchor: "bottom", font: { size: 11, color: "#64748b" },
  }));
}

function HistoryCard({ h, metric }) {
  const s = h.stats;
  return (
    <Card title={`${h.label}: full history`} subtitle="Shaded: COVID-19 (red) and the FIFA World Cup (blue).">
      <div className="stats">
        <Stat label={`Latest (${s.latest_date})`} value={fmtValue(s.latest, metric)} />
        <Stat label="Last 12 months average" value={fmtValue(s.last12_mean, metric)} hint={`${fmtSigned(s.yoy_change_pct)} vs previous 12 months`} />
        <Stat label="Mean (all months)" value={fmtValue(s.mean, metric)} hint={`std ${fmtNum(s.std)}`} />
        <Stat label="Range" value={`${fmtValue(s.min, metric)} – ${fmtValue(s.max, metric)}`} hint={`${s.n} months`} />
      </div>
      <Chart
        data={[{ type: "scatter", mode: "lines", name: h.label, x: h.dates, y: h.values, line: { color: "#0f766e", width: 2 } }]}
        layout={{ shapes: eventShapes(h.events), annotations: eventLabels(h.events), yaxis: { title: h.label }, showlegend: false }}
      />
    </Card>
  );
}

function SeasonalCard({ h }) {
  const p = h.seasonal_profile;
  return (
    <Card title="Seasonal profile" subtitle={p.note}>
      <Chart
        // A line (not bars) so the y-axis is not forced to start at 0, which would hide the seasonal shape.
        data={[{ type: "scatter", mode: "lines+markers", x: p.months.map((m) => MONTH_NAMES[m - 1]), y: p.values, line: { color: "#14b8a6", width: 2.5 }, name: h.label }]}
        layout={{ yaxis: { title: h.label }, hovermode: "closest", showlegend: false }}
        height={300}
      />
    </Card>
  );
}

// Three stacked panels: observed + trend, seasonal component, remainder.
function DecompositionCard({ d }) {
  const data = [
    { type: "scatter", mode: "lines", name: "Observed", x: d.dates, y: d.observed, line: { color: "#cbd5e1" }, yaxis: "y" },
    { type: "scatter", mode: "lines", name: "Trend", x: d.dates, y: d.trend, line: { color: "#0f766e", width: 2.5 }, yaxis: "y" },
    { type: "scatter", mode: "lines", name: "Seasonal", x: d.dates, y: d.seasonal, line: { color: "#f59e0b" }, yaxis: "y2" },
    { type: "bar", name: "Remainder", x: d.dates, y: d.resid, marker: { color: "#94a3b8" }, yaxis: "y3" },
  ];
  const layout = {
    xaxis: { anchor: "y3" },
    yaxis: { domain: [0.68, 1], title: "Level" },
    yaxis2: { domain: [0.36, 0.62], title: "Seasonal", gridcolor: "#e2e8f0" },
    yaxis3: { domain: [0, 0.3], title: "Remainder", gridcolor: "#e2e8f0" },
  };
  return (
    <Card title="STL decomposition" subtitle={d.note}>
      <Chart data={data} layout={layout} height={520} />
    </Card>
  );
}

function StationarityCard({ d }) {
  const st = d.stationarity;
  const rows = [
    ["ADF, level", st.adf_level_p, "H0: unit root (non-stationary). p < 0.05 means stationary."],
    ["ADF, first difference", st.adf_diff1_p, "Same test after differencing once (d = 1)."],
    ["ADF, seasonal difference (lag 12)", st.adf_seasdiff12_p, "Same test after a seasonal difference (D = 1)."],
    ["KPSS, level", st.kpss_level_p, "H0: stationary. p < 0.05 means non-stationary."],
  ];
  return (
    <Card title="Trend, seasonality and stationarity">
      <div className="stats">
        <Stat label="Trend strength" value={fmtNum(d.strength.trend_strength, 2)} hint="0 = none, 1 = strong" />
        <Stat label="Seasonal strength" value={fmtNum(d.strength.seasonal_strength, 2)} hint="0 = none, 1 = strong" />
        <Stat label="Conclusion" value={st.verdict} />
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr><th>Test</th><th className="num">p-value</th><th>How to read it</th></tr>
          </thead>
          <tbody>
            {rows.map(([name, p, how]) => (
              <tr key={name}>
                <td>{name}</td>
                <td className="num">{fmtP(p)}</td>
                <td className="muted">{how}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="muted small">
        ADF and KPSS can disagree when a series has level shifts (COVID). That is why the SARIMA order is chosen by
        validation error rather than by these tests alone.
      </p>
    </Card>
  );
}

export default function TrendExplorer() {
  const { segment, metric } = useSelection();
  const history = useApi("history", { segment, metric });
  const decomposition = useApi("decomposition", { segment, metric });

  return (
    <>
      <h1>Trend explorer</h1>
      <p className="lead">History, seasonality and decomposition for {segment}.</p>
      <Controls />
      <Async state={history}>
        {(h) => (
          <>
            <HistoryCard h={h} metric={metric} />
            <SeasonalCard h={h} />
          </>
        )}
      </Async>
      <Async state={decomposition}>
        {(d) => (
          <>
            <DecompositionCard d={d} />
            <StationarityCard d={d} />
          </>
        )}
      </Async>
    </>
  );
}
