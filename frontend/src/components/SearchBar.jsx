import React, { useRef } from "react";

export default function SearchBar({ value, onChange, onSearch, loading }) {
  const inputRef = useRef(null);

  function handleKey(e) {
    if (e.key === "Enter") onSearch();
  }

  return (
    <div className="flex gap-2">
      <div className="relative flex-1">
        <span className="absolute inset-y-0 left-3 flex items-center text-gray-400 pointer-events-none">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M21 21l-4.35-4.35M17 11A6 6 0 1 1 5 11a6 6 0 0 1 12 0z" />
          </svg>
        </span>
        <input
          ref={inputRef}
          type="text"
          className="w-full pl-10 pr-4 py-3 rounded-xl border border-gray-200 bg-white text-base
                     shadow-sm focus:outline-none focus:ring-2 focus:ring-brand-500 transition"
          placeholder="Search contracts by keyword, agency, or description…"
          value={value}
          onChange={e => onChange(e.target.value)}
          onKeyDown={handleKey}
        />
        {value && (
          <button
            className="absolute inset-y-0 right-3 flex items-center text-gray-400 hover:text-gray-600"
            onClick={() => { onChange(""); inputRef.current?.focus(); }}
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>

      <button
        className="btn-primary flex items-center gap-2 min-w-[110px] justify-center"
        onClick={onSearch}
        disabled={loading}
      >
        {loading ? (
          <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
          </svg>
        ) : (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M21 21l-4.35-4.35M17 11A6 6 0 1 1 5 11a6 6 0 0 1 12 0z" />
          </svg>
        )}
        Search
      </button>
    </div>
  );
}
