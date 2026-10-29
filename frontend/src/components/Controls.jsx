// Controls.jsx - the segment / metric / horizon pickers shown at the top of each page.
// Options come from /api/meta, so the frontend never assumes which segments exist.
import { useSelection } from "../selection.jsx";

export default function Controls({ showSegment = true, showMetric = true, showHorizon = false }) {
  const { meta, segment, setSegment, metric, setMetric, horizon, setHorizon } = useSelection();
  const m = meta.data;

  return (
    <div className="controls">
      {showSegment && (
        <label>
          Segment
          <select value={segment} onChange={(e) => setSegment(e.target.value)}>
            {m.segments.map((s) => (
              <option key={s} value={s}>
                {s === m.aggregate_segment ? `${s} (national total)` : s}
              </option>
            ))}
          </select>
        </label>
      )}

      {showMetric && (
        <div className="control-group">
          <span>Metric</span>
          <div className="toggle">
            {m.metrics.map((x) => (
              <button key={x.id} className={x.id === metric ? "on" : ""} onClick={() => setMetric(x.id)}>
                {x.label}
              </button>
            ))}
          </div>
        </div>
      )}

      {showHorizon && (
        <div className="control-group">
          <span>Horizon</span>
          <div className="toggle">
            {m.horizons.map((h) => (
              <button key={h} className={h === horizon ? "on" : ""} onClick={() => setHorizon(h)}>
                {h} months
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
