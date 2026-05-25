import { useState, useCallback } from "react";

// ---------------------------------------------------------------------------
// Static data loader — reads naics-insights.json from frontend/public/ once
// per page session. This file is generated from the pre-seeded SQLite DB
// and bundled with the frontend, so the Insights page works without the
// backend running for all 42 common NAICS codes.
// ---------------------------------------------------------------------------
let _staticPromise = null;

function loadStaticData() {
  if (!_staticPromise) {
    _staticPromise = fetch("/naics-insights.json")
      .then(r => (r.ok ? r.json() : { codes: {} }))
      .catch(() => ({ codes: {} }));
  }
  return _staticPromise;
}

// Recompute FY forecast from today's date — the static JSON was generated at
// seed time so days_remaining would be stale. Everything else is stable.
function computeFyForecast() {
  const today = new Date();
  const month = today.getMonth() + 1;
  const year = today.getFullYear();
  const fyEndYear = month <= 9 ? year : year + 1;
  const fyEnd = new Date(fyEndYear, 8, 30); // Sep 30
  const daysRemaining = Math.max(Math.ceil((fyEnd - today) / 86_400_000), 1);
  const isSurge = month >= 6 && month <= 9;
  const fyLabel = `FY${fyEndYear}`;

  let message;
  if (isSurge) {
    message = daysRemaining <= 30
      ? `Final stretch of ${fyLabel} — ${daysRemaining} days until Sep 30. Agencies are racing to obligate remaining budget. Monitor SAM.gov daily and be ready to respond within hours.`
      : `Fiscal year-end surge underway. ${fyLabel} closes Sep 30 (${daysRemaining} days away). Agencies accelerate July–Sep spending to avoid 'use it or lose it' expiration — high-volume period for awards.`;
  } else if (month >= 10) {
    message = `${fyLabel} started Oct 1. New budgets are being allocated — slower Q1 contracting activity expected. ${daysRemaining} days until this FY closes. Good window to refine your capability statement.`;
  } else {
    message = `Mid-${fyLabel} (ends Sep 30, ${daysRemaining} days away). Steady contracting activity — a good window to build relationships with contracting officers before the summer surge.`;
  }

  return { fy_label: fyLabel, is_surge_window: isSurge, days_remaining: daysRemaining, message };
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------
export function useNaicsInsight() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeKey, setActiveKey] = useState(null);

  const fetchInsight = useCallback(async (naicsCode, setAside = null) => {
    const key = `${naicsCode}:${setAside || ""}`;
    if (key === activeKey && data) return;

    setLoading(true);
    setError(null);

    try {
      // ── Path 1: static JSON (no backend required) ─────────────────────────
      // Only for unfiltered lookups — set-aside filtered data needs the API.
      if (!setAside) {
        const sd = await loadStaticData();
        const entry = sd.codes?.[naicsCode];
        if (entry) {
          setData({
            ...entry,
            naics_code: naicsCode,
            set_aside_code: null,
            set_aside_label: null,
            // Patch FY forecast so days_remaining reflects today, not seed date
            fy_forecast: computeFyForecast(),
          });
          setActiveKey(key);
          setLoading(false);
          return;
        }
      }

      // ── Path 2: live API (backend must be running) ────────────────────────
      const params = new URLSearchParams({ naics_code: naicsCode });
      if (setAside) params.set("set_aside", setAside);
      const res = await fetch(`/api/insights/naics-activity?${params}`);
      const text = await res.text();
      let body;
      try {
        body = JSON.parse(text);
      } catch {
        throw new Error("Backend server is not responding — make sure it is running on port 8000.");
      }
      if (!res.ok) throw new Error(body.detail || `Error ${res.status}`);
      setData(body);
      setActiveKey(key);
    } catch (err) {
      setError(err.message);
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [activeKey, data]);

  const clear = useCallback(() => {
    setData(null);
    setError(null);
    setActiveKey(null);
  }, []);

  return { data, loading, error, fetchInsight, clear };
}
