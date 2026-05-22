import React, { useState } from "react";
import { Link } from "react-router-dom";
import { testimonials, founderNote } from "../data/testimonials";
import ShareButton from "../components/ShareButton";

const CERT_COLORS = {
  SDVOSB: "bg-green-100 text-green-800 border-green-200",
  VOSB:   "bg-green-100 text-green-800 border-green-200",
  "8AN":  "bg-blue-100 text-blue-800 border-blue-200",
  HZC:    "bg-blue-100 text-blue-800 border-blue-200",
  WOSB:   "bg-purple-100 text-purple-800 border-purple-200",
  SBA:    "bg-gray-100 text-gray-700 border-gray-200",
};

const VALUES = [
  {
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
          d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
      </svg>
    ),
    title: "Plain language, always",
    body: "Federal contracting has its own language — SAM.gov, NAICS codes, set-asides, FAR clauses. Every feature on this platform is designed to translate that language into plain English so no veteran is locked out by jargon.",
  },
  {
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
          d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
      </svg>
    ),
    title: "Built for newcomers first",
    body: "Every design decision starts with one question: would someone encountering federal contracting for the first time understand this? If not, we rethink it. Veterans who've won dozens of contracts should find it useful. Veterans on day one should feel at home.",
  },
  {
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
          d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
      </svg>
    ),
    title: "No account required",
    body: "Bookmarks save to your browser. Nothing is tracked. No email required. The only goal is to put the right contract in front of the right veteran — everything else is friction we don't want to create.",
  },
];

function TestimonialCard({ t }) {
  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 flex flex-col">
      {/* Large decorative quote mark */}
      <div className="text-5xl font-serif leading-none text-brand-200 select-none mb-2">"</div>
      <blockquote className="text-gray-700 text-sm leading-relaxed flex-1 mb-4">
        {t.quote}
      </blockquote>
      <div className="flex items-end justify-between gap-3 mt-auto pt-4 border-t border-gray-100">
        <div>
          <p className="font-semibold text-gray-900 text-sm">{t.name}</p>
          <p className="text-gray-400 text-xs mt-0.5">{t.company} · {t.state}</p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {t.certification && (
            <span className={`text-xs font-bold px-2 py-0.5 rounded-full border ${CERT_COLORS[t.certification] ?? "bg-gray-100 text-gray-700 border-gray-200"}`}>
              {t.certification}
            </span>
          )}
          {t.sourceUrl && (
            <a href={t.sourceUrl} target="_blank" rel="noopener noreferrer"
              className="text-xs text-brand-600 hover:underline font-medium">
              Story ↗
            </a>
          )}
        </div>
      </div>
    </div>
  );
}

export default function MissionPage() {
  return (
    <div className="flex flex-col">

      {/* ── Hero ────────────────────────────────────────────────────────── */}
      <div className="relative bg-brand-900 overflow-hidden">
        {/* Decorative background rings */}
        <div className="absolute inset-0 pointer-events-none overflow-hidden">
          <div className="absolute -top-32 -right-32 w-96 h-96 rounded-full bg-brand-700/30 blur-3xl" />
          <div className="absolute -bottom-20 -left-20 w-80 h-80 rounded-full bg-green-900/30 blur-3xl" />
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full border border-white/5" />
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] rounded-full border border-white/5" />
        </div>

        <div className="relative max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-20 text-center">
          <div className="inline-flex items-center gap-2 bg-green-500/20 text-green-300 border border-green-500/30 rounded-full px-4 py-1.5 text-sm font-semibold mb-6">
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
            </svg>
            Veteran Contract Intelligence
          </div>
          <h1 className="text-4xl sm:text-5xl font-bold text-white leading-tight mb-5">
            Veterans deserve more than<br className="hidden sm:block" /> a thank-you.
          </h1>
          <p className="text-brand-200 text-lg leading-relaxed max-w-2xl mx-auto mb-8">
            The federal government is legally required to set aside billions of dollars in contracts
            for veteran-owned businesses every year. Horizon Search exists to make sure every veteran
            who has earned that right can actually find and pursue those opportunities.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-3">
            <Link to="/" className="bg-white text-brand-700 font-bold px-6 py-3 rounded-xl hover:bg-brand-50 transition text-sm">
              Search contracts →
            </Link>
            <Link to="/start" className="bg-green-600/30 text-green-200 border border-green-500/40 font-bold px-6 py-3 rounded-xl hover:bg-green-600/50 transition text-sm">
              New? Start here →
            </Link>
            <ShareButton />
          </div>
        </div>
      </div>

      {/* ── What we believe ─────────────────────────────────────────────── */}
      <div className="bg-gray-50 border-b border-gray-200 py-14">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-2xl font-bold text-gray-900 text-center mb-2">What we believe</h2>
          <p className="text-gray-500 text-center text-sm mb-10">The principles behind every design decision on this platform.</p>
          <div className="grid sm:grid-cols-3 gap-6">
            {VALUES.map(v => (
              <div key={v.title} className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6">
                <div className="w-11 h-11 bg-brand-100 text-brand-600 rounded-xl flex items-center justify-center mb-4">
                  {v.icon}
                </div>
                <h3 className="font-bold text-gray-900 mb-2">{v.title}</h3>
                <p className="text-sm text-gray-500 leading-relaxed">{v.body}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── About the builder ───────────────────────────────────────────── */}
      <div className="bg-white py-14 border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col sm:flex-row gap-10 items-start">
            {/* Logo placeholder — backlog item */}
            <div className="shrink-0 w-20 h-20 rounded-2xl bg-brand-900 flex items-center justify-center self-start">
              <svg className="w-10 h-10 text-white/70" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                  d="M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16H9m3 0h3" />
              </svg>
            </div>
            <div className="flex-1">
              <p className="text-xs font-semibold uppercase tracking-widest text-gray-400 mb-2">About the builder</p>
              <h2 className="text-2xl font-bold text-gray-900 mb-1">{founderNote.name}</h2>
              <p className="text-brand-600 text-sm font-medium mb-4">{founderNote.role}</p>
              <blockquote className="text-gray-700 text-base leading-relaxed border-l-4 border-brand-200 pl-4 mb-4 italic">
                "{founderNote.message}"
              </blockquote>
              <p className="text-sm text-gray-500 leading-relaxed">
                Horizon Search is free to use, requires no account, and never tracks your searches.
                It is built on top of the public SAM.gov API and reflects live data directly from the
                federal government's contract database.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* ── Testimonials ────────────────────────────────────────────────── */}
      <div className="bg-gradient-to-b from-brand-900 to-brand-800 py-16">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-10">
            <p className="text-xs font-semibold uppercase tracking-widest text-brand-300 mb-2">
              From the community
            </p>
            <h2 className="text-2xl font-bold text-white mb-2">Veterans on federal contracting</h2>
            <p className="text-brand-300 text-sm max-w-xl mx-auto">
              Firsthand accounts from veteran business owners who have navigated the federal contracting process.
            </p>
          </div>
          <div className="grid sm:grid-cols-3 gap-5">
            {testimonials.map((t, i) => <TestimonialCard key={i} t={t} />)}
          </div>
          <p className="text-center text-brand-400 text-xs mt-6">
            Have a story to share? Reach out — we'd love to feature more veteran voices here.
          </p>
        </div>
      </div>

      {/* ── Bottom CTA ──────────────────────────────────────────────────── */}
      <div className="bg-white py-14">
        <div className="max-w-2xl mx-auto px-4 text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-3">
            Ready to find your next contract?
          </h2>
          <p className="text-gray-500 text-sm mb-6 leading-relaxed">
            Active opportunities, filtered for veteran set-asides, with plain-English explanations
            on every listing. No account needed.
          </p>
          <div className="flex flex-wrap gap-3 justify-center">
            <Link to="/" className="bg-brand-600 hover:bg-brand-700 text-white font-bold px-6 py-3 rounded-xl transition text-sm">
              Search contracts →
            </Link>
            <Link to="/start" className="border border-gray-200 text-gray-700 hover:bg-gray-50 font-semibold px-6 py-3 rounded-xl transition text-sm">
              Start Here guide →
            </Link>
          </div>
        </div>
      </div>

    </div>
  );
}
