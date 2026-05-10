import React, { useState, useEffect } from "react";
import SearchBar from "../components/SearchBar";
import FilterPanel from "../components/FilterPanel";
import ContractList from "../components/ContractList";
import { useContracts } from "../hooks/useContracts";

const QUICK_FILTERS = [
  { label: "All SDVOSB",       set_aside: "SDVOSBC" },
  { label: "SDVOSB Sole Source", set_aside: "SDVOSBS" },
  { label: "VOSB",              set_aside: "VSB" },
  { label: "8(a)",              set_aside: "8AN" },
  { label: "HUBZone",           set_aside: "HZC" },
  { label: "Sources Sought",    solicitation_type: "r" },
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
            Open <code className="bg-yellow-100 px-1 rounded">backend\.env</code> and set your{" "}
            <code className="bg-yellow-100 px-1 rounded">SAM_GOV_API_KEY</code>.{" "}
            Get a free key at{" "}
            <a href="https://sam.gov/profile/details" target="_blank" rel="noopener noreferrer"
              className="underline font-semibold hover:text-yellow-900">sam.gov/profile/details</a>.
          </span>
        </div>
        <button onClick={onDismiss} className="shrink-0 text-yellow-600 hover:text-yellow-800 transition" aria-label="Dismiss">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>
  );
}

export default function SearchPage() {
  const { filters, updateFilter, resetFilters, results, loading, error, page, limit, search, goToPage } = useContracts();
  const [apiKeyMissing, setApiKeyMissing] = useState(false);
  const [bannerDismissed, setBannerDismissed] = useState(false);

  useEffect(() => {
    fetch("/api/config/status")
      .then(r => r.json())
      .then(d => { if (!d.api_key_configured) setApiKeyMissing(true); })
      .catch(() => {});
  }, []);

  const hasActiveFilters = Object.entries(filters).some(([k, v]) => k !== "keyword" && v !== "");

  function applyQuickFilter(qf) {
    const next = { ...filters };
    if (qf.set_aside)        { next.set_aside = qf.set_aside; next.solicitation_type = ""; }
    if (qf.solicitation_type){ next.solicitation_type = qf.solicitation_type; next.set_aside = ""; }
    Object.keys(qf).forEach(k => updateFilter(k === "set_aside" ? "set_aside" : k, next[k]));
    search(next, 0);
  }

  function isQuickActive(qf) {
    if (qf.set_aside)         return filters.set_aside === qf.set_aside;
    if (qf.solicitation_type) return filters.solicitation_type === qf.solicitation_type;
    return false;
  }

  return (
    <>
      {apiKeyMissing && !bannerDismissed && <ApiKeyBanner onDismiss={() => setBannerDismissed(true)} />}

      {/* Hero search bar */}
      <div className="bg-gradient-to-b from-brand-900 to-brand-700 pb-8 pt-4 shadow-lg">
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
          <div className="flex flex-wrap gap-2 mt-4">
            <span className="text-xs text-brand-200 self-center font-medium">Quick:</span>
            {QUICK_FILTERS.map(qf => (
              <button
                key={qf.label}
                onClick={() => applyQuickFilter(qf)}
                className={`text-xs px-3 py-1.5 rounded-full font-medium transition border ${
                  isQuickActive(qf)
                    ? "bg-white text-brand-700 border-white"
                    : "bg-white/10 text-white border-white/20 hover:bg-white/20"
                }`}
              >
                {qf.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Main layout */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex-1">
        <div className="flex gap-6 items-start">

          {/* Sidebar — fixed width, scrolls independently */}
          <div className="w-72 shrink-0 sticky top-4 overflow-y-auto max-h-[calc(100vh-5rem)]">
            <FilterPanel
              filters={filters}
              onUpdate={updateFilter}
              onSearch={() => search(filters, 0)}
              onReset={resetFilters}
            />

            <div className="mt-4 bg-green-50 border border-green-200 rounded-xl p-4 text-sm">
              <h3 className="font-semibold text-green-800 mb-2">Veteran Business Resources</h3>
              <ul className="space-y-2 text-xs">
                {[
                  { href: "https://www.sba.gov/federal-contracting/contracting-assistance-programs/veteran-assistance-programs", label: "SBA Veteran Programs", sub: "Register for SDVOSB / VOSB" },
                  { href: "https://sam.gov/content/home", label: "Register on SAM.gov", sub: "Required for all federal contracts" },
                  { href: "https://www.va.gov/osdbu/", label: "VA OSDBU", sub: "VA small business office" },
                  { href: "https://www.acquisition.gov/far/subpart-19.14", label: "FAR 19.14 — SDVOSB Rules", sub: "Legal basis for set-aside preference" },
                ].map(r => (
                  <li key={r.href}>
                    <a href={r.href} target="_blank" rel="noopener noreferrer"
                      className="font-medium text-green-700 hover:underline">{r.label} ↗</a>
                    <p className="text-green-600">{r.sub}</p>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Results */}
          <div className="flex-1 min-w-0">
            {results && hasActiveFilters && (
              <span className="inline-block bg-brand-100 text-brand-700 px-2 py-0.5 rounded-full text-xs font-medium mb-4">
                Filters active
              </span>
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
    </>
  );
}
