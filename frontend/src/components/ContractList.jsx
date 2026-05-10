import React from "react";
import ContractCard from "./ContractCard";
import Pagination from "./Pagination";

function EmptyState({ hasFilters }) {
  return (
    <div className="text-center py-16 text-gray-400">
      <svg className="w-14 h-14 mx-auto mb-4 text-gray-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
          d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
      <p className="text-lg font-semibold text-gray-500">No contracts found</p>
      <p className="text-sm mt-1">
        {hasFilters ? "Try broadening your filters or changing keywords." : "Use the search bar above to find contracts."}
      </p>
    </div>
  );
}

function RateLimitState() {
  return (
    <div className="text-center py-16">
      <svg className="w-14 h-14 mx-auto mb-4 text-amber-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
          d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <p className="text-lg font-semibold text-amber-600">Search limit reached</p>
      <p className="text-sm text-gray-500 mt-2 max-w-sm mx-auto">
        The SAM.gov free API allows a limited number of searches per day.
        Wait a few minutes and try again — your results will be back shortly.
      </p>
      <p className="text-xs text-gray-400 mt-3">
        Tip: repeated searches for the same filters are cached and won't use your quota.
      </p>
    </div>
  );
}

function ErrorState({ message }) {
  return (
    <div className="text-center py-16">
      <svg className="w-14 h-14 mx-auto mb-4 text-red-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
          d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
      </svg>
      <p className="text-lg font-semibold text-red-500">Search failed</p>
      <p className="text-sm text-gray-500 mt-1 max-w-md mx-auto">{message}</p>
    </div>
  );
}

export default function ContractList({ results, loading, error, page, limit, onPageChange, hasFilters }) {
  if (loading) {
    return (
      <div className="space-y-4">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="bg-white rounded-xl border border-gray-200 p-5 animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-3/4 mb-3" />
            <div className="h-3 bg-gray-100 rounded w-1/2 mb-4" />
            <div className="flex gap-2 mb-4">
              <div className="h-5 bg-gray-100 rounded-full w-24" />
              <div className="h-5 bg-gray-100 rounded-full w-20" />
            </div>
            <div className="grid grid-cols-4 gap-3">
              {[...Array(4)].map((_, j) => (
                <div key={j} className="h-8 bg-gray-100 rounded" />
              ))}
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (error === "__RATE_LIMIT__") return <RateLimitState />;
  if (error) return <ErrorState message={error} />;
  if (!results) return <EmptyState hasFilters={false} />;
  if (results.contracts.length === 0) return <EmptyState hasFilters={hasFilters} />;

  return (
    <div>
      <p className="text-sm text-gray-500 mb-4">
        Found <span className="font-semibold text-gray-800">{results.total.toLocaleString()}</span> active contracts
      </p>

      <div className="space-y-4">
        {results.contracts.map(contract => (
          <ContractCard key={contract.notice_id} contract={contract} />
        ))}
      </div>

      <Pagination
        total={results.total}
        limit={limit}
        page={page}
        onPageChange={onPageChange}
      />
    </div>
  );
}
