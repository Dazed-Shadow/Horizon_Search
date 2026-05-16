import React from "react";
import { formatDate, formatCurrency, deadlineStatus } from "../utils/formatters";
import { SET_ASIDE_COLORS, VETERAN_CODES } from "../utils/constants";

function SetAsideBadge({ code, label }) {
  if (!label) return null;
  const group = VETERAN_CODES.has(code) ? "Veteran"
    : (code?.startsWith("WOSB") || code?.startsWith("EDWOSB")) ? "Women-Owned"
    : "Small Business";
  const color = SET_ASIDE_COLORS[group] || SET_ASIDE_COLORS.Other;
  return (
    <span className={`badge ${color}`}>
      {VETERAN_CODES.has(code) && (
        <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
          <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
        </svg>
      )}
      {label}
    </span>
  );
}

const AWARDED_TYPES = new Set(["a", "u"]);

export default function ContractCard({ contract, onOpen }) {
  const deadline = deadlineStatus(contract.response_deadline);
  const isAwarded = AWARDED_TYPES.has(contract.solicitation_type);

  return (
    <article className={`bg-white rounded-xl border shadow-sm hover:shadow-md transition p-5 ${
      isAwarded ? "border-gray-200 opacity-80" : "border-gray-200"
    }`}>
      {/* Header row */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <button
            type="button"
            onClick={() => onOpen(contract)}
            className="text-left font-semibold text-gray-900 leading-snug line-clamp-2 mb-1
                       hover:text-brand-700 transition w-full"
          >
            {contract.title}
          </button>
          <p className="text-sm text-gray-500 truncate">
            {[contract.agency, contract.sub_agency, contract.office]
              .filter(Boolean).join(" › ")}
          </p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {isAwarded && (
            <span className="badge bg-gray-100 text-gray-500 border border-gray-200">
              Already Awarded
            </span>
          )}
          {contract.ui_link && (
            <a
              href={contract.ui_link}
              target="_blank"
              rel="noopener noreferrer"
              className="text-brand-600 hover:text-brand-700 border border-brand-200
                         hover:bg-brand-50 rounded-lg px-3 py-1.5 text-xs font-semibold transition"
            >
              SAM.gov ↗
            </a>
          )}
        </div>
      </div>

      {/* Badges */}
      <div className="flex flex-wrap gap-1.5 mt-3">
        <SetAsideBadge code={contract.set_aside_code} label={contract.set_aside_label} />
        {contract.solicitation_type_label && (
          <span className="badge bg-gray-100 text-gray-700">
            {contract.solicitation_type_label}
          </span>
        )}
        {contract.naics_code && (
          <span className="badge bg-indigo-50 text-indigo-700">
            NAICS {contract.naics_code}
          </span>
        )}
        {contract.place_of_performance && (
          <span className="badge bg-gray-100 text-gray-600">
            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
            </svg>
            {contract.place_of_performance}
          </span>
        )}
      </div>

      {/* Key metrics row */}
      <div className="mt-4 grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm">
        <div>
          <p className="text-xs text-gray-400 mb-0.5">Posted</p>
          <p className="font-medium text-gray-700">{formatDate(contract.posted_date) || "—"}</p>
        </div>
        <div>
          <p className="text-xs text-gray-400 mb-0.5">Response Deadline</p>
          <p className={`font-medium ${deadline?.color || "text-gray-700"}`}>
            {formatDate(contract.response_deadline) || "—"}
            {deadline && <span className="ml-1 text-xs">({deadline.label})</span>}
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-400 mb-0.5">Solicitation #</p>
          <p className="font-mono text-xs text-gray-700 truncate">
            {contract.solicitation_number || "—"}
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-400 mb-0.5">Award Amount</p>
          <p className="font-medium text-gray-700">
            {contract.award_amount ? formatCurrency(contract.award_amount) : "—"}
          </p>
        </div>
      </div>

      {/* View details link */}
      <div className="mt-4 flex items-center justify-end">
        <button
          onClick={() => onOpen(contract)}
          className="text-sm font-semibold text-brand-700 hover:text-brand-800 hover:underline"
        >
          View details →
        </button>
      </div>
    </article>
  );
}
