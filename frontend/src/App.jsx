import React, { useState, useEffect } from "react";
import SearchBar from "./components/SearchBar";
import FilterPanel from "./components/FilterPanel";
import ContractList from "./components/ContractList";
import { useContracts } from "./hooks/useContracts";
import { SET_ASIDES, VETERAN_CODES } from "./utils/constants";

const VETERAN_QUICK_FILTERS = [
  { label: "All SDVOSB", code: "SDVOSBC" },
  { label: "SDVOSB Sole Source", code: "SDVOSBS" },
  { label: "VOSB", code: "VSB" },
  { label: "8(a)", code: "8AN" },
  { label: "HUBZone", code: "HZC" },
  { label: "Sources Sought", code: null, field: "solicitation_type", value: "r" },
];

function ApiKeyBanner({ onDismiss }) {
  return (
    <div className="bg-yellow-50 border-b border-yellow-200 px-4 py-3">
      <div className="max-w-7xl mx-auto flex items-center justify-between gap-4">
        <div className="flex items-center gap-2 text-sm text-yellow-800">
          <svg className="w-4 h-4 shrink-0 text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
          </svg>
          <span>
            <strong>SAM.gov API key not configured.</strong>{" "}
            Copy <code className="bg-yellow-100 px-1 rounded">backend/.env.example</code> to{" "}
            <code className="bg-yellow-100 px-1 rounded">backend/.env</code> and add your free key from{" "}
            <a
              href="https://sam.gov/profile/details"
              target="_blank"
              rel="noopener noreferrer"
              className="underline font-semibold hover:text-yellow-900"
            >
              sam.gov/profile/details
            </a>
            . Live search will not work until then.
          </span>
        </div>
        <button
          onClick={onDismiss}
          className="shrink-0 text-yellow-600 hover:text-yellow-800 transition"
          aria-label="Dismiss"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>
  );
}

export default function App() {
  const {
    filters,
    updateFilter,
    resetFilters,
    results,
    loading,
    error,
    page,
    limit,
    search,
    goToPage,
  } = useContracts();

  const [apiKeyMissing, setApiKeyMissing] = useState(false);
  const [bannerDismissed, setBannerDismissed] = useState(false);

  useEffect(() => {
    fetch("/api/config/status")
      .then(r => r.json())
      .then(data => {
        if (!data.api_key_configured) setApiKeyMissing(true);
      })
      .catch(() => {}); // backend not running yet — silent
  }, []);

  const hasActiveFilters = Object.entries(filters).some(([k, v]) => k !== "keyword" && v !== "");

  function handleQuickFilter(qf) {
    if (qf.field) {
      updateFilter(qf.field, qf.value);
      const newFilters = { ...filters, [qf.field]: qf.value };
      search(newFilters, 0);
    } else {
      updateFilter("set_aside", qf.code);
      const newFilters = { ...filters, set_aside: qf.code };
      search(newFilters, 0);
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-brand-900 text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-5">
          <div className="flex items-center gap-3 mb-1">
            <div className="bg-white/10 rounded-lg p-2">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16H9m3 0h3" />
              </svg>
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight">Horizon Search</h1>
              <p className="text-xs text-brand-100 leading-none">Veteran Contract Intelligence Platform</p>
            </div>
          </div>
        </div>
      </header>

      {/* API key warning banner */}
      {apiKeyMissing && !bannerDismissed && (
        <ApiKeyBanner onDismiss={() => setBannerDismissed(true)} />
      )}

      {/* Hero search */}
      <div className="bg-gradient-to-b from-brand-900 to-brand-700 pb-8 pt-2 shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <p className="text-brand-100 text-sm mb-4">
            Search active federal contracts across SAM.gov — filtered for veteran-owned business set-asides.
          </p>
          <SearchBar
            value={filters.keyword}
            onChange={v => updateFilter("keyword", v)}
            onSearch={() => search(filters, 0)}
            loading={loading}
          />

          {/* Quick filter pills */}
          <div className="flex flex-wrap gap-2 mt-4">
            <span className="text-xs text-brand-200 self-center font-medium">Quick:</span>
            {VETERAN_QUICK_FILTERS.map(qf => (
              <button
                key={qf.label}
                className={`text-xs px-3 py-1.5 rounded-full font-medium transition border ${
                  (qf.field
                    ? filters[qf.field] === qf.value
                    : filters.set_aside === qf.code)
                    ? "bg-white text-brand-700 border-white"
                    : "bg-white/10 text-white border-white/20 hover:bg-white/20"
                }`}
                onClick={() => handleQuickFilter(qf)}
              >
                {qf.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex gap-6 items-start">
          {/* Filter sidebar */}
          <div className="w-72 shrink-0 sticky top-6">
            <FilterPanel
              filters={filters}
              onUpdate={updateFilter}
              onSearch={() => search(filters, 0)}
              onReset={resetFilters}
            />

            {/* Veteran resources card */}
            <div className="mt-4 bg-green-50 border border-green-200 rounded-xl p-4 text-sm">
              <h3 className="font-semibold text-green-800 mb-2">Veteran Business Resources</h3>
              <ul className="space-y-1 text-green-700 text-xs">
                <li>
                  <a href="https://www.sba.gov/federal-contracting/contracting-assistance-programs/veteran-assistance-programs"
                    target="_blank" rel="noopener noreferrer"
                    className="hover:underline font-medium">SBA Veteran Programs ↗</a>
                  <p className="text-green-600">Register for SDVOSB / VOSB certification</p>
                </li>
                <li className="pt-1">
                  <a href="https://sam.gov/content/home"
                    target="_blank" rel="noopener noreferrer"
                    className="hover:underline font-medium">Register on SAM.gov ↗</a>
                  <p className="text-green-600">Required to bid on federal contracts</p>
                </li>
                <li className="pt-1">
                  <a href="https://www.va.gov/osdbu/"
                    target="_blank" rel="noopener noreferrer"
                    className="hover:underline font-medium">VA OSDBU ↗</a>
                  <p className="text-green-600">VA's Office of Small &amp; Disadvantaged Business</p>
                </li>
                <li className="pt-1">
                  <a href="https://www.acquisition.gov/far/subpart-19.14"
                    target="_blank" rel="noopener noreferrer"
                    className="hover:underline font-medium">FAR 19.14 — SDVOSB Rules ↗</a>
                  <p className="text-green-600">Legal basis for set-aside preference</p>
                </li>
              </ul>
            </div>
          </div>

          {/* Results */}
          <div className="flex-1 min-w-0">
            {results && (
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2 text-sm text-gray-500">
                  {hasActiveFilters && (
                    <span className="bg-brand-100 text-brand-700 px-2 py-0.5 rounded-full text-xs font-medium">
                      Filters active
                    </span>
                  )}
                </div>
              </div>
            )}

            <ContractList
              results={results}
              loading={loading}
              error={error}
              page={page}
              limit={limit}
              onPageChange={goToPage}
              hasFilters={hasActiveFilters || filters.keyword !== ""}
            />

            {!results && !loading && (
              <div className="text-center py-20 text-gray-400">
                <svg className="w-20 h-20 mx-auto mb-5 text-gray-100" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1}
                    d="M21 21l-4.35-4.35M17 11A6 6 0 1 1 5 11a6 6 0 0 1 12 0z" />
                </svg>
                <p className="text-xl font-semibold text-gray-400">Search active government contracts</p>
                <p className="mt-2 text-sm max-w-sm mx-auto">
                  Enter a keyword or use the quick filters above. All results come live from SAM.gov.
                </p>
                <div className="mt-8 grid grid-cols-3 gap-4 max-w-lg mx-auto text-left">
                  {[
                    { icon: "🎖️", title: "Veteran Set-Asides", desc: "SDVOSB & VOSB reserved contracts" },
                    { icon: "🏢", title: "All Agencies", desc: "DoD, VA, DHS, and every federal dept." },
                    { icon: "📋", title: "Full Details", desc: "Deadlines, NAICS, POC, and more" },
                  ].map(tip => (
                    <div key={tip.title} className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
                      <div className="text-2xl mb-2">{tip.icon}</div>
                      <p className="font-semibold text-gray-700 text-sm">{tip.title}</p>
                      <p className="text-xs text-gray-400 mt-0.5">{tip.desc}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </main>

      <footer className="border-t border-gray-200 mt-12 py-6 text-center text-xs text-gray-400">
        Horizon Search · Contract data sourced from{
        " "}
        <a href="https://sam.gov" target="_blank" rel="noopener noreferrer" className="underline">SAM.gov</a>
        {" "}· For veteran-owned businesses
      </footer>
    </div>
  );
}
