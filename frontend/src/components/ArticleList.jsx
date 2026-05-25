import { useState } from "react";
import { articles, BUCKETS } from "../data/articles";

const BUCKET_COLORS = {
  "Funding & Contracts": "bg-green-100 text-green-800",
  "Founder Profiles":    "bg-brand-100 text-brand-800",
  "Media & Creators":    "bg-pink-100 text-pink-800",
  "Leadership Lessons":  "bg-amber-100 text-amber-800",
  "Policy & Programs":   "bg-blue-100 text-blue-800",
};

const SOURCE_COLORS = {
  "SBA":          "bg-blue-600",
  "Inc.":         "bg-purple-600",
  "Forbes":       "bg-green-600",
  "HBR":          "bg-red-700",
  "Task & Purpose": "bg-gray-700",
  "WATM":         "bg-brand-600",
  "Podcast":      "bg-orange-600",
  "Mil Times":    "bg-gray-600",
};

export default function ArticleList() {
  const [activeBucket, setActiveBucket] = useState("All");

  const filtered = activeBucket === "All"
    ? articles
    : articles.filter(a => a.bucket === activeBucket);

  return (
    <section>
      <div className="mb-5">
        <h2 className="text-xl font-bold text-gray-900 mb-1">Articles & Resources</h2>
        <p className="text-sm text-gray-500">
          Curated coverage of veteran entrepreneurs, funding programs, and leadership from top publications.
        </p>
      </div>

      {/* Bucket filter chips */}
      <div className="flex flex-wrap gap-2 mb-6">
        {BUCKETS.map(b => (
          <button
            key={b}
            type="button"
            onClick={() => setActiveBucket(b)}
            className={`text-xs font-semibold px-3 py-1.5 rounded-full border transition ${
              activeBucket === b
                ? "bg-brand-600 text-white border-brand-600"
                : "bg-white text-gray-600 border-gray-200 hover:border-brand-300 hover:text-brand-600"
            }`}
          >
            {b}
          </button>
        ))}
      </div>

      {/* Article rows */}
      <div className="space-y-3">
        {filtered.map(a => (
          <a
            key={a.id}
            href={a.url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex gap-4 items-start p-4 bg-white rounded-xl border border-gray-100
                       hover:border-brand-200 hover:shadow-sm transition group"
          >
            {/* Source badge */}
            <div className={`${SOURCE_COLORS[a.sourceShort] ?? "bg-gray-600"} shrink-0 w-10 h-10 rounded-lg
                            flex items-center justify-center text-white text-xs font-bold text-center leading-tight`}>
              {a.sourceShort}
            </div>

            <div className="flex-1 min-w-0">
              <div className="flex items-start justify-between gap-3 flex-wrap">
                <p className="font-semibold text-gray-900 text-sm group-hover:text-brand-700 leading-snug">
                  {a.title}
                  {a.verify && (
                    <span className="ml-2 text-xs text-amber-600 font-normal">(URL to verify)</span>
                  )}
                </p>
                <span className={`shrink-0 text-xs font-medium px-2 py-0.5 rounded-full border
                                  ${BUCKET_COLORS[a.bucket] ?? "bg-gray-100 text-gray-600"}`}>
                  {a.bucket}
                </span>
              </div>
              <p className="text-xs text-gray-500 mt-0.5 mb-1">
                {a.source} · {a.author} · {a.published}
              </p>
              <p className="text-xs text-gray-500 leading-relaxed">{a.summary}</p>
            </div>
          </a>
        ))}
      </div>

      <p className="text-xs text-gray-400 mt-5 text-center">
        Articles marked "(URL to verify)" link to the source homepage until a direct link is confirmed.
      </p>
    </section>
  );
}
