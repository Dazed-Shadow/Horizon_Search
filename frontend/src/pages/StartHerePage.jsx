import React, { useState } from "react";
import { Link } from "react-router-dom";

const STEPS = [
  {
    number: "01",
    title: "Register your business on SAM.gov",
    tagline: "Required for every federal contract — no exceptions.",
    color: "brand",
    icon: (
      <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
          d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-2 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
      </svg>
    ),
    why: "SAM.gov (System for Award Management) is the federal government's official vendor database. Agencies cannot pay you if your business isn't registered here. Registration is free and takes about 1–3 business days to activate.",
    steps: [
      "Go to SAM.gov and create an account using your business email.",
      "Have your EIN (Employer Identification Number) ready — you'll need it.",
      "Enter your NAICS codes — these tell agencies what services you offer.",
      "Complete the representations and certifications (takes ~30 min).",
      "Submit and wait 1–3 days for activation.",
    ],
    note: "Renew your SAM.gov registration every year or you'll be locked out of contracts.",
    links: [
      { href: "https://sam.gov/content/home", label: "Register on SAM.gov ↗" },
      { href: "https://www.sba.gov/federal-contracting/contracting-guide/register-system-award-management", label: "SBA registration guide ↗" },
    ],
    faq: [
      { q: "Is SAM.gov registration really free?", a: "Yes — completely free. Never pay a third party to register for you. Scammers charge hundreds of dollars for a service the government provides at no cost." },
      { q: "What is a NAICS code?", a: "A 6-digit industry classification code. Every contract lists the NAICS code for the type of work. You need to have matching codes in your SAM.gov profile to bid." },
    ],
  },
  {
    number: "02",
    title: "Get your veteran set-aside certification",
    tagline: "Certifications unlock contracts reserved only for veteran businesses.",
    color: "green",
    icon: (
      <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
          d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
      </svg>
    ),
    why: "The federal government sets aside billions in contracts annually for certified veteran-owned businesses. Without certification, you're competing against every company in America. With it, you compete only against other veteran businesses — dramatically better odds.",
    steps: [
      "Determine which certifications apply: SDVOSB (service-disabled), VOSB (any veteran), 8(a) (socially/economically disadvantaged), HUBZone (geographic), WOSB (women-owned).",
      "For SDVOSB/VOSB: apply through the VA's VetCert program at vetbiz.va.gov.",
      "For 8(a), HUBZone, or WOSB: apply through certify.sba.gov.",
      "Gather your documents: DD-214, business formation docs, tax returns, operating agreements.",
      "Submit and wait — SDVOSB/VOSB takes 60–90 days; SBA programs vary.",
    ],
    note: "You can bid on SDVOSB contracts only after your VA certification is active. Start the process early.",
    links: [
      { href: "https://vetbiz.va.gov/vip/", label: "VA VetCert (SDVOSB/VOSB) ↗" },
      { href: "https://certify.sba.gov", label: "SBA Certify (8a/HUBZone/WOSB) ↗" },
    ],
    faq: [
      { q: "What's the difference between SDVOSB and VOSB?", a: "SDVOSB is for veterans with a service-connected disability rating from the VA. VOSB is for any honorably discharged veteran. SDVOSB contracts are more numerous and have stronger protections." },
      { q: "Can I have multiple certifications?", a: "Yes. Many veteran businesses hold both SDVOSB and 8(a) certifications, which opens two different pools of set-aside contracts." },
    ],
    internalLink: { to: "/licensing", label: "Full certification guide →" },
  },
  {
    number: "03",
    title: "Find and evaluate contracts",
    tagline: "That's what Horizon Search is for.",
    color: "indigo",
    icon: (
      <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
          d="M21 21l-4.35-4.35M17 11A6 6 0 1 1 5 11a6 6 0 0 1 12 0z" />
      </svg>
    ),
    why: "SAM.gov lists over 40,000 active opportunities at any time. Most aren't relevant to your business. Horizon Search filters to veteran set-asides, lets you sort by deadline and value, and translates the jargon so you can quickly decide what's worth pursuing.",
    steps: [
      "Use the quick filters at the top to find contracts matching your certification (e.g. 'All SDVOSB').",
      "Filter by your NAICS code to find work in your industry.",
      "Click any contract to open the detail view — check the deadline, agency, and description.",
      "Look for Sources Sought (type 'r') notices — responding early gets your company known to the agency.",
      "Bookmark contracts you want to pursue and revisit them from the 'Saved' panel.",
    ],
    note: "A Sources Sought response is not a bid. It's free marketing to the agency — always respond to relevant ones.",
    links: [],
    internalLink: { to: "/", label: "Search contracts now →" },
    faq: [
      { q: "What is a Sources Sought notice?", a: "The agency is doing market research before writing a formal solicitation. Responding tells them you exist and can do the work — and often shapes the final requirements in your favor. This is one of the highest-ROI activities for a new contractor." },
      { q: "How do I know if a contract is worth pursuing?", a: "Check: (1) Does your NAICS code match? (2) Is your certification type listed in the set-aside? (3) Is the deadline realistic? (4) Have you done similar work you can reference? If yes to all four, it's worth a closer read." },
    ],
  },
  {
    number: "04",
    title: "Write and submit your bid",
    tagline: "Your proposal is your first impression. Make it count.",
    color: "amber",
    icon: (
      <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
          d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
      </svg>
    ),
    why: "Federal agencies select vendors based on written proposals, not reputation alone. A well-structured proposal that directly addresses the Statement of Work — with clear pricing and past performance references — wins contracts regardless of company size.",
    steps: [
      "Read the full solicitation on SAM.gov — every word. Agencies disqualify bids that miss requirements.",
      "Attend any pre-proposal conference or site visit the agency offers.",
      "Write your technical approach to directly mirror the Statement of Work (SOW) sections.",
      "Include past performance: 3 references doing similar work, with dollar values and outcomes.",
      "Submit before the deadline — late submissions are automatically rejected.",
    ],
    note: "After a loss, you can request a debrief from the agency. Most will explain why you didn't win — use that to improve your next bid.",
    links: [
      { href: "https://www.acquisition.gov/far", label: "Federal Acquisition Regulation (FAR) ↗" },
      { href: "https://www.sba.gov/federal-contracting/contracting-guide/win-contract", label: "SBA winning a contract guide ↗" },
    ],
    internalLink: { to: "/primer", label: "Full 'How to Win' guide →" },
    faq: [
      { q: "Do I need a lawyer to submit a proposal?", a: "No. Most small business proposals are written by the business owner. What matters is clear writing and direct responses to the solicitation's requirements — not legal language." },
      { q: "What if I've never had a federal contract before?", a: "Mention relevant commercial or government subcontract work. Agencies understand that every contractor was new once. Starting with smaller contracts (under $250,000) builds your past performance record." },
    ],
  },
];

const COLOR = {
  brand:  { bg: "bg-brand-600",  light: "bg-brand-50",  border: "border-brand-200", text: "text-brand-700",  num: "text-brand-300" },
  green:  { bg: "bg-green-600",  light: "bg-green-50",  border: "border-green-200", text: "text-green-700",  num: "text-green-300" },
  indigo: { bg: "bg-indigo-600", light: "bg-indigo-50", border: "border-indigo-200",text: "text-indigo-700", num: "text-indigo-300" },
  amber:  { bg: "bg-amber-500",  light: "bg-amber-50",  border: "border-amber-200", text: "text-amber-700",  num: "text-amber-300" },
};

function StepCard({ step, index }) {
  const [openFaq, setOpenFaq] = useState(null);
  const c = COLOR[step.color];

  return (
    <section className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
      {/* Header band */}
      <div className={`${c.bg} px-6 py-5 flex items-start gap-4`}>
        <div className="shrink-0 bg-white/20 rounded-xl p-2.5 text-white">
          {step.icon}
        </div>
        <div className="flex-1 min-w-0">
          <p className={`text-xs font-bold uppercase tracking-widest ${c.num} mb-0.5`}>Step {step.number}</p>
          <h2 className="text-lg font-bold text-white leading-snug">{step.title}</h2>
          <p className="text-white/80 text-sm mt-0.5">{step.tagline}</p>
        </div>
      </div>

      <div className="px-6 py-5 space-y-5">
        {/* Why this matters */}
        <p className="text-sm text-gray-600 leading-relaxed">{step.why}</p>

        {/* Checklist */}
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-gray-400 mb-2">Action steps</p>
          <ol className="space-y-2">
            {step.steps.map((s, i) => (
              <li key={i} className="flex gap-3 text-sm text-gray-700">
                <span className={`shrink-0 w-5 h-5 rounded-full ${c.bg} text-white flex items-center justify-center text-xs font-bold mt-0.5`}>
                  {i + 1}
                </span>
                <span className="leading-relaxed">{s}</span>
              </li>
            ))}
          </ol>
        </div>

        {/* Pro tip */}
        <div className={`${c.light} ${c.border} border rounded-lg px-4 py-3 text-sm`}>
          <span className={`font-semibold ${c.text}`}>Pro tip: </span>
          <span className="text-gray-700">{step.note}</span>
        </div>

        {/* FAQ */}
        {step.faq?.length > 0 && (
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-gray-400 mb-2">Common questions</p>
            <div className="space-y-1">
              {step.faq.map((item, i) => (
                <div key={i} className="border border-gray-100 rounded-lg overflow-hidden">
                  <button
                    type="button"
                    onClick={() => setOpenFaq(openFaq === i ? null : i)}
                    className="w-full text-left px-4 py-3 text-sm font-medium text-gray-800 flex items-center justify-between gap-2 hover:bg-gray-50 transition"
                  >
                    <span>{item.q}</span>
                    <span className="shrink-0 text-gray-400">{openFaq === i ? "▲" : "▼"}</span>
                  </button>
                  {openFaq === i && (
                    <div className="px-4 pb-3 text-sm text-gray-600 leading-relaxed border-t border-gray-100 pt-2">
                      {item.a}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Links */}
        {(step.links?.length > 0 || step.internalLink) && (
          <div className="flex flex-wrap gap-3 pt-1">
            {step.links?.map(l => (
              <a key={l.href} href={l.href} target="_blank" rel="noopener noreferrer"
                className="text-sm font-semibold text-brand-600 hover:text-brand-700 hover:underline">
                {l.label}
              </a>
            ))}
            {step.internalLink && (
              <Link to={step.internalLink.to}
                className="text-sm font-semibold text-brand-600 hover:text-brand-700 hover:underline">
                {step.internalLink.label}
              </Link>
            )}
          </div>
        )}
      </div>
    </section>
  );
}

export default function StartHerePage() {
  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-10">

      {/* Hero */}
      <div className="text-center mb-10">
        <div className="inline-flex items-center gap-2 bg-green-100 text-green-800 rounded-full px-4 py-1.5 text-sm font-semibold mb-4">
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
          </svg>
          Built for veteran business owners
        </div>
        <h1 className="text-3xl font-bold text-gray-900 mb-3">Your road map to winning federal contracts</h1>
        <p className="text-gray-500 text-base leading-relaxed max-w-xl mx-auto">
          The federal government is legally required to award a portion of its contracts to veteran-owned businesses.
          These four steps are all you need to get your first one.
        </p>
      </div>

      {/* Step progress strip */}
      <div className="flex items-center gap-2 mb-8 overflow-x-auto pb-1">
        {STEPS.map((step, i) => (
          <React.Fragment key={step.number}>
            <div className={`shrink-0 flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-bold ${COLOR[step.color].bg} text-white`}>
              <span>{step.number}</span>
              <span className="hidden sm:inline">{step.title.split(" ").slice(0, 2).join(" ")}</span>
            </div>
            {i < STEPS.length - 1 && <div className="shrink-0 w-5 h-px bg-gray-300" />}
          </React.Fragment>
        ))}
      </div>

      {/* Step cards */}
      <div className="space-y-6">
        {STEPS.map((step, i) => <StepCard key={step.number} step={step} index={i} />)}
      </div>

      {/* Bottom CTA */}
      <div className="mt-10 bg-brand-900 rounded-2xl p-8 text-center text-white">
        <h2 className="text-xl font-bold mb-2">Ready to find your first contract?</h2>
        <p className="text-brand-200 text-sm mb-5">
          Horizon Search shows you active opportunities filtered to your set-aside type — with plain-English explanations on every card.
        </p>
        <Link to="/"
          className="inline-block bg-white text-brand-700 font-bold px-6 py-3 rounded-xl hover:bg-brand-50 transition text-sm">
          Search active contracts →
        </Link>
      </div>
    </div>
  );
}
