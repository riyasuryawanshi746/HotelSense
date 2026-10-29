// Overview.jsx - every segment side by side for one metric (from /api/overview).
// Clicking a row selects that segment and opens the Trend explorer.
import { useNavigate } from "react-router-dom";
import { useApi } from "../api.js";
import { useSelection } from "../selection.jsx";
import { fmtSigned, fmtValue, horizonDetail, horizonLabel } from "../format.js";
import Chart from "../components/Chart.jsx";
import Controls from "../components/Controls.jsx";
import { Async, Badge, Card } from "../components/ui.jsx";

export default function Overview() {
  const { metric, setSegment } = useSelection();
  const state = useApi("overview", { metric });
  const navigate = useNavigate();

  function openSegment(name) {
    setSegment(name);
    navigate("/trend");
  }

  return (
    <>
      <h1>Overview</h1>
      <p className="lead">
        Pick a metric to compare all accommodation segments. "Last 12 months" is compared with the 12 months before
        it. Click a segment to explore its history.
      </p>
      <Controls showSegment={false} />

      <Async state={state}>
        {(d) => {
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
                subtitle={`"Best model" is the lowest-RMSE model in the backtest at the ${horizonDetail(6)}. "No better than last year" means it did not beat simply repeating last year's values by at least 5%.`}
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
        }}
      </Async>
    </>
  );
}
