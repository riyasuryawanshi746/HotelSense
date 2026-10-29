// api.js - the only place the frontend talks to the backend.
// Every number on screen comes from these calls; nothing is hard-coded.
import { useEffect, useState } from "react";

// Build "/api/forecast?segment=...&metric=..." safely.
// URLSearchParams encodes "+" and "&" in segment names such as "1 & 2 Star Hotels+".
function buildUrl(path, params = {}) {
  const query = new URLSearchParams(params).toString();
  return query ? `/api/${path}?${query}` : `/api/${path}`;
}

// Fetch JSON; on failure throw an Error carrying the backend's "detail" message.
export async function getJson(path, params) {
  let response;
  try {
    response = await fetch(buildUrl(path, params));
  } catch {
    throw new Error("Cannot reach the backend. Is it running on port 8000?");
  }
  let body = null;
  try {
    body = await response.json();
  } catch {
    // not JSON (for example the proxy's own error page)
  }
  if (!response.ok) {
    // No JSON body means the answer came from the Vite proxy, not FastAPI: the backend is not running.
    if (body === null) {
      throw new Error("The backend did not respond. Start it with: cd backend && uvicorn main:app --reload --port 8000");
    }
    const detail = body.detail || response.statusText;
    throw new Error(`Request failed (${response.status}): ${detail}`);
  }
  return body;
}

// React hook: load an endpoint and re-load whenever the parameters change.
// Returns { data, error, loading }. Pass params = null to skip the request.
export function useApi(path, params) {
  const key = params === null ? null : JSON.stringify(params);
  const [state, setState] = useState({ data: null, error: null, loading: key !== null });

  useEffect(() => {
    if (key === null) return;
    let cancelled = false; // ignore answers that arrive after the user changed the selection
    setState((s) => ({ data: s.data, error: null, loading: true }));
    getJson(path, JSON.parse(key))
      .then((data) => !cancelled && setState({ data, error: null, loading: false }))
      .catch((error) => !cancelled && setState({ data: null, error, loading: false }));
    return () => {
      cancelled = true;
    };
  }, [path, key]);

  return state;
}
