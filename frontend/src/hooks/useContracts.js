import { useState, useCallback, useRef } from "react";
import { buildQueryString } from "../utils/formatters";

const INITIAL_FILTERS = {
  keyword: "",
  set_aside: "",
  naics_code: "",
  agency: "",
  solicitation_type: "",
  posted_from: "",
  posted_to: "",
  response_deadline_from: "",
  response_deadline_to: "",
  state: "",
  open_only: true,   // hide already-awarded contracts by default
};

export function useContracts() {
  const [filters, setFilters] = useState(INITIAL_FILTERS);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(0);
  const limit = 25;
  const abortRef = useRef(null);

  const search = useCallback(async (overrideFilters = null, pageOverride = 0) => {
    if (abortRef.current) abortRef.current.abort();
    abortRef.current = new AbortController();

    const activeFilters = overrideFilters ?? filters;
    const offset = pageOverride * limit;

    setLoading(true);
    setError(null);

    try {
      const { open_only, ...apiFilters } = activeFilters;
    const qs = buildQueryString({ ...apiFilters, open_only: open_only ? "true" : "false", limit, offset });
      const res = await fetch(`/api/contracts/search?${qs}`, {
        signal: abortRef.current.signal,
      });

      if (!res.ok) {
        if (res.status === 429) {
          throw new Error("__RATE_LIMIT__");
        }
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `Server error ${res.status}`);
      }

      const data = await res.json();
      setResults(data);
      setPage(pageOverride);
    } catch (err) {
      if (err.name !== "AbortError") {
        setError(err.message);
        setResults(null);
      }
    } finally {
      setLoading(false);
    }
  }, [filters]);

  const updateFilter = useCallback((key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  }, []);

  const resetFilters = useCallback(() => {
    setFilters(INITIAL_FILTERS);
    setResults(null);
    setError(null);
    setPage(0);
  }, []);

  const goToPage = useCallback((newPage) => {
    search(filters, newPage);
  }, [search, filters]);

  return {
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
  };
}
