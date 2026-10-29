// App.jsx - page layout (header + navigation) and the routes for the four pages.
import { NavLink, Navigate, Route, Routes } from "react-router-dom";
import { SelectionProvider, useSelection } from "./selection.jsx";
import { ErrorBox, Loading } from "./components/ui.jsx";
import Overview from "./pages/Overview.jsx";
import TrendExplorer from "./pages/TrendExplorer.jsx";
import Forecast from "./pages/Forecast.jsx";
import ModelComparison from "./pages/ModelComparison.jsx";

const PAGES = [
  { path: "/overview", label: "Overview" },
  { path: "/trend", label: "Trend explorer" },
  { path: "/forecast", label: "Forecast" },
  { path: "/models", label: "Model comparison" },
];

// Pages are only shown once /api/meta has loaded, because they need the segment list.
function Pages() {
  const { meta, segment } = useSelection();
  if (meta.error) return <ErrorBox error={meta.error} />;
  if (!meta.data || segment === null) return <Loading />;
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/overview" replace />} />
      <Route path="/overview" element={<Overview />} />
      <Route path="/trend" element={<TrendExplorer />} />
      <Route path="/forecast" element={<Forecast />} />
      <Route path="/models" element={<ModelComparison />} />
      <Route path="*" element={<Navigate to="/overview" replace />} />
    </Routes>
  );
}

function DataNote() {
  const { meta } = useSelection();
  if (!meta.data) return null;
  return (
    <span>
      Data {meta.data.first_date} to {meta.data.last_date}
    </span>
  );
}

export default function App() {
  return (
    <SelectionProvider>
      <header className="header">
        <div className="brand">
          <strong>HotelSense</strong>
          <span className="muted">Qatar hotel occupancy and revenue forecasting</span>
        </div>
        <nav className="nav">
          {PAGES.map((p) => (
            <NavLink key={p.path} to={p.path} className={({ isActive }) => (isActive ? "active" : "")}>
              {p.label}
            </NavLink>
          ))}
        </nav>
      </header>
      <main className="main">
        <Pages />
      </main>
      <footer className="footer">
        <span>Source: Qatar Tourism, State of Qatar Open Data (CC BY). Segment-level data, not individual hotels.</span>
        <DataNote />
      </footer>
    </SelectionProvider>
  );
}
