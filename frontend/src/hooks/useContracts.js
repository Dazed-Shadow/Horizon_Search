import { useState, useCallback, useRef, useMemo } from "react";
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

// Sort controls: let users reorder the current page of results by deadline, posted date, or award value.
// sortBy lives in this hook alongside results so it resets automatically when a new search fires.
export function useContracts() {
  const [filters, setFilters] = useState(INITIAL_FILTERS);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(0);
  const [sortBy, setSortBy] = useState("default");
  const limit = 25;
  const abortRef = useRef(null);

  const search = useCallback(async (overrideFilters = null, pageOverride = 0) => {
    if (abortRef.current) abortRef.current.abort();
    abortRef.current = new AbortController();

    const activeFilters = overrideFilters ?? filters;
    const offset = pageOverride * limit;

    setLoading(true);
    setError(null);
    setSortBy("default");

    try {
      const { open_only, ...apiFilters } = activeFilters;
    const qs = buildQueryString({ ...apiFilters, open_only: open_only ? "true" : "false", limit, offset });
      const API_BASE = import.meta.env.VITE_API_URL ?? "";
      const res = await fetch(`${API_BASE}/api/contracts/search?${qs}`, {
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

  // Derive a sorted copy of the current page's contracts; nulls always sort to the end.
  // Sort applies only to the fetched page — server owns total count and pagination.
  const sortedContracts = useMemo(() => {
    const contracts = results?.contracts;
    if (!contracts || sortBy === "default") return contracts ?? [];
    const arr = [...contracts];
    if (sortBy === "deadline") {
      arr.sort((a, b) => {
        if (!a.response_deadline) return 1;
        if (!b.response_deadline) return -1;
        return new Date(a.response_deadline) - new Date(b.response_deadline);
      });
    } else if (sortBy === "posted") {
      arr.sort((a, b) => {
        if (!a.posted_date) return 1;
        if (!b.posted_date) return -1;
        return new Date(b.posted_date) - new Date(a.posted_date);
      });
    } else if (sortBy === "award") {
      arr.sort((a, b) => {
        if (a.award_amount == null) return 1;
        if (b.award_amount == null) return -1;
        return b.award_amount - a.award_amount;
      });
    }
    return arr;
  }, [results?.contracts, sortBy]);

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
    sortBy,
    setSortBy,
    sortedContracts,
  };
}
