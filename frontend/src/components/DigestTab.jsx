/**
 * DigestTab — renders a structured RFP digest from the parsed backend digest object.
 * Matches the existing ContractDetailDrawer visual language (SectionLabel, gray-50 stat cards,
 * brand colors).
 *
 * Props:
 *   digest      — ContractDigest | null
 *   loading     — bool
 *   onSeeRaw    — () => void
 */
function SectionLabel({ children }) {
  return (
    <p className="text-xs font-semibold uppercase tracking-wide text-gray-400 mb-2">
      {children}
    </p>
  );
}

function ConfidencePill({ confidence }) {
  const map = {
    high:   { cls: "bg-green-100 text-green-800 border border-green-200",   label: "High confidence" },
    medium: { cls: "bg-amber-100 text-amber-800 border border-amber-200",   label: "Medium confidence" },
    low:    { cls: "bg-gray-100 text-gray-600 border border-gray-200",       label: "Limited structure found — see Raw tab" },
  };
  const { cls, label } = map[confidence] ?? map.low;
  return (
    <span className={`inline-block text-xs font-semibold px-2.5 py-1 rounded-full ${cls}`}>
      {label}
    </span>
  );
}

function SkeletonBars() {
  return (
    <div className="py-5 space-y-3 animate-pulse">
      <div className="h-4 bg-gray-200 rounded w-3/4" />
      <div className="h-4 bg-gray-200 rounded w-1/2" />
      <div className="h-4 bg-gray-200 rounded w-5/6" />
    </div>
  );
}

export default function DigestTab({ digest, loading, onSeeRaw }) {
  if (loading) {
    return <SkeletonBars />;
  }

  if (!digest) {
    return (
      <div className="py-5">
        <p className="text-sm text-gray-400 italic">
          Could not load digest. Switch to the Raw tab to view the description.
        </p>
        <button
          onClick={onSeeRaw}
          className="mt-2 text-xs text-brand-600 hover:underline"
        >
          Switch to Raw tab
        </button>
      </div>
    );
  }

  const {
    scope_summary,
    deliverables,
    submission_requirements,
    evaluation_criteria,
    period_of_performance,
    estimated_value,
    key_dates,
    extraction_confidence,
  } = digest;

  return (
    <div className="py-4 space-y-0">
      {/* Header row: title + confidence pill */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-gray-800">RFP Digest</h3>
        <ConfidencePill confidence={extraction_confidence} />
      </div>

      {/* Scope summary */}
      {scope_summary && (
        <section className="py-4 border-b border-gray-100">
          <SectionLabel>Scope summary</SectionLabel>
          <div className="bg-brand-50 border border-brand-200 rounded-lg p-3">
            <p className="text-sm text-brand-800 leading-relaxed">{scope_summary}</p>
          </div>
        </section>
      )}

      {/* Period of performance + Estimated value — side-by-side stat cards */}
      {(period_of_performance || estimated_value) && (
        <section className="py-4 border-b border-gray-100">
          <div className="grid grid-cols-2 gap-4">
            {period_of_performance && (
              <div className="bg-gray-50 rounded-xl p-3">
                <p className="text-xs text-gray-400 mb-1">Period of performance</p>
                <p className="text-sm font-semibold text-gray-800">{period_of_performance}</p>
              </div>
            )}
            {estimated_value && (
              <div className="bg-gray-50 rounded-xl p-3">
                <p className="text-xs text-gray-400 mb-1">Estimated value</p>
                <p className="text-sm font-semibold text-gray-800">{estimated_value}</p>
              </div>
            )}
          </div>
        </section>
      )}

      {/* Deliverables */}
      {deliverables && deliverables.length > 0 && (
        <section className="py-4 border-b border-gray-100">
          <SectionLabel>Deliverables</SectionLabel>
          <ul className="space-y-1">
            {deliverables.map((item, i) => (
              <li key={i} className="flex gap-2 text-sm text-gray-700">
                <span className="text-gray-400 shrink-0 mt-0.5">•</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* Submission requirements */}
      {submission_requirements && submission_requirements.length > 0 && (
        <section className="py-4 border-b border-gray-100">
          <SectionLabel>Submission requirements</SectionLabel>
          <ul className="space-y-1">
            {submission_requirements.map((item, i) => (
              <li key={i} className="flex gap-2 text-sm text-gray-700">
                <span className="text-gray-400 shrink-0 mt-0.5">•</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* Evaluation criteria */}
      {evaluation_criteria && evaluation_criteria.length > 0 && (
        <section className="py-4 border-b border-gray-100">
          <SectionLabel>Evaluation criteria</SectionLabel>
          <ul className="space-y-1">
            {evaluation_criteria.map((item, i) => (
              <li key={i} className="flex gap-2 text-sm text-gray-700">
                <span className="text-gray-400 shrink-0 mt-0.5">•</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* Key dates */}
      {key_dates && key_dates.length > 0 && (
        <section className="py-4 border-b border-gray-100">
          <SectionLabel>Key dates</SectionLabel>
          <ul className="space-y-1.5">
            {key_dates.map((kd, i) => (
              <li key={i} className="flex gap-3 text-sm">
                <span className="font-semibold text-gray-700 shrink-0">{kd.label}:</span>
                <span className="text-gray-600">{kd.date}</span>
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* Footer */}
      <div className="pt-4">
        <p className="text-xs text-gray-400">
          Need the full text?{" "}
          <button
            onClick={onSeeRaw}
            className="text-brand-600 hover:underline font-medium"
          >
            Switch to Raw.
          </button>
        </p>
      </div>
    </div>
  );
}
