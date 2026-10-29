// ui.jsx - small presentational building blocks reused by every page.

export function Loading({ text = "Loading…" }) {
  return <div className="loading">{text}</div>;
}

// Shows an error returned by api.js (including the backend's "detail" message).
export function ErrorBox({ error }) {
  if (!error) return null;
  return (
    <div className="error" role="alert">
      <strong>Something went wrong.</strong> {error.message}
    </div>
  );
}

// A white panel with an optional title and subtitle.
export function Card({ title, subtitle, children, className = "" }) {
  return (
    <section className={`card ${className}`}>
      {title && <h2>{title}</h2>}
      {subtitle && <p className="muted small">{subtitle}</p>}
      {children}
    </section>
  );
}

// A single headline number, e.g. "Latest value: 52.2%".
export function Stat({ label, value, hint }) {
  return (
    <div className="stat">
      <div className="stat-label">{label}</div>
      <div className="stat-value">{value}</div>
      {hint && <div className="stat-hint">{hint}</div>}
    </div>
  );
}

// A coloured pill. tone: "good" | "warn" | "info" | "neutral".
export function Badge({ tone = "neutral", children }) {
  return <span className={`badge badge-${tone}`}>{children}</span>;
}

// Wraps the content of a data-driven card: shows loading / error states first.
export function Async({ state, children }) {
  if (state.error) return <ErrorBox error={state.error} />;
  if (!state.data) return <Loading />;
  return (
    <div className={state.loading ? "refreshing" : ""}>
      {children(state.data)}
    </div>
  );
}
