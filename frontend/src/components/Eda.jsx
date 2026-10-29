// Eda.jsx - Overview page sections built from /api/eda:
//   DatasetAtAGlance (raw file -> cleaned data, quality checks), KeyFindings, EdaHighlights (charts).
// Every number and sentence comes from the API (backend/eda.py); this file only lays them out.
import Chart from "./Chart.jsx";
import { Badge, Card, Stat } from "./ui.jsx";
import { fmtValue } from "../format.js";

// The national total is drawn thicker and in black so it stands out from the six segments.
function lineStyle(segment, aggregate) {
  return segment === aggregate ? { color: "#0f172a", width: 3 } : { width: 1.5 };
}

// ------------------------------------------------------------------ dataset at a glance
export function DatasetAtAGlance({ ds }) {
  const raw = ds.raw;
  const clean = ds.clean;
  return (
    <Card title="Dataset at a glance" subtitle={`Source file: ${raw.file}. Qatar Tourism, State of Qatar Open Data (CC BY).`}>
      <div className="stats">
        <Stat label="Records" value={clean.rows.toLocaleString()} hint={`${raw.rows} in the raw file, ${raw.columns} columns`} />
        <Stat label="Date range" value={`${clean.first_date} to ${clean.last_date}`} hint={`${clean.months} months`} />
        <Stat label="Frequency" value={clean.frequency} hint={`${clean.rows_per_segment ?? "–"} rows per segment`} />
        <Stat label="Segments" value={clean.n_segments} hint={`incl. ${clean.aggregate_segment} (national total)`} />
        <Stat label="Series analysed" value={clean.n_series} hint={`${clean.n_segments} segments × ${clean.metrics.length} metrics`} />
      </div>
      <p className="small">
        <strong>Metrics:</strong> {clean.metrics.map((m) => m.label).join(" · ")}.{" "}
        <span className="muted">Raw columns: {raw.column_names.join(", ")}.</span>
      </p>

      <div className="grid-2">
        <div>
          <h3>From raw file to analysis data</h3>
          <ol className="steps">
            {ds.cleaning_steps.map((s, i) => (
              <li key={i}>{s}</li>
            ))}
          </ol>
        </div>
        <div>
          <h3>Data-quality checks</h3>
          <div className="table-wrap">
            <table>
              <thead>
                <tr><th>Check</th><th className="num">Rows found</th></tr>
              </thead>
              <tbody>
                {ds.quality.map((q) => (
                  <tr key={q.check}>
                    <td className="wrap">{q.check}</td>
                    <td className="num">{q.result === 0 ? <Badge tone="good">0</Badge> : <Badge tone="warn">{q.result}</Badge>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {ds.occupancy_over_100.length > 0 && (
            <p className="muted small">
              Occupancy above 100%:{" "}
              {ds.occupancy_over_100.map((o) => `${o.segment} ${o.date} (${o.occupancy}%, demand ${o.demand.toLocaleString()} vs supply ${o.supply.toLocaleString()})`).join("; ")}.
            </p>
          )}
          <p className="muted small">{ds.aggregate_check.text}</p>
        </div>
      </div>
    </Card>
  );
}

// ------------------------------------------------------------------ key findings
export function KeyFindings({ findings }) {
  if (!findings || findings.length === 0) {
    return <Card title="Key findings"><p className="muted">No findings available.</p></Card>;
  }
  return (
    <Card title="Key findings" subtitle="Each statement is calculated from the published data; none of them claims a cause.">
      <ul className="findings">
        {findings.map((f) => (
          <li key={f.topic}>
            <strong>{f.topic}.</strong> {f.text}
          </li>
        ))}
      </ul>
    </Card>
  );
}

// ------------------------------------------------------------------ EDA charts
function TrendChart({ e, aggregate }) {
  const a = e.annual_means;
  const data = Object.entries(a.series).map(([seg, ys]) => ({
    type: "scatter", mode: "lines+markers", name: seg, x: a.years, y: ys, line: lineStyle(seg, aggregate),
  }));
  return (
    <Card
      title={`Historical trend: yearly average ${e.label}`}
      subtitle={`${a.note} Complete calendar years only${a.excluded_partial_years.length ? ` (left out: ${a.excluded_partial_years.join(", ")})` : ""}.`}
    >
      <Chart data={data} layout={{ yaxis: { title: e.label }, xaxis: { dtick: 1 }, hovermode: "closest" }} height={360} />
    </Card>
  );
}

function SeasonalChart({ e, aggregate }) {
  const s = e.seasonal_profile;
  const data = Object.entries(s.series).map(([seg, ys]) => ({
    type: "scatter", mode: "lines+markers", name: seg, x: s.months, y: ys, line: lineStyle(seg, aggregate),
  }));
  return (
    <Card title={`Seasonal pattern: average ${e.label} by calendar month`} subtitle={s.note}>
      <Chart data={data} layout={{ yaxis: { title: e.label }, hovermode: "closest" }} height={360} />
    </Card>
  );
}

// Median with the middle 50% (Q1 to Q3) as a bar, and the lowest / highest month as small markers.
function DistributionChart({ e, metric }) {
  const segs = Object.keys(e.distribution);
  const d = segs.map((s) => e.distribution[s]);
  const data = [
    {
      type: "scatter", mode: "markers", name: "Median (bar = middle 50%)", x: segs, y: d.map((x) => x.median),
      marker: { size: 10, color: "#0d9488" },
      error_y: { type: "data", symmetric: false, array: d.map((x) => x.q3 - x.median), arrayminus: d.map((x) => x.median - x.q1), thickness: 6, width: 0, color: "#99f6e4" },
    },
    { type: "scatter", mode: "markers", name: "Lowest month", x: segs, y: d.map((x) => x.min), marker: { symbol: "triangle-down", color: "#94a3b8" } },
    { type: "scatter", mode: "markers", name: "Highest month", x: segs, y: d.map((x) => x.max), marker: { symbol: "triangle-up", color: "#f59e0b" } },
  ];
  return (
    <Card title={`Distribution of monthly ${e.label} by segment`} subtitle="All months, including the COVID period and World Cup months.">
      <Chart data={data} layout={{ yaxis: { title: e.label }, hovermode: "closest" }} height={360} />
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Segment</th><th className="num">Min</th><th className="num">Q1</th><th className="num">Median</th>
              <th className="num">Q3</th><th className="num">Max</th><th className="num">Mean</th><th className="num">Variation (CV)</th>
            </tr>
          </thead>
          <tbody>
            {segs.map((s, i) => (
              <tr key={s}>
                <td>{s}</td>
                {["min", "q1", "median", "q3", "max", "mean"].map((k) => (
                  <td key={k} className="num">{fmtValue(d[i][k], metric)}</td>
                ))}
                <td className="num">{d[i].cv_pct == null ? "–" : `${d[i].cv_pct}%`}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}

function PeriodChart({ e }) {
  const p = e.period_means;
  const colors = ["#94a3b8", "#ef4444", "#0d9488"];
  const data = p.periods.map((period, i) => ({
    type: "bar", name: period.replace(/^\d\.\s*/, ""), x: p.segments, y: p.segments.map((s) => p.values[s][i]),
    marker: { color: colors[i % colors.length] },
  }));
  return (
    <Card title={`Segment comparison: average ${e.label} before, during and after COVID`}>
      <Chart data={data} layout={{ barmode: "group", yaxis: { title: e.label }, hovermode: "closest" }} height={360} />
    </Card>
  );
}

function RelationshipChart({ rel, aggregate }) {
  const data = Object.entries(rel.points).map(([seg, p]) => ({
    type: "scatter", mode: "markers", name: seg, x: p.occupancy, y: p.adr,
    marker: { size: seg === aggregate ? 6 : 5, opacity: 0.6, color: seg === aggregate ? "#0f172a" : undefined },
  }));
  return (
    <Card title="Relationship: occupancy vs ADR (each dot is one month)" subtitle={rel.note}>
      <Chart
        data={data}
        // the x-axis title needs room, so the legend sits a little lower than on other charts
        layout={{ xaxis: { title: "Occupancy rate (%)" }, yaxis: { title: "ADR (QAR)" }, hovermode: "closest",
                  legend: { orientation: "h", y: -0.25, yanchor: "top" } }}
        height={400}
      />
      <div className="table-wrap">
        <table>
          <thead>
            <tr><th>Segment</th><th className="num">Pearson r</th><th className="num">Months</th></tr>
          </thead>
          <tbody>
            {rel.correlations.map((c) => (
              <tr key={c.segment}>
                <td>{c.segment}</td>
                <td className="num">{c.r == null ? "–" : `${c.r > 0 ? "+" : ""}${c.r.toFixed(2)}`}</td>
                <td className="num">{c.n}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="muted small">r near 0 means no linear relationship; ±1 means a perfect one.</p>
    </Card>
  );
}

function OutlierCard({ o, label }) {
  if (!o) {
    return (
      <Card title="Unusual months">
        <p className="muted">Outlier table not available. Run scripts/02_eda.py to create it.</p>
      </Card>
    );
  }
  const periods = ["COVID period", "World Cup months", "Other months"];
  return (
    <Card title={`Unusual months (${o.total} flagged across all series)`} subtitle={o.note}>
      <div className="grid-2">
        <div>
          <h3>Flagged months by metric and period</h3>
          <div className="table-wrap">
            <table>
              <thead>
                <tr><th>Metric</th>{periods.map((p) => <th key={p} className="num">{p}</th>)}</tr>
              </thead>
              <tbody>
                {Object.entries(o.by_metric_and_period).map(([m, row]) => (
                  <tr key={m}>
                    <td>{m}</td>
                    {periods.map((p) => <td key={p} className="num">{row[p] ?? 0}</td>)}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
        <div>
          <h3>Largest for {label}</h3>
          {o.top_for_metric.length === 0 ? (
            <p className="muted small">No flagged months for this metric.</p>
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr><th>Segment</th><th>Month</th><th className="num">Robust z</th><th>Period</th></tr>
                </thead>
                <tbody>
                  {o.top_for_metric.map((r) => (
                    <tr key={`${r.segment}-${r.date}`}>
                      <td>{r.segment}</td><td>{r.date}</td><td className="num">{r.robust_z}</td><td>{r.period}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </Card>
  );
}

export function EdaHighlights({ e, metric, aggregate }) {
  return (
    <>
      <h2 className="section-title">EDA highlights: {e.label}</h2>
      <p className="lead">Exploratory charts for the metric selected above. The relationship chart always compares occupancy with ADR.</p>
      <TrendChart e={e} aggregate={aggregate} />
      <SeasonalChart e={e} aggregate={aggregate} />
      <DistributionChart e={e} metric={metric} />
      <PeriodChart e={e} />
      <RelationshipChart rel={e.relationship} aggregate={aggregate} />
      <OutlierCard o={e.outliers} label={e.label} />
    </>
  );
}
