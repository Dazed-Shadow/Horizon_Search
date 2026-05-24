import React, { useState } from "react";
import { SET_ASIDES, SOLICITATION_TYPES, US_STATES, COMMON_NAICS } from "../utils/constants";

function FilterSection({ title, children, defaultOpen = true }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="border-b border-gray-100 last:border-0">
      <button
        className="flex w-full items-center justify-between py-3 text-sm font-semibold text-gray-700 hover:text-brand-600 transition"
        onClick={() => setOpen(o => !o)}
      >
        {title}
        <svg className={`w-4 h-4 transition-transform ${open ? "rotate-180" : ""}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      {open && <div className="pb-4 space-y-2">{children}</div>}
    </div>
  );
}

// Group set-asides by category for display
const SET_ASIDE_GROUPS = SET_ASIDES.reduce((acc, sa) => {
  if (!acc[sa.group]) acc[sa.group] = [];
  acc[sa.group].push(sa);
  return acc;
}, {});

export default function FilterPanel({ filters, onUpdate, onSearch, onReset, onRequestInsight }) {
  return (
    <aside className="bg-white rounded-xl border border-gray-200 shadow-sm p-4 space-y-1">
      <div className="flex items-center justify-between mb-2">
        <h2 className="font-bold text-gray-800">Filters</h2>
        <button className="text-xs text-brand-600 hover:underline" onClick={onReset}>
          Clear all
        </button>
      </div>

      {/* Open solicitations toggle */}
      <div className="flex items-center justify-between py-2 border-b border-gray-100">
        <div>
          <p className="text-sm font-semibold text-gray-700">Open solicitations only</p>
          <p className="text-xs text-gray-400">Hide already-awarded contracts</p>
        </div>
        <button
          role="switch"
          aria-checked={filters.open_only !== false}
          onClick={() => onUpdate("open_only", filters.open_only === false ? true : false)}
          className={`relative inline-flex h-5 w-9 shrink-0 rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-brand-500 ${
            filters.open_only !== false ? "bg-brand-600" : "bg-gray-200"
          }`}
        >
          <span className={`inline-block h-4 w-4 mt-0.5 rounded-full bg-white shadow transition-transform ${
            filters.open_only !== false ? "translate-x-4" : "translate-x-0.5"
          }`} />
        </button>
      </div>

      <FilterSection title="Veteran & Small Business Set-Aside">
        <select
          className="filter-input"
          value={filters.set_aside}
          onChange={e => onUpdate("set_aside", e.target.value)}
        >
          <option value="">All set-aside types</option>
          {Object.entries(SET_ASIDE_GROUPS).map(([group, items]) => (
            <optgroup key={group} label={`— ${group} —`}>
              {items.map(sa => (
                <option key={sa.code} value={sa.code}>{sa.label}</option>
              ))}
            </optgroup>
          ))}
        </select>
        <p className="text-xs text-gray-400 leading-snug mt-1">
          SDVOSB &amp; VOSB contracts are reserved for veteran-owned LLCs registered in SAM.gov.
        </p>
      </FilterSection>

      <FilterSection title="Solicitation Type">
        <select
          className="filter-input"
          value={filters.solicitation_type}
          onChange={e => onUpdate("solicitation_type", e.target.value)}
        >
          <option value="">All types</option>
          {SOLICITATION_TYPES.map(t => (
            <option key={t.code} value={t.code}>{t.label}</option>
          ))}
        </select>
      </FilterSection>

      <FilterSection title="Industry (NAICS Code)">
        <select
          className="filter-input"
          value={filters.naics_code}
          onChange={e => onUpdate("naics_code", e.target.value)}
        >
          <option value="">All industries</option>
          {COMMON_NAICS.map(n => (
            <option key={n.code} value={n.code}>{n.code} — {n.label}</option>
          ))}
        </select>
        <input
          type="text"
          className="filter-input mt-1"
          placeholder="Or enter NAICS code manually…"
          value={filters.naics_code.length === 6 && !COMMON_NAICS.find(n => n.code === filters.naics_code)
            ? filters.naics_code : ""}
          onChange={e => {
            const v = e.target.value.replace(/\D/g, "").slice(0, 6);
            if (v) onUpdate("naics_code", v);
          }}
        />
        {filters.naics_code && onRequestInsight && (
          <button
            type="button"
            onClick={() => onRequestInsight(filters.naics_code)}
            className="mt-2 w-full flex items-center justify-center gap-1.5 text-xs font-semibold
                       text-brand-600 hover:text-brand-700 bg-brand-50 hover:bg-brand-100
                       border border-brand-200 rounded-lg py-1.5 transition"
          >
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            View 12-month activity
          </button>
        )}
      </FilterSection>

      <FilterSection title="Agency / Department">
        <input
          type="text"
          className="filter-input"
          placeholder="e.g. Department of Defense"
          value={filters.agency}
          onChange={e => onUpdate("agency", e.target.value)}
        />
      </FilterSection>

      <FilterSection title="Place of Performance" defaultOpen={false}>
        <select
          className="filter-input"
          value={filters.state}
          onChange={e => onUpdate("state", e.target.value)}
        >
          <option value="">Any state / territory</option>
          {US_STATES.map(([code, name]) => (
            <option key={code} value={code}>{name}</option>
          ))}
        </select>
      </FilterSection>

      <FilterSection title="Posted Date Range" defaultOpen={false}>
        <div className="space-y-2">
          <div>
            <label className="filter-label">From</label>
            <input
              type="date"
              className="filter-input"
              value={filters.posted_from}
              onChange={e => {
                const d = e.target.value;
                if (!d) { onUpdate("posted_from", ""); return; }
                const [y, m, day] = d.split("-");
                onUpdate("posted_from", `${m}/${day}/${y}`);
              }}
            />
          </div>
          <div>
            <label className="filter-label">To</label>
            <input
              type="date"
              className="filter-input"
              value={filters.posted_to}
              onChange={e => {
                const d = e.target.value;
                if (!d) { onUpdate("posted_to", ""); return; }
                const [y, m, day] = d.split("-");
                onUpdate("posted_to", `${m}/${day}/${y}`);
              }}
            />
          </div>
        </div>
      </FilterSection>

      <FilterSection title="Response Deadline" defaultOpen={false}>
        <div className="space-y-2">
          <div>
            <label className="filter-label">From</label>
            <input
              type="date"
              className="filter-input"
              value={filters.response_deadline_from}
              onChange={e => {
                const d = e.target.value;
                if (!d) { onUpdate("response_deadline_from", ""); return; }
                const [y, m, day] = d.split("-");
                onUpdate("response_deadline_from", `${m}/${day}/${y}`);
              }}
            />
          </div>
          <div>
            <label className="filter-label">To</label>
            <input
              type="date"
              className="filter-input"
              value={filters.response_deadline_to}
              onChange={e => {
                const d = e.target.value;
                if (!d) { onUpdate("response_deadline_to", ""); return; }
                const [y, m, day] = d.split("-");
                onUpdate("response_deadline_to", `${m}/${day}/${y}`);
              }}
            />
          </div>
        </div>
      </FilterSection>

      <div className="pt-2">
        <button className="btn-primary w-full" onClick={onSearch}>
          Apply Filters
        </button>
      </div>
    </aside>
  );
}
