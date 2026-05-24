import React from "react";

export default function NaicsInsightPanel({ data, loading, error, onDismiss, naicsLabel }) {
  if (!loading && !data && !error) return null;

  const maxCount = data ? Math.max(...data.months.map(m => m.count), 1) : 1;

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
          <p className="text-sm text-gray-600 font-medium">Fetching 12 months of SAM.gov data…</p>
          <p className="text-xs text-gray-400 mt-1">Results are cached after first load</p>
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

          {/* Bar chart */}
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

          {/* Interpretation callout */}
          <div className="bg-green-50 border border-green-200 rounded-xl px-4 py-3 flex gap-2 items-start">
            <svg className="w-4 h-4 text-green-600 mt-0.5 shrink-0" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
            </svg>
            <p className="text-xs text-green-800 leading-relaxed">{data.interpretation}</p>
          </div>

        </div>
      )}
    </div>
  );
}
