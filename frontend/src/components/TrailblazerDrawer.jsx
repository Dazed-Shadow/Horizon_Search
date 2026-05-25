import { useEffect, useRef } from "react";
import { articles } from "../data/articles";

const RESOURCE_ICONS = {
  book:    { label: "Book",    color: "bg-amber-100 text-amber-800",  icon: "📖" },
  article: { label: "Article", color: "bg-blue-100 text-blue-800",   icon: "📰" },
  podcast: { label: "Podcast", color: "bg-purple-100 text-purple-800",icon: "🎙️" },
  video:   { label: "Video",   color: "bg-red-100 text-red-800",     icon: "▶️" },
};

export default function TrailblazerDrawer({ figure, onClose }) {
  const panelRef  = useRef(null);
  const closeRef  = useRef(null);
  const FOCUSABLE = 'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])';

  // Esc + focus trap + scroll lock — same pattern as ContractDetailDrawer
  useEffect(() => {
    if (!figure) return;
    document.body.style.overflow = "hidden";
    closeRef.current?.focus();

    const onKey = (e) => {
      if (e.key === "Escape") { onClose(); return; }
      if (e.key !== "Tab") return;
      const panel = panelRef.current;
      if (!panel) return;
      const focusable = [...panel.querySelectorAll(FOCUSABLE)];
      if (!focusable.length) return;
      const first = focusable[0], last = focusable[focusable.length - 1];
      if (e.shiftKey) { if (document.activeElement === first) { e.preventDefault(); last.focus(); } }
      else            { if (document.activeElement === last)  { e.preventDefault(); first.focus(); } }
    };
    document.addEventListener("keydown", onKey);
    return () => { document.removeEventListener("keydown", onKey); document.body.style.overflow = ""; };
  }, [figure, onClose]);

  if (!figure) return null;

  const relatedArticles = articles.filter(a => a.featured_figure_slug === figure.slug);

  return (
    <>
      <div className="fixed inset-0 bg-black/40 z-40 backdrop-fade-in" onClick={onClose} aria-hidden="true" />

      <aside
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-label={`${figure.name} — full profile`}
        className="fixed top-0 right-0 h-full w-full md:w-[clamp(400px,44vw,580px)]
                   bg-white shadow-2xl z-50 flex flex-col drawer-slide-in"
      >
        {/* Header */}
        <header className={`${figure.avatarColor} px-6 py-5 flex items-start justify-between gap-4 shrink-0`}>
          <div className="flex items-center gap-4">
            <div className="shrink-0 w-14 h-14 rounded-xl bg-white/20 flex items-center justify-center
                            text-white font-bold text-xl select-none">
              {figure.initials}
            </div>
            <div>
              <h2 className="text-xl font-bold text-white leading-tight">{figure.name}</h2>
              <p className="text-white/80 text-sm">{figure.branch} · {figure.yearsServed}</p>
              <p className="text-white/60 text-xs mt-0.5">{figure.era}</p>
            </div>
          </div>
          <button
            ref={closeRef}
            onClick={onClose}
            className="shrink-0 p-1.5 rounded-lg bg-white/10 hover:bg-white/25 text-white transition"
            aria-label="Close profile"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </header>

        {/* Scrollable body */}
        <div className="flex-1 overflow-y-auto">

          {/* Role + hook */}
          <div className="px-6 py-5 border-b border-gray-100">
            <p className="text-xs font-semibold uppercase tracking-widest text-brand-600 mb-1">
              {figure.role}
            </p>
            <p className="text-sm font-semibold text-gray-700 leading-relaxed italic">
              "{figure.oneLineHook}"
            </p>
          </div>

          {/* Full bio */}
          <div className="px-6 py-5 border-b border-gray-100">
            <p className="text-xs font-semibold uppercase tracking-wide text-gray-400 mb-3">Biography</p>
            {figure.bio.split("\n\n").map((para, i) => (
              <p key={i} className="text-sm text-gray-700 leading-relaxed mb-3 last:mb-0">{para}</p>
            ))}
          </div>

          {/* Tags */}
          <div className="px-6 py-4 border-b border-gray-100 flex flex-wrap gap-1.5">
            {figure.tags.map(tag => (
              <span key={tag}
                className="text-xs font-medium px-2.5 py-1 rounded-full bg-gray-100 text-gray-600">
                {tag}
              </span>
            ))}
          </div>

          {/* Resources */}
          <div className="px-6 py-5 border-b border-gray-100">
            <p className="text-xs font-semibold uppercase tracking-wide text-gray-400 mb-3">Books, articles & resources</p>
            <div className="space-y-3">
              {figure.resources.map((r, i) => {
                const meta = RESOURCE_ICONS[r.type] ?? RESOURCE_ICONS.article;
                return (
                  <a key={i} href={r.url} target="_blank" rel="noopener noreferrer"
                    className="flex gap-3 p-3 rounded-xl border border-gray-100 hover:border-brand-200
                               hover:bg-brand-50 transition group">
                    <span className="text-xl shrink-0 mt-0.5">{meta.icon}</span>
                    <div className="min-w-0">
                      <div className="flex items-center gap-2 flex-wrap mb-0.5">
                        <span className={`text-xs font-bold px-1.5 py-0.5 rounded ${meta.color}`}>
                          {meta.label}
                        </span>
                      </div>
                      <p className="text-sm font-semibold text-gray-800 group-hover:text-brand-700 leading-snug">
                        {r.title}
                      </p>
                      <p className="text-xs text-gray-500 mt-0.5">by {r.author}</p>
                      <p className="text-xs text-gray-500 leading-relaxed mt-1">{r.description}</p>
                    </div>
                  </a>
                );
              })}
            </div>
          </div>

          {/* Related articles */}
          {relatedArticles.length > 0 && (
            <div className="px-6 py-5 border-b border-gray-100">
              <p className="text-xs font-semibold uppercase tracking-wide text-gray-400 mb-3">
                Related articles
              </p>
              <div className="space-y-2">
                {relatedArticles.map(a => (
                  <a key={a.id} href={a.url} target="_blank" rel="noopener noreferrer"
                    className="block p-3 rounded-xl border border-gray-100 hover:border-brand-200
                               hover:bg-brand-50 transition">
                    <div className="flex items-start justify-between gap-2">
                      <p className="text-sm font-semibold text-gray-800 leading-snug">{a.title}</p>
                      <span className="shrink-0 text-xs text-gray-400 font-medium">{a.sourceShort}</span>
                    </div>
                    <p className="text-xs text-gray-500 mt-1 leading-relaxed">{a.summary}</p>
                  </a>
                ))}
              </div>
            </div>
          )}

          {/* External links */}
          <div className="px-6 py-5">
            <p className="text-xs font-semibold uppercase tracking-wide text-gray-400 mb-3">
              External links
            </p>
            <div className="flex flex-wrap gap-3">
              {figure.externalLinks.website && (
                <a href={figure.externalLinks.website} target="_blank" rel="noopener noreferrer"
                  className="text-sm font-semibold text-brand-600 hover:text-brand-700 hover:underline">
                  Official site ↗
                </a>
              )}
              {figure.externalLinks.wikipedia && (
                <a href={figure.externalLinks.wikipedia} target="_blank" rel="noopener noreferrer"
                  className="text-sm font-semibold text-brand-600 hover:text-brand-700 hover:underline">
                  Wikipedia ↗
                </a>
              )}
            </div>
          </div>

          <div className="h-4" />
        </div>

        {/* Footer */}
        <footer className="border-t border-gray-200 px-6 py-3 bg-white shrink-0">
          <p className="text-xs text-gray-400 text-center">
            Know a veteran whose story belongs here?{" "}
            <a href="mailto:the.riveraj@gmail.com?subject=Trailblazer suggestion"
              className="text-brand-600 hover:underline font-medium">
              Share their story →
            </a>
          </p>
        </footer>
      </aside>
    </>
  );
}
