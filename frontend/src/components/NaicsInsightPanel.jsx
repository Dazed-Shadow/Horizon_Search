import React from "react";

function AgencyBar({ agency, count, maxCount }) {
  const pct = maxCount > 0 ? (count / maxCount) * 100 : 0;
  const shortName = agency
    .replace("Department of the ", "Dept. of the ")
    .replace("Department of ", "Dept. of ")
    .replace("National Aeronautics and Space Administration", "NASA")
    .replace("Environmental Protection Agency", "EPA")
    .replace("Social Security Administration", "SSA")
    .replace("General Services Administration", "GSA");
  return (
    <div className="flex items-center gap-2">
      <span className="w-36 shrink-0 text-right text-xs text-gray-500 truncate" title={agency}>
        {shortName}
      </span>
      <div className="relative flex-1 h-4 bg-gray-100 rounded overflow-hidden">
        <div className="h-full bg-indigo-400 rounded" style={{ width: `${pct}%` }} />
      </div>
      <span className="w-6 shrink-0 text-right text-xs font-semibold text-gray-700">{count}</span>
    </div>
  );
}

export default function NaicsInsightPanel({ data, loading, error, onDismiss, naicsLabel }) {
  if (!loading && !data && !error) return null;

  const maxCount = data ? Math.max(...data.months.map(m => m.count), 1) : 1;
  const maxAgencyCount = data?.agency_breakdown
    ? Math.max(...data.agency_breakdown.agencies.map(a => a.count), 1)
    : 1;

  return (
    <div className="border border-brand-200 rounded-2xl bg-white shadow-sm overflow-hidden mb-5">

      {/* Header */}
      <div className="flex items-start justify-between gap-3 px-5 py-4 border-b border-gray-100 bg-brand-50">
        <div className="min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className="font-bold text-brand-900 text-sm">12-Month Activity</h3>
            {data && (
              <span className="text-xs font-mono text-brand-600 bg-white border border-brand-200 px-2 py-0.5 rounded">
                NAICS {data.naics_code}
              </span>
            )}
            {data?.set_aside_label && (
              <span className="text-xs font-semibold bg-green-50 text-green-700 border border-green-200 px-2 py-0.5 rounded-full">
                {data.set_aside_label}
              </span>
            )}
          </div>
          {naicsLabel && (
            <p className="text-xs text-gray-500 mt-0.5 truncate">{naicsLabel}</p>
          )}
        </div>
        <button
          onClick={onDismiss}
          aria-label="Close activity panel"
          className="shrink-0 text-gray-400 hover:text-gray-600 transition p-1 rounded-lg hover:bg-gray-100"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* Loading */}
      {loading && (
        <div className="px-5 py-10 text-center">
          <div className="inline-block w-6 h-6 border-2 border-brand-400 border-t-transparent rounded-full animate-spin mb-3" />
          <p className="text-sm text-gray-600 font-medium">Loading 24 months of SAM.gov data…</p>
          <p className="text-xs text-gray-400 mt-1">Includes per-agency breakdown — results cached after first load</p>
        </div>
      )}

      {/* Error */}
      {error && !loading && (
        <div className="px-5 py-6 text-center">
          <p className="text-sm text-red-600 font-medium">Unable to load activity data</p>
          <p className="text-xs text-gray-400 mt-1">{error}</p>
        </div>
      )}

      {/* Data */}
      {data && !loading && (
        <div className="px-5 py-4">

          {/* Monthly bar chart */}
          <div className="space-y-1.5 mb-5">
            {data.months.map(m => (
              <div key={m.month} className="flex items-center gap-2">
                <span className={`w-16 shrink-0 text-right text-xs ${m.is_current ? "text-gray-400" : "text-gray-500"}`}>
                  {m.month_label.replace(/(\w+) (\d{4})/, (_, mo, yr) => `${mo} '${yr.slice(2)}`)}
                </span>
                <div className="relative flex-1 h-5 bg-gray-100 rounded overflow-hidden">
                  <div
                    className={`h-full rounded transition-all duration-300 ${
                      m.is_current
                        ? "bg-brand-300"
                        : data.set_aside_code
                        ? "bg-green-500"
                        : "bg-brand-500"
                    }`}
                    style={{ width: `${(m.count / maxCount) * 100}%` }}
                  />
                  {m.is_current && m.count > 0 && (
                    <span className="absolute right-1.5 top-0 text-[10px] text-gray-400 leading-5 font-medium">
                      so far
                    </span>
                  )}
                </div>
                <span className={`w-6 shrink-0 text-right text-xs font-semibold ${m.count === 0 ? "text-gray-300" : "text-gray-700"}`}>
                  {m.count}
                </span>
              </div>
            ))}
          </div>

          {/* Summary stats */}
          <div className="grid grid-cols-3 gap-3 mb-4">
            <div className="text-center bg-gray-50 rounded-xl p-3">
              <p className="text-xl font-bold text-brand-700">{data.total_opportunities}</p>
              <p className="text-xs text-gray-500 mt-0.5">total posted</p>
            </div>
            <div className="text-center bg-gray-50 rounded-xl p-3">
              <p className="text-xl font-bold text-brand-700">{data.avg_per_month}</p>
              <p className="text-xs text-gray-500 mt-0.5">avg / month</p>
            </div>
            <div className="text-center bg-gray-50 rounded-xl p-3">
              <p className="text-sm font-bold text-brand-700 leading-snug">{data.peak_month}</p>
              <p className="text-xs text-gray-500 mt-0.5">peak month</p>
            </div>
          </div>

          {/* FY forecast callout */}
          {data.fy_forecast && (
            <div className={`border rounded-xl px-4 py-3 flex gap-2 items-start mb-4 ${
              data.fy_forecast.is_surge_window
                ? "bg-amber-50 border-amber-200"
                : "bg-gray-50 border-gray-200"
            }`}>
              <svg
                className={`w-4 h-4 mt-0.5 shrink-0 ${data.fy_forecast.is_surge_window ? "text-amber-500" : "text-gray-400"}`}
                fill="currentColor" viewBox="0 0 20 20"
              >
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
              </svg>
              <div>
                <p className={`text-xs font-semibold mb-0.5 ${data.fy_forecast.is_surge_window ? "text-amber-800" : "text-gray-700"}`}>
                  {data.fy_forecast.fy_label} · {data.fy_forecast.days_remaining} days remaining
                </p>
                <p className={`text-xs leading-relaxed ${data.fy_forecast.is_surge_window ? "text-amber-700" : "text-gray-500"}`}>
                  {data.fy_forecast.message}
                </p>
              </div>
            </div>
          )}

          {/* Interpretation callout */}
          <div className="bg-green-50 border border-green-200 rounded-xl px-4 py-3 flex gap-2 items-start mb-4">
            <svg className="w-4 h-4 text-green-600 mt-0.5 shrink-0" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
            </svg>
            <p className="text-xs text-green-800 leading-relaxed">{data.interpretation}</p>
          </div>

          {/* Agency breakdown */}
          {data.agency_breakdown && (
            <div className="mb-4">
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                Top Agencies — 12-Month Window
              </p>
              <div className="space-y-1.5 mb-3">
                {data.agency_breakdown.agencies.map(a => (
                  <AgencyBar
                    key={a.agency}
                    agency={a.agency}
                    count={a.count}
                    maxCount={maxAgencyCount}
                  />
                ))}
              </div>
              <p className="text-xs text-gray-600 leading-relaxed">
                {data.agency_breakdown.interpretation}
              </p>
            </div>
          )}

          {/* Bid timing */}
          {data.bid_timing && (
            <div className="bg-blue-50 border border-blue-200 rounded-xl px-4 py-3">
              <p className="text-xs font-semibold text-blue-800 mb-2">Best Months to Bid</p>
              <div className="flex flex-wrap gap-1.5 mb-2">
                {data.bid_timing.best_months.map(m => (
                  <span key={m} className="text-xs bg-blue-100 text-blue-800 border border-blue-200 px-2 py-0.5 rounded-full font-medium">
                    {m}
                  </span>
                ))}
              </div>
              <p className="text-xs text-blue-700 leading-relaxed mb-1">
                {data.bid_timing.recommendation}
              </p>
              <p className="text-xs text-blue-500 font-semibold">{data.bid_timing.prep_window}</p>
            </div>
          )}

        </div>
      )}
    </div>
  );
}
