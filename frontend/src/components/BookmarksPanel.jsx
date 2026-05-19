// Bookmark / watch list: a slide-in panel (same drawer pattern as ContractDetailDrawer) that lists saved contracts.
// Renders compact rows with title, agency, urgency-colored deadline, Remove and Open buttons; newest bookmark first.
import { useEffect, useRef } from "react";
import { formatDate } from "../utils/formatters";
import { deadlineStatus } from "../utils/formatters";

function EmptyBookmarks() {
  return (
    <div className="flex flex-col items-center justify-center h-full px-8 text-center">
      <svg className="w-16 h-16 text-gray-200 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
          d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
      </svg>
      <p className="font-semibold text-gray-500 mb-2">No saved contracts yet</p>
      <p className="text-sm text-gray-400 leading-relaxed">
        Click the bookmark icon on any contract card to save it here.
        Your saved contracts stay between visits — no account needed.
      </p>
    </div>
  );
}

export default function BookmarksPanel({ bookmarks, onClose, onOpen, onRemove }) {
  const closeButtonRef = useRef(null);

  // Esc to close + body scroll lock (same pattern as ContractDetailDrawer)
  useEffect(() => {
    const onKey = (e) => { if (e.key === "Escape") onClose(); };
    document.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
    };
  }, [onClose]);

  useEffect(() => { closeButtonRef.current?.focus(); }, []);

  return (
    <>
      <div className="fixed inset-0 bg-black/40 z-40" onClick={onClose} aria-hidden="true" />

      <aside
        role="dialog"
        aria-modal="true"
        aria-label="Saved contracts"
        className="fixed top-0 right-0 h-full w-full md:w-[clamp(360px,40vw,520px)]
                   bg-white shadow-2xl z-50 flex flex-col"
      >
        <header className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 z-10 flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Saved contracts</h2>
            <p className="text-sm text-gray-500">
              {bookmarks.length === 0 ? "None saved" : `${bookmarks.length} saved`}
            </p>
          </div>
          <button
            ref={closeButtonRef}
            onClick={onClose}
            className="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition"
            aria-label="Close saved contracts panel"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </header>

        <div className="flex-1 overflow-y-auto">
          {bookmarks.length === 0 ? (
            <EmptyBookmarks />
          ) : (
            <ul className="divide-y divide-gray-100">
              {bookmarks.map(({ notice_id, bookmarked_at, contract }) => {
                const dl = deadlineStatus(contract.response_deadline);
                return (
                  <li key={notice_id} className="px-6 py-4">
                    <p className="font-semibold text-gray-900 text-sm leading-snug line-clamp-2 mb-0.5">
                      {contract.title}
                    </p>
                    <p className="text-xs text-gray-500 truncate mb-2">
                      {[contract.agency, contract.sub_agency].filter(Boolean).join(" › ")}
                    </p>
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        {contract.response_deadline ? (
                          <span className={`text-xs font-medium ${dl?.color ?? "text-gray-500"}`}>
                            {formatDate(contract.response_deadline)}
                            {dl && <span className="ml-1">({dl.label})</span>}
                          </span>
                        ) : (
                          <span className="text-xs text-gray-400">No deadline</span>
                        )}
                        <p className="text-xs text-gray-400 mt-0.5">
                          Saved {new Date(bookmarked_at).toLocaleDateString("en-US", { month: "short", day: "numeric" })}
                        </p>
                      </div>
                      <div className="flex gap-2 shrink-0">
                        <button
                          onClick={() => onRemove(notice_id)}
                          className="text-xs px-3 py-1.5 border border-gray-200 text-gray-500
                                     rounded-lg hover:bg-gray-50 hover:text-red-600 transition"
                        >
                          Remove
                        </button>
                        <button
                          onClick={() => onOpen(contract)}
                          className="text-xs px-3 py-1.5 bg-brand-600 text-white
                                     rounded-lg hover:bg-brand-700 transition font-semibold"
                        >
                          Open
                        </button>
                      </div>
                    </div>
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      </aside>
    </>
  );
}
