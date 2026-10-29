// Chart.jsx - a thin React wrapper around Plotly (the small "basic" build: lines, bars, pies).
// Usage: <Chart data={[...traces]} layout={{...}} height={360} />
import { useEffect, useRef } from "react";
import Plotly from "plotly.js-basic-dist-min";

// Shared look for every chart in the app.
const BASE_LAYOUT = {
  margin: { l: 60, r: 20, t: 30, b: 45 },
  paper_bgcolor: "rgba(0,0,0,0)",
  plot_bgcolor: "rgba(0,0,0,0)",
  font: { family: "system-ui, sans-serif", size: 12, color: "#334155" },
  legend: { orientation: "h", y: -0.18 },
  hovermode: "x unified",
  xaxis: { gridcolor: "#e2e8f0" },
  yaxis: { gridcolor: "#e2e8f0", zeroline: false },
};

const CONFIG = { responsive: true, displaylogo: false, modeBarButtonsToRemove: ["lasso2d", "select2d"] };

export default function Chart({ data, layout = {}, height = 360 }) {
  const ref = useRef(null);

  // Redraw whenever the data or layout change. Plotly.react only updates what changed.
  useEffect(() => {
    const merged = {
      ...BASE_LAYOUT,
      ...layout,
      xaxis: { ...BASE_LAYOUT.xaxis, ...layout.xaxis },
      yaxis: { ...BASE_LAYOUT.yaxis, ...layout.yaxis },
      height,
    };
    Plotly.react(ref.current, data, merged, CONFIG);
  }, [data, layout, height]);

  // Free Plotly's memory when the chart leaves the page.
  useEffect(() => {
    const node = ref.current;
    return () => Plotly.purge(node);
  }, []);

  return <div ref={ref} className="chart" />;
}
