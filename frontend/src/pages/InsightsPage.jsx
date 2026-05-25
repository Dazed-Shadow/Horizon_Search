import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import NaicsInsightPanel from "../components/NaicsInsightPanel";
import { useNaicsInsight } from "../hooks/useNaicsInsight";
import { COMMON_NAICS } from "../utils/constants";

const NAICS_BY_CATEGORY = COMMON_NAICS.reduce((acc, n) => {
  (acc[n.category] = acc[n.category] || []).push(n);
  return acc;
}, {});

export default function InsightsPage() {
  const [selectedCode, setSelectedCode] = useState("");
  const [customCode, setCustomCode] = useState("");
  const [snapshotDate, setSnapshotDate] = useState(null);
  const { data, loading, error, fetchInsight, clear } = useNaicsInsight();

  // Load snapshot metadata once to show the "data as of" date
  useEffect(() => {
    fetch("/naics-insights.json")
      .then(r => r.json())
      .then(sd => setSnapshotDate(sd.generated_at ?? null))
      .catch(() => {});
  }, []);

  const activeCode = customCode.trim() || selectedCode;
  const canLoad = activeCode.length === 6;

  function handleLoad() {
    if (!canLoad) return;
    fetchInsight(activeCode);
  }

  function handleSelectCode(code) {
    setSelectedCode(code);
    setCustomCode("");
    clear();
  }

  function handleCustomCode(val) {
    setCustomCode(val.replace(/\D/g, "").slice(0, 6));
    setSelectedCode("");
    clear();
  }

  const naicsLabel = COMMON_NAICS.find(n => n.code === (data?.naics_code ?? activeCode))?.label;

  return (
    <div className="flex flex-col min-h-screen bg-gray-50">

      {/* Hero */}
      <div className="bg-brand-900 py-12">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 text-center">
          <p className="text-xs font-semibold uppercase tracking-widest text-brand-300 mb-2">
            Market Intelligence
          </p>
          <h1 className="text-3xl sm:text-4xl font-bold text-white mb-3">
            NAICS Activity Insights
          </h1>
          <p className="text-brand-300 text-sm max-w-xl mx-auto leading-relaxed">
            Research 24 months of federal contract posting history for any NAICS code — before you
            commit to a certification or start writing a proposal. See which agencies are buying,
            when they buy, and how active your market has been.
          </p>
          {snapshotDate && (
            <p className="text-brand-400 text-xs mt-3">
              Market snapshot · Data as of {snapshotDate} · Refreshed periodically
            </p>
          )}
        </div>
      </div>

      <div className="max-w-3xl mx-auto w-full px-4 sm:px-6 py-8">

        {/* Picker card */}
        <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-5 mb-5">
          <h2 className="text-sm font-bold text-gray-800 mb-4">Choose a NAICS Code</h2>

          {/* Common codes grouped dropdown */}
          <div className="mb-3">
            <label className="block text-xs font-medium text-gray-500 mb-1">Select from common codes</label>
            <select
              value={selectedCode}
              onChange={e => handleSelectCode(e.target.value)}
              className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-brand-400 bg-white"
            >
              <option value="">— Browse by category —</option>
              {Object.entries(NAICS_BY_CATEGORY).map(([cat, codes]) => (
                <optgroup key={cat} label={cat}>
                  {codes.map(n => (
                    <option key={n.code} value={n.code}>{n.code} — {n.label}</option>
                  ))}
                </optgroup>
              ))}
            </select>
          </div>

          {/* Divider */}
          <div className="flex items-center gap-3 my-3">
            <div className="flex-1 h-px bg-gray-100" />
            <span className="text-xs text-gray-400 font-medium">or</span>
            <div className="flex-1 h-px bg-gray-100" />
          </div>

          {/* Custom code input */}
          <div className="mb-5">
            <label className="block text-xs font-medium text-gray-500 mb-1">
              Enter any 6-digit NAICS code
              <span className="text-gray-400 font-normal ml-1">(requires backend for codes outside the 42 common codes)</span>
            </label>
            <input
              type="text"
              inputMode="numeric"
              maxLength={6}
              placeholder="e.g. 541512"
              value={customCode}
              onChange={e => handleCustomCode(e.target.value)}
              className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm font-mono tracking-widest focus:outline-none focus:ring-2 focus:ring-brand-400"
            />
          </div>

          <button
            onClick={handleLoad}
            disabled={!canLoad}
            className="w-full bg-brand-600 hover:bg-brand-700 disabled:bg-gray-100 disabled:text-gray-400 text-white font-bold py-2.5 rounded-xl text-sm transition"
          >
            {canLoad ? `Load Activity for ${activeCode}` : "Enter or select a NAICS code above"}
          </button>
        </div>

        {/* Insight panel */}
        {(loading || data || error) && (
          <NaicsInsightPanel
            data={data}
            loading={loading}
            error={error}
            onDismiss={clear}
            naicsLabel={naicsLabel}
          />
        )}

        {/* Search CTA */}
        {data && (
          <div className="bg-green-50 border border-green-200 rounded-2xl px-5 py-4 flex items-center justify-between gap-4 mb-8">
            <div>
              <p className="text-sm font-semibold text-green-800">Ready to search live contracts?</p>
              <p className="text-xs text-green-600 mt-0.5">
                Use NAICS {data.naics_code} in Search Contracts to see active opportunities.
              </p>
            </div>
            <Link
              to="/"
              className="shrink-0 bg-green-600 hover:bg-green-700 text-white font-bold px-4 py-2 rounded-xl text-sm transition"
            >
              Search contracts →
            </Link>
          </div>
        )}

        {/* Empty state */}
        {!loading && !data && !error && (
          <div className="text-center py-12 text-gray-400">
            <svg className="w-10 h-10 mx-auto mb-3 opacity-40" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            <p className="text-sm font-medium">Select a NAICS code above to load activity data</p>
            <p className="text-xs mt-1">
              Snapshot data for 42 common codes loads instantly · No backend required
            </p>
          </div>
        )}

      </div>
    </div>
  );
}
