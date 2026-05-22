import { useEffect, useRef, useState } from "react";
import { formatDate, formatCurrency } from "../utils/formatters";
import { SET_ASIDE_COLORS, VETERAN_CODES } from "../utils/constants";
import { SET_ASIDE_EXPLANATIONS, SOLICITATION_TYPE_EXPLANATIONS } from "../utils/explainers";
import LiveCountdown from "./LiveCountdown";

function relativeDate(dateStr) {
  if (!dateStr) return null;
  const days = Math.round((Date.now() - new Date(dateStr).getTime()) / 86_400_000);
  if (days === 0) return "Today";
  if (days === 1) return "Yesterday";
  if (days < 0)  return `In ${Math.abs(days)} days`;
  return `${days} days ago`;
}

function SectionLabel({ children }) {
  return (
    <p className="text-xs font-semibold uppercase tracking-wide text-gray-400 mb-2">
      {children}
    </p>
  );
}

function ExplainerCard({ heading, title, summary, eligibilityLabel, eligibility, action, learnMore, accentColor = "green" }) {
  const colors = {
    green:  { bg: "bg-green-50",  border: "border-green-200",  head: "text-green-800",  body: "text-green-700" },
    indigo: { bg: "bg-indigo-50", border: "border-indigo-200", head: "text-indigo-800", body: "text-indigo-700" },
    blue:   { bg: "bg-blue-50",   border: "border-blue-200",   head: "text-blue-800",   body: "text-blue-700" },
  };
  const c = colors[accentColor] ?? colors.green;

  return (
    <section className="py-5 border-b border-gray-100">
      <SectionLabel>{heading}</SectionLabel>
      <p className="font-semibold text-gray-800 mb-1">{title}</p>
      <p className="text-sm text-gray-600 leading-relaxed">{summary}</p>
      {(eligibility || action) && (
        <div className={`mt-3 ${c.bg} border ${c.border} rounded-lg p-3 text-sm`}>
          <p className={`font-semibold ${c.head} mb-0.5`}>{eligibilityLabel || "Who can bid"}</p>
          <p className={`${c.body} leading-relaxed`}>{eligibility ?? action}</p>
        </div>
      )}
      {learnMore && (
        <a href={learnMore} target="_blank" rel="noopener noreferrer"
          className="text-xs text-brand-600 hover:underline mt-2 inline-block">
          Learn more about this program ↗
        </a>
      )}
    </section>
  );
}

// Drawer polish: slide-in animation via CSS keyframe, full keyboard focus trap (Tab/Shift+Tab cycles
// within the panel), and Esc-to-close all coexist in a single keydown handler.
export default function ContractDetailDrawer({ contract, onClose, isBookmarked, onToggleBookmark }) {
  const closeButtonRef = useRef(null);
  const panelRef = useRef(null);
  const bodyRef = useRef(null);
  const [copied, setCopied] = useState(false);

  const FOCUSABLE = 'a[href], button:not([disabled]), input, select, textarea, [tabindex]:not([tabindex="-1"])';

  useEffect(() => {
    if (!contract) return;
    document.body.style.overflow = "hidden";

    const onKey = (e) => {
      if (e.key === "Escape") { onClose(); return; }
      if (e.key !== "Tab") return;

      // Focus trap: cycle within the drawer panel
      const panel = panelRef.current;
      if (!panel) return;
      const focusable = [...panel.querySelectorAll(FOCUSABLE)];
      if (focusable.length === 0) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];

      if (e.shiftKey) {
        if (document.activeElement === first) { e.preventDefault(); last.focus(); }
      } else {
        if (document.activeElement === last) { e.preventDefault(); first.focus(); }
      }
    };

    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
    };
  }, [contract, onClose]);

  // Focus close button when drawer opens
  useEffect(() => {
    if (contract) closeButtonRef.current?.focus();
  }, [contract]);

  // Scroll drawer body to top when a different contract opens
  useEffect(() => {
    if (contract && bodyRef.current) bodyRef.current.scrollTop = 0;
  }, [contract?.notice_id]);

  if (!contract) return null;

  const bookmarked = isBookmarked?.(contract.notice_id) ?? false;

  const setAsideExplainer = contract.set_aside_code
    ? (SET_ASIDE_EXPLANATIONS[contract.set_aside_code] ?? null)
    : null;

  const setAsideGroup = VETERAN_CODES.has(contract.set_aside_code) ? "Veteran"
    : (contract.set_aside_code?.startsWith("WOSB") || contract.set_aside_code?.startsWith("EDWOSB")) ? "Women-Owned"
    : "Small Business";
  const setAsideBadgeColor = SET_ASIDE_COLORS[setAsideGroup] || SET_ASIDE_COLORS.Other;

  const noticeExplainer = contract.solicitation_type
    ? (SOLICITATION_TYPE_EXPLANATIONS[contract.solicitation_type] ?? null)
    : null;

  function handleCopyLink() {
    if (!contract.ui_link) return;
    navigator.clipboard.writeText(contract.ui_link).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/40 z-40 backdrop-fade-in"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Drawer panel — slide-in-right animation on every open */}
      <aside
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="drawer-title"
        className="fixed top-0 right-0 h-full w-full md:w-[clamp(380px,42vw,560px)]
                   bg-white shadow-2xl z-50 flex flex-col drawer-slide-in"
      >
        {/* ── Sticky header ─────────────────────────────────────────── */}
        <header className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 z-10">
          <div className="flex items-start justify-between gap-3 mb-3">
            <div className="flex-1 min-w-0">
              <h2 id="drawer-title" className="text-xl font-semibold text-gray-900 leading-snug">
                {contract.title}
              </h2>
              {(contract.agency || contract.sub_agency || contract.office) && (
                <p className="text-sm text-gray-500 mt-1">
                  {[contract.agency, contract.sub_agency, contract.office].filter(Boolean).join(" › ")}
                </p>
              )}
            </div>
            <button
              ref={closeButtonRef}
              onClick={onClose}
              className="shrink-0 p-1.5 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition"
              aria-label="Close detail panel"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Primary action buttons */}
          <div className="flex gap-2">
            {contract.ui_link && (
              <a
                href={contract.ui_link}
                target="_blank"
                rel="noopener noreferrer"
                className="flex-1 text-center text-sm font-semibold bg-brand-600 text-white
                           rounded-lg px-3 py-2 hover:bg-brand-700 transition"
              >
                View on SAM.gov ↗
              </a>
            )}
            {contract.ui_link && (
              <button
                onClick={handleCopyLink}
                className="text-sm font-semibold border border-gray-200 text-gray-600
                           rounded-lg px-3 py-2 hover:bg-gray-50 transition min-w-[90px]"
              >
                {copied ? "Copied ✓" : "Copy link"}
              </button>
            )}
          </div>
        </header>

        {/* ── Scrollable body ───────────────────────────────────────── */}
        <div ref={bodyRef} className="flex-1 overflow-y-auto px-6">

          {/* Section B: At-a-glance stats */}
          <section className="py-5 border-b border-gray-100">
            <SectionLabel>At a glance</SectionLabel>
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-gray-50 rounded-xl p-3">
                <p className="text-xs text-gray-400 mb-1">Time remaining</p>
                <p className="text-lg font-bold">
                  <LiveCountdown deadline={contract.response_deadline} />
                </p>
              </div>
              <div className="bg-gray-50 rounded-xl p-3">
                <p className="text-xs text-gray-400 mb-1">Response deadline</p>
                <p className="text-sm font-semibold text-gray-800">
                  {formatDate(contract.response_deadline) || "Not specified"}
                </p>
              </div>
              <div className="bg-gray-50 rounded-xl p-3">
                <p className="text-xs text-gray-400 mb-1">Posted</p>
                <p className="text-sm font-semibold text-gray-800">
                  {formatDate(contract.posted_date) || "—"}
                  {contract.posted_date && (
                    <span className="block text-xs text-gray-400 font-normal mt-0.5">
                      {relativeDate(contract.posted_date)}
                    </span>
                  )}
                </p>
              </div>
              <div className="bg-gray-50 rounded-xl p-3">
                <p className="text-xs text-gray-400 mb-1">Award amount</p>
                <p className="text-sm font-semibold text-gray-800">
                  {contract.award_amount ? formatCurrency(contract.award_amount) : "Not specified"}
                </p>
              </div>
            </div>

            {/* Badges */}
            <div className="flex flex-wrap gap-1.5 mt-3">
              {contract.set_aside_label && (
                <span className={`badge ${setAsideBadgeColor}`}>{contract.set_aside_label}</span>
              )}
              {contract.solicitation_type_label && (
                <span className="badge bg-gray-100 text-gray-700">{contract.solicitation_type_label}</span>
              )}
              {contract.naics_code && (
                <span className="badge bg-indigo-50 text-indigo-700">NAICS {contract.naics_code}</span>
              )}
              {contract.place_of_performance && (
                <span className="badge bg-gray-100 text-gray-600">{contract.place_of_performance}</span>
              )}
            </div>
          </section>

          {/* Section C: Set-aside explainer */}
          {setAsideExplainer ? (
            <ExplainerCard
              heading="What this set-aside means"
              title={setAsideExplainer.title}
              summary={setAsideExplainer.summary}
              eligibility={setAsideExplainer.eligibility}
              learnMore={setAsideExplainer.learnMore}
              accentColor="green"
            />
          ) : contract.set_aside_code ? (
            <section className="py-5 border-b border-gray-100">
              <SectionLabel>Set-aside type</SectionLabel>
              <p className="text-sm font-semibold text-gray-800">{contract.set_aside_code}</p>
              <p className="text-sm text-gray-500 mt-1">
                This contract has a specific set-aside designation. Check SAM.gov for full eligibility requirements.
              </p>
            </section>
          ) : null}

          {/* Section C: Solicitation type explainer */}
          {noticeExplainer ? (
            <ExplainerCard
              heading="What this notice type means"
              title={noticeExplainer.title}
              summary={noticeExplainer.summary}
              eligibilityLabel="What to do"
              eligibility={noticeExplainer.action}
              accentColor="blue"
            />
          ) : null}

          {/* Section C: NAICS explainer */}
          {contract.naics_code && (
            <section className="py-5 border-b border-gray-100">
              <SectionLabel>NAICS code — industry classification</SectionLabel>
              <p className="font-semibold text-gray-800 font-mono">{contract.naics_code}</p>
              {contract.naics_description && (
                <p className="text-sm text-gray-600 mt-0.5">{contract.naics_description}</p>
              )}
              <div className="mt-3 bg-indigo-50 border border-indigo-200 rounded-lg p-3 text-sm">
                <p className="font-semibold text-indigo-800 mb-0.5">Why this matters</p>
                <p className="text-indigo-700 leading-relaxed">
                  Your business must have this NAICS code in its SAM.gov registration to be eligible to bid.
                  You can add NAICS codes in your SAM.gov entity profile at any time.
                </p>
              </div>
              <a
                href={`https://www.naics.com/naics-code-description/?code=${contract.naics_code}`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-brand-600 hover:underline mt-2 inline-block"
              >
                Look up NAICS {contract.naics_code} details ↗
              </a>
            </section>
          )}

          {/* Section D: Full description */}
          <section className="py-5 border-b border-gray-100">
            <SectionLabel>Description</SectionLabel>
            {contract.description ? (
              <p className="text-sm text-gray-600 leading-relaxed whitespace-pre-line">
                {contract.description}
              </p>
            ) : (
              <p className="text-sm text-gray-400 italic">
                No description provided by the agency. View the full solicitation on SAM.gov for details.
              </p>
            )}
          </section>

          {/* Section E: POC + IDs */}
          <section className="py-5 border-b border-gray-100">
            <SectionLabel>Point of contact</SectionLabel>
            {contract.contact?.name || contract.contact?.email || contract.contact?.phone ? (
              <div className="space-y-1 text-sm">
                {contract.contact.name && (
                  <p className="font-semibold text-gray-800">{contract.contact.name}</p>
                )}
                {contract.contact.email && (
                  <a href={`mailto:${contract.contact.email}`}
                    className="block text-brand-600 hover:underline">
                    {contract.contact.email}
                  </a>
                )}
                {contract.contact.phone && (
                  <a href={`tel:${contract.contact.phone}`}
                    className="block text-gray-600 hover:underline">
                    {contract.contact.phone}
                  </a>
                )}
              </div>
            ) : (
              <p className="text-sm text-gray-400 italic">No contact information available.</p>
            )}

            <div className="mt-4 space-y-2">
              {contract.solicitation_number && (
                <div>
                  <p className="text-xs text-gray-400 mb-0.5">Solicitation number</p>
                  <p className="font-mono text-sm text-gray-700">{contract.solicitation_number}</p>
                </div>
              )}
              {contract.notice_id && (
                <div>
                  <p className="text-xs text-gray-400 mb-0.5">Notice ID</p>
                  <p className="font-mono text-xs text-gray-500">{contract.notice_id}</p>
                </div>
              )}
              {contract.place_of_performance && (
                <div>
                  <p className="text-xs text-gray-400 mb-0.5">Place of performance</p>
                  <p className="text-sm text-gray-700">{contract.place_of_performance}</p>
                </div>
              )}
            </div>
          </section>

          {/* Bottom padding */}
          <div className="h-4" />
        </div>

        {/* ── Sticky footer ─────────────────────────────────────────── */}
        <footer className="sticky bottom-0 bg-white border-t border-gray-200 px-6 py-3 flex gap-3">
          {contract.ui_link ? (
            <a
              href={contract.ui_link}
              target="_blank"
              rel="noopener noreferrer"
              className="flex-1 text-center text-sm font-semibold bg-brand-600 text-white
                         rounded-lg px-4 py-2.5 hover:bg-brand-700 transition"
            >
              Respond on SAM.gov ↗
            </a>
          ) : (
            <div className="flex-1" />
          )}
          <button
            onClick={() => onToggleBookmark?.(contract)}
            className={`text-sm font-semibold border rounded-lg px-4 py-2.5 transition ${
              bookmarked
                ? "border-amber-300 bg-amber-50 text-amber-700 hover:bg-amber-100"
                : "border-gray-200 text-gray-600 hover:bg-gray-50"
            }`}
          >
            {bookmarked ? "Saved ✓" : "Save for later"}
          </button>
        </footer>
      </aside>
    </>
  );
}
