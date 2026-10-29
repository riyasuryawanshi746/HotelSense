// ModelComparison.jsx - backtest results for one series (/api/evaluation)
// and the summary across all 21 series (/api/model-summary).
import { useApi } from "../api.js";
import { useSelection } from "../selection.jsx";
import { ALL_HORIZONS, MODEL_COLORS, fmtNum, fmtSigned, horizonDetail, horizonLabel } from "../format.js";
import Chart from "../components/Chart.jsx";
import Controls from "../components/Controls.jsx";
import { Async, Badge, Card } from "../components/ui.jsx";

const MODELS = ["Seasonal Naive", "Holt-Winters", "SARIMA", "Combination"];

// Metrics table for the selected horizon; the winner is highlighted.
function MetricsTable({ e }) {
  const rows = e.table.filter((r) => r.horizon === e.horizon);
  const best = e.best[e.horizon];
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Model</th>
            <th className="num">MAE</th>
            <th className="num">RMSE</th>
            <th className="num">MAPE %</th>
            <th className="num">Skill vs Seasonal Naive</th>
            <th className="num">Raw 80% coverage</th>
            <th className="num">Cells (origins)</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.model} className={best && r.model === best.model ? "best" : ""}>
              <td>{r.model} {best && r.model === best.model && <Badge tone="info">Lowest RMSE</Badge>}</td>
              <td className="num">{fmtNum(r.MAE, 2)}</td>
              <td className="num">{fmtNum(r.RMSE, 2)}</td>
              <td className="num">{fmtNum(r.MAPE, 1)}</td>
              <td className={`num ${r.skill_vs_snaive_pct > 0 ? "pos" : r.skill_vs_snaive_pct < 0 ? "neg" : ""}`}>
                {r.model === "Seasonal Naive" ? "baseline" : fmtSigned(r.skill_vs_snaive_pct)}
              </td>
              <td className="num">{fmtNum(r.coverage80, 0)}%</td>
              <td className="num">{r.n} ({r.n_origins})</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// One line per horizon: which model won and whether that win counts.
function WinnerList({ e }) {
  return (
    <ul className="winners">
      {Object.entries(e.best).map(([h, b]) => (
        <li key={h}>
          <strong>{horizonLabel(h)}:</strong> {b.model} ({fmtSigned(b.skill_vs_snaive_pct)} vs baseline){" "}
          {b.beats_baseline ? <Badge tone="good">Real improvement (≥ 5%)</Badge> : <Badge tone="warn">No better than last year</Badge>}
        </li>
      ))}
    </ul>
  );
}

function RmseByHorizonChart({ e }) {
  const horizons = [...new Set(e.table.map((r) => r.horizon))].sort((a, b) => a - b);
  const data = MODELS.map((m) => ({
    type: "bar", name: m, marker: { color: MODEL_COLORS[m] },
    x: horizons.map(horizonLabel),
    y: horizons.map((h) => e.table.find((r) => r.model === m && r.horizon === h)?.RMSE ?? null),
  }));
  return <Chart data={data} layout={{ barmode: "group", yaxis: { title: "RMSE" }, hovermode: "closest" }} height={320} />;
}

function BacktestChart({ e }) {
  const b = e.backtest;
  const data = [
    { type: "scatter", mode: "lines+markers", name: "Actual (published)", x: b.dates, y: b.actual, line: { color: "#0f172a", width: 3 } },
    ...MODELS.filter((m) => b.models[m]).map((m) => ({
      type: "scatter", mode: "lines+markers", name: m, x: b.dates, y: b.models[m], line: { color: MODEL_COLORS[m], width: 1.5 },
    })),
  ];
  return <Chart data={data} height={360} />;
}

// Renders a {row: {column: value}} object from /api/model-summary as a table.
// rowName / colName turn raw keys (such as "6") into readable labels (such as "6-month horizon").
function SummaryTable({ table, rowLabel, suffix = "", rowName = (r) => r, colName = (c) => c }) {
  const rows = Object.keys(table);
  const cols = [...new Set(rows.flatMap((r) => Object.keys(table[r])))];
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>{rowLabel}</th>
            {cols.map((c) => <th key={c} className="num">{colName(c)}</th>)}
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r}>
              <td>{rowName(r)}</td>
              {cols.map((c) => <td key={c} className="num">{table[r][c] == null ? "–" : `${table[r][c]}${suffix}`}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// Shown when the API has no result for the requested scope. We never fall back to a pooled number.
function Unavailable({ what }) {
  return <p className="muted small">{what}: not available from the API for this horizon.</p>;
}

const PCT_COLUMN = { pct_series_beating_baseline: "% of segment × horizon results", pct: "% of segments" };

// Three clearly separated scopes: every horizon side by side, the selected horizon only, and all horizons pooled.
function AllSeriesSummary({ s, horizon }) {
  const scope = s.scope || {};
  const mapeH = s.median_mape_by_metric_and_horizon?.[horizon];
  const beatsH = s.pct_series_where_model_beats_baseline_by_horizon?.[horizon];
  // {metric: pct} -> {metric: {pct: value}} so it fits SummaryTable
  const beatsHTable = beatsH && Object.fromEntries(Object.entries(beatsH).map(([m, v]) => [m, { pct: v }]));

  return (
    <Card
      title="Across all 21 series (7 segments × 3 metrics)"
      subtitle="The honest picture: the simple 'same as last year' baseline is hard to beat, especially for ADR."
    >
      <h3 className="scope-title">Each horizon separately</h3>
      <div className="grid-2">
        <div>
          <h3>Wins (lowest RMSE)</h3>
          <SummaryTable table={s.wins_by_horizon} rowLabel="Horizon" rowName={horizonLabel} />
          <p className="muted small">{scope.wins_by_horizon}</p>
        </div>
        <div>
          <h3>Median skill vs Seasonal Naive (%)</h3>
          <SummaryTable table={s.median_skill_vs_baseline_pct} rowLabel="Horizon" rowName={horizonLabel} suffix="%" />
          <p className="muted small">{scope.median_skill_vs_baseline_pct}</p>
        </div>
        <div>
          <h3>Raw model 80% interval coverage (%)</h3>
          <SummaryTable table={s.raw_interval_coverage_pct} rowLabel="Horizon" rowName={horizonLabel} suffix="%" />
          <p className="muted small">
            {scope.raw_interval_coverage_pct}. Below 80% means the models' own intervals are too narrow, so the app
            uses intervals calibrated on backtest errors instead. Calibration uses the same backtest, so real coverage
            may be a little lower.
          </p>
        </div>
      </div>

      <h3 className="scope-title">{horizonDetail(horizon)} only</h3>
      <div className="grid-2">
        <div>
          <h3>Median MAPE by metric (%)</h3>
          {mapeH ? <SummaryTable table={mapeH} rowLabel="Metric" suffix="%" /> : <Unavailable what="Median MAPE" />}
          <p className="muted small">{scope.median_mape_by_metric_and_horizon}</p>
        </div>
        <div>
          <h3>Winner beats the baseline by ≥ 5%</h3>
          {beatsHTable ? (
            <SummaryTable table={beatsHTable} rowLabel="Metric" suffix="%" colName={(c) => PCT_COLUMN[c] || c} />
          ) : (
            <Unavailable what="Share beating the baseline" />
          )}
          <p className="muted small">{scope.pct_series_where_model_beats_baseline_by_horizon}</p>
        </div>
      </div>

      <h3 className="scope-title">{ALL_HORIZONS} (3, 6 and 12 months pooled)</h3>
      <p className="muted small">
        These combine the 3-, 6- and 12-month results into one number, so they do not describe any single horizon and
        should not be compared with the horizon-specific tables above.
      </p>
      <div className="grid-2">
        <div>
          <h3>Median MAPE by metric (%), {ALL_HORIZONS.toLowerCase()}</h3>
          <SummaryTable table={s.median_mape_by_metric} rowLabel="Metric" suffix="%" />
          <p className="muted small">{scope.median_mape_by_metric}</p>
        </div>
        <div>
          <h3>Winner beats the baseline by ≥ 5%, {ALL_HORIZONS.toLowerCase()}</h3>
          <SummaryTable table={s.pct_series_where_model_beats_baseline} rowLabel="Metric" suffix="%" colName={(c) => PCT_COLUMN[c] || c} />
          <p className="muted small">{scope.pct_series_where_model_beats_baseline}</p>
        </div>
      </div>
    </Card>
  );
}

export default function ModelComparison() {
  const { segment, metric, horizon } = useSelection();
  const evaluation = useApi("evaluation", { segment, metric, horizon });
  const summary = useApi("model-summary", {});

  return (
    <>
      <h1>Model comparison</h1>
      <p className="lead">
        Rolling-origin backtest: each model is re-fitted on data up to an origin (first one 2022-12, then every 2
        months) and scored on the following months. All models are scored on exactly the same months.
      </p>
      <Controls showHorizon />

      <Async state={evaluation}>
        {(e) => (
          <>
            <Card title={`${segment}: ${horizonDetail(e.horizon)}`} subtitle="Skill = 1 − RMSE / RMSE of Seasonal Naive. Positive is better than repeating last year.">
              <MetricsTable e={e} />
              <WinnerList e={e} />
            </Card>
            <Card title="RMSE at each horizon" subtitle="Each bar is a separate horizon result; none of them is pooled across horizons.">
              <RmseByHorizonChart e={e} />
            </Card>
            <Card title={e.backtest.description} subtitle="Each point is a forecast made exactly this many months before the target month (that single step only, not steps 1 to h).">
              <BacktestChart e={e} />
              <p className="muted small">{e.note}</p>
            </Card>
          </>
        )}
      </Async>

      <Async state={summary}>{(s) => <AllSeriesSummary s={s} horizon={horizon} />}</Async>
    </>
  );
}
