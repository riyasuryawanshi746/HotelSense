// Overview.jsx - the landing page:
//   1. Dataset at a glance and Key findings (from /api/eda)
//   2. every segment side by side for one metric (from /api/overview); clicking a row opens the Trend explorer
//   3. EDA highlights for the selected metric (from /api/eda)
import { useNavigate } from "react-router-dom";
import { useApi } from "../api.js";
import { useSelection } from "../selection.jsx";
import { fmtSigned, fmtValue, horizonDetail, horizonLabel } from "../format.js";
import Chart from "../components/Chart.jsx";
import Controls from "../components/Controls.jsx";
import { DatasetAtAGlance, EdaHighlights, KeyFindings } from "../components/Eda.jsx";
import { Async, Badge, Card } from "../components/ui.jsx";

// The latest 12 months vs the 12 months before, for every segment (unchanged from before).
function LatestComparison({ d, metric, openSegment }) {
  const names = d.segments.map((r) => r.segment);
  const chartData = [
    { type: "bar", name: "Previous 12 months", x: names, y: d.segments.map((r) => r.prev12_mean), marker: { color: "#cbd5e1" } },
    { type: "bar", name: "Last 12 months", x: names, y: d.segments.map((r) => r.last12_mean), marker: { color: "#0d9488" } },
  ];
  return (
    <>
      <Card title={`${d.label}: average of the last 12 months vs the 12 months before`}>
        <Chart data={chartData} layout={{ barmode: "group", yaxis: { title: d.label }, hovermode: "closest" }} height={340} />
      </Card>

      <Card
        title="Segments"
        subtitle={`"Best model" is the lowest-RMSE model in the backtest at the ${horizonDetail(6)}. "No better than last year" means it did not beat simply repeating last year's values by at least 5%. Click a row to explore that segment.`}
      >
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Segment</th>
                <th>Latest month</th>
                <th className="num">Latest value</th>
                <th className="num">Last 12 months</th>
                <th className="num">Previous 12 months</th>
                <th className="num">Change</th>
                <th>Best model ({horizonLabel(6)})</th>
              </tr>
            </thead>
            <tbody>
              {d.segments.map((r) => (
                <tr key={r.segment} className="clickable" onClick={() => openSegment(r.segment)}>
                  <td>{r.segment}</td>
                  <td>{r.latest_date}</td>
                  <td className="num">{fmtValue(r.latest, metric)}</td>
                  <td className="num">{fmtValue(r.last12_mean, metric)}</td>
                  <td className="num">{fmtValue(r.prev12_mean, metric)}</td>
                  <td className={`num ${r.change_pct >= 0 ? "pos" : "neg"}`}>{fmtSigned(r.change_pct)}</td>
                  <td>
                    {r.best_model_6m ?? "–"}{" "}
                    {r.beats_baseline_6m === false && <Badge tone="warn">No better than last year</Badge>}
                    {r.beats_baseline_6m === true && <Badge tone="good">Beats baseline</Badge>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </>
  );
}

export default function Overview() {
  const { metric, setSegment, meta } = useSelection();
  const overview = useApi("overview", { metric });
  const eda = useApi("eda", { metric });
  const navigate = useNavigate();
  const aggregate = meta.data.aggregate_segment;

  function openSegment(name) {
    setSegment(name);
    navigate("/trend");
  }

  return (
    <>
      <h1>Overview</h1>
      <p className="lead">
        What the data contains, what the exploratory analysis shows, and how every segment is doing now. Pick a
        metric to update the comparison and the EDA charts.
      </p>

      <Async state={eda}>
        {(e) => (
          <>
            <DatasetAtAGlance ds={e.dataset} />
            <KeyFindings findings={e.key_findings} />
          </>
        )}
      </Async>

      <h2 className="section-title">Latest 12 months by segment</h2>
      <Controls showSegment={false} />
      <Async state={overview}>{(d) => <LatestComparison d={d} metric={metric} openSegment={openSegment} />}</Async>

      <Async state={eda}>{(e) => <EdaHighlights e={e} metric={metric} aggregate={aggregate} />}</Async>
    </>
  );
}
