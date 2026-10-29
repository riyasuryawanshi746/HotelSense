// selection.jsx - the user's current choices (segment, metric, horizon), shared by all pages.
// Also loads /api/meta once, which lists the valid segments, metrics and horizons.
import { createContext, useContext, useEffect, useState } from "react";
import { useApi } from "./api.js";

const SelectionContext = createContext(null);

export function SelectionProvider({ children }) {
  const meta = useApi("meta", {});
  const [segment, setSegment] = useState(null);
  const [metric, setMetric] = useState("occupancy");
  const [horizon, setHorizon] = useState(6);

  // Once meta has arrived, start with the national total (Qatar+).
  useEffect(() => {
    if (meta.data && segment === null) setSegment(meta.data.aggregate_segment);
  }, [meta.data, segment]);

  const value = { meta, segment, setSegment, metric, setMetric, horizon, setHorizon };
  return <SelectionContext.Provider value={value}>{children}</SelectionContext.Provider>;
}

// Any component can call useSelection() to read or change the current choices.
export function useSelection() {
  return useContext(SelectionContext);
}

// Human-readable label for a metric id, taken from /api/meta.
export function useMetricLabel(metricId) {
  const { meta } = useSelection();
  const found = meta.data?.metrics.find((m) => m.id === metricId);
  return found ? found.label : metricId;
}
