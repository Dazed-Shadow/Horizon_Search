import React, { useState } from "react";
import { Link } from "react-router-dom";

/* ─── Data ─────────────────────────────────────────────────────────────── */

const SECTIONS = [
  {
    id: "advantage",
    step: "01",
    color: "brand",
    title: "The Veteran Advantage",
    icon: "M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16H9m3 0h3",
    summary: "The federal government is legally required to direct a share of contract dollars to veteran-owned businesses. Here's why that matters for you.",
    content: [
      {
        heading: "Set-Asides: The Law Is on Your Side",
        body: "Under the National Defense Authorization Act and the Veterans Benefits, Health Care, and Information Technology Act, federal agencies must meet annual goals for contracting with veteran-owned small businesses. The VA alone is required to award at least 20% of its prime contract dollars to SDVOSBs. When an agency sets aside a contract for veteran businesses, only certified veteran-owned companies can compete — that means fewer competitors and a level playing field built specifically for you.",
      },
      {
        heading: "Set-Aside Types",
        body: null,
        table: [
          { code: "SDVOSBC", label: "Service-Disabled Veteran-Owned Small Business", note: "Requires VA disability rating. Highest-priority set-aside. Most VA contracts reserved for SDVOSB." },
          { code: "VOSBC",   label: "Veteran-Owned Small Business", note: "Any honorably discharged veteran with 51%+ ownership. Broader eligibility than SDVOSB." },
          { code: "8(a)",    label: "SBA 8(a) Business Development", note: "9-year program for economically disadvantaged businesses. Sole-source awards up to $4.5M (services)." },
          { code: "HUBZone", label: "Historically Underutilized Business Zone", note: "Location-based preference. 10% price evaluation advantage over non-HUBZone competitors." },
          { code: "WOSB",   label: "Women-Owned Small Business", note: "Applies if your business is 51%+ women-owned. Can stack with veteran status." },
          { code: "SB",     label: "Small Business Set-Aside", note: "Broadest set-aside. Any small business under the NAICS size standard can compete." },
        ],
      },
      {
        heading: "The Numbers",
        body: "The federal government spent over $750 billion on contracts in FY2023. SDVOSB-designated contracts alone totaled over $30 billion. You do not need to be the biggest company in the room — you need the right certifications and a credible proposal.",
      },
    ],
  },
  {
    id: "eligibility",
    step: "02",
    color: "indigo",
    title: "Are You Eligible?",
    icon: "M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z",
    summary: "A quick eligibility check before you invest time in certification. The full certification roadmap is in the Licensing & Certs guide.",
    content: [
      {
        heading: "SDVOSB — Service-Disabled Veteran-Owned Small Business",
        body: null,
        checklist: [
          "You have a VA service-connected disability rating (any percentage, including 0%)",
          "You own at least 51% of the business, unconditionally",
          "You hold the highest officer title (President/CEO/Managing Member)",
          "You control day-to-day operations and long-term decision-making",
          "The business qualifies as 'small' under the NAICS code for the contract",
          "Your business is a for-profit entity organized in the U.S.",
        ],
      },
      {
        heading: "VOSB — Veteran-Owned Small Business",
        body: "Same ownership and control requirements as SDVOSB, but no disability rating is required. Honorable or general discharge qualifies. VOSB set-asides are used when there aren't enough SDVOSB competitors to ensure fair competition.",
      },
      {
        heading: "Common Disqualifiers",
        body: null,
        checklist: [
          "Non-veteran owns more than 49% — fails the 51% rule",
          "Veteran is a silent partner or investor without operational control",
          "Operating agreement or articles of incorporation give veto power to a non-veteran investor",
          "Business exceeds the small business size standard for the target NAICS code (check SBA's size standards tool)",
          "SAM.gov registration is expired or missing required NAICS codes",
        ],
        negative: true,
      },
      {
        heading: "Where to Certify",
        body: "SDVOSB and VOSB: apply through the SBA Veterans Advantage portal at veterans.certify.sba.gov. VA CVE verification is separate and required specifically for VA contracts. See the Licensing & Certs guide for the full step-by-step process.",
      },
    ],
  },
  {
    id: "lifecycle",
    step: "03",
    color: "green",
    title: "The Contracting Lifecycle",
    icon: "M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15",
    summary: "A federal contract follows a predictable sequence. Understanding where you are in that sequence tells you exactly what to do next.",
    content: [
      {
        heading: null,
        body: null,
        phases: [
          {
            num: "1",
            name: "Requirement & Planning",
            color: "bg-gray-100 text-gray-700",
            detail: "The agency identifies a need, assigns it a NAICS code, estimates the contract value, and decides whether to compete it as a set-aside. You can't see most of this — but watching agency forecast portals (USASpending.gov, agency procurement forecasts) lets you anticipate what's coming 6–12 months out.",
          },
          {
            num: "2",
            name: "Pre-Solicitation / Sources Sought",
            color: "bg-blue-100 text-blue-700",
            detail: "Before releasing a formal solicitation, contracting officers often post a Sources Sought Notice on SAM.gov to gauge market interest. Responding to Sources Sought costs nothing and puts your name in front of the contracting officer before the competition opens. Include your capability statement and relevant past performance.",
          },
          {
            num: "3",
            name: "Solicitation Released",
            color: "bg-indigo-100 text-indigo-700",
            detail: "The formal solicitation appears on SAM.gov as an RFP (Request for Proposals), RFQ (Request for Quotes), or IFB (Invitation for Bids). Read Section L (Instructions) and Section M (Evaluation Criteria) first — these tell you exactly how to structure your response and how it will be scored. Missing a required section is an automatic disqualification in many cases.",
          },
          {
            num: "4",
            name: "Q&A Period",
            color: "bg-purple-100 text-purple-700",
            detail: "After the solicitation drops, there's typically a 7–30 day window to submit questions. Submit every question you have — the government posts all questions and answers publicly, so competitors see the same information. But your question may reveal a weakness in the solicitation that forces a clarifying amendment, which helps everyone.",
          },
          {
            num: "5",
            name: "Proposal Submission",
            color: "bg-orange-100 text-orange-700",
            detail: "You submit your proposal by the deadline. Most proposals have three volumes: Technical Approach (how you'll do the work), Management Approach (who will do it), and Price/Cost. Some also require a Past Performance volume. Late proposals are rejected without exception — build in 48 hours of buffer before the real deadline.",
          },
          {
            num: "6",
            name: "Evaluation & Award",
            color: "bg-yellow-100 text-yellow-700",
            detail: "The agency evaluates proposals against the published criteria. Common evaluation methods: Lowest Price Technically Acceptable (LPTA) — cheapest technically compliant wins; Best Value Tradeoff — evaluators balance technical quality against price. After award, unsuccessful bidders can request a debriefing — always request one. It's free intel for your next proposal.",
          },
          {
            num: "7",
            name: "Contract Performance",
            color: "bg-green-100 text-green-700",
            detail: "You won. Now you deliver. Federal contracts include a Contracting Officer's Representative (COR) who monitors your performance and submits performance ratings to CPARS (Contractor Performance Assessment Reporting System). These ratings follow you — good CPARS ratings are past performance gold for future bids. Treat every contract as an audition for the next.",
          },
        ],
      },
    ],
  },
  {
    id: "opportunities",
    step: "04",
    color: "teal",
    title: "Finding the Right Opportunities",
    icon: "M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z",
    summary: "Not every contract is worth chasing. Here's how to filter for opportunities you can actually win.",
    content: [
      {
        heading: "Using SAM.gov Effectively",
        body: "SAM.gov is the single required posting location for federal contracts over $25,000. Use the Opportunities search and filter by: Set-Aside Type (SDVOSBC, VOSBC, etc.), NAICS Code (your service area), Place of Performance (where the work happens), and Posted Date (recent postings). Horizon Search is a faster interface on top of SAM.gov — use it for daily monitoring, then go to SAM.gov for the full solicitation documents.",
      },
      {
        heading: "Reading a Contract Listing",
        body: null,
        checklist: [
          "Notice Type — 'Solicitation' or 'Combined Synopsis' means you can bid. 'Sources Sought' means respond with a capability statement. 'Award Notice' means it already went to someone.",
          "NAICS Code — must match one of your registered NAICS codes in SAM.gov for your bid to be considered.",
          "Set-Aside — if it says SDVOSBC, only SDVOSB-certified businesses can bid. If it says 'Total Small Business,' any small business can compete.",
          "Response Deadline — this is hard. There are no extensions unless the agency issues an amendment.",
          "Place of Performance — where you'll actually do the work. Remote work has become more common post-2020, but many contracts still require on-site presence.",
          "Period of Performance — the base contract length plus option years. A '1+4' means 1 base year with 4 one-year options = 5 years max. Longer periods of performance = more revenue stability.",
        ],
      },
      {
        heading: "The 'Bid / No-Bid' Decision",
        body: "Not every solicitation is worth a proposal. Proposals take 20–200+ hours to write well. Before committing, ask: Do I have directly relevant past performance? Can I realistically staff this contract at the required security clearance level? Is the contract value worth the investment? Do I know the incumbent? (Incumbents win re-competes roughly 70% of the time — factor that into your odds.) A disciplined no-bid decision preserves resources for winnable opportunities.",
      },
      {
        heading: "Forecasting Future Work",
        body: "USASpending.gov shows every federal award — search by NAICS, agency, or contractor to see what's been awarded and when contracts expire. Expiring contracts are re-competed. Finding a $5M contract that expires in 8 months gives you time to get introduced to the agency, understand the requirement, and build a responsive proposal before the solicitation drops.",
      },
    ],
  },
  {
    id: "proposal",
    step: "05",
    color: "orange",
    title: "Writing a Proposal That Wins",
    icon: "M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z",
    summary: "The proposal is where contracts are won and lost. Most companies lose not because of price, but because of a weak technical approach or missed compliance requirements.",
    content: [
      {
        heading: "The Capability Statement",
        body: "Before you write a full proposal, you need a one-page capability statement. This is your company's resume — handed out at networking events, attached to Sources Sought responses, and sent to contracting officers as an introduction. Required elements: Core Competencies (what you do and how), Differentiators (why you, not a competitor), Past Performance (2–5 examples with agency name, contract number, dollar value, and your role), Company Data (CAGE code, UEI, NAICS codes, SAM.gov status, certifications). Keep it to one page. Update it quarterly.",
      },
      {
        heading: "Technical Volume",
        body: "The technical volume answers: how will you deliver the required services? Address the Statement of Work (SOW) or Performance Work Statement (PWS) section by section. Show your methodology, tools, and quality control process. Evaluators can't assume you understand something — if your proposal doesn't say it explicitly, it doesn't exist. Ghost the competition: if the solicitation hints at agency pain points (past performance failures, security weaknesses, schedule slippages), describe how your approach specifically prevents those problems.",
      },
      {
        heading: "Past Performance",
        body: "Past performance is typically evaluated as 'Exceptional / Very Good / Satisfactory / Marginal / Unsatisfactory' based on CPARS records and references you provide. As a new company, you have two options: (1) use the personal past performance of your key personnel from their prior employers or military service — many solicitations allow this explicitly; (2) team with a company that has relevant past performance (see Teaming section). Never fabricate or inflate past performance — federal misrepresentation carries criminal penalties.",
      },
      {
        heading: "Pricing",
        body: "For LPTA contracts, price is everything above the technical minimum. Know your labor rates, burden rates (benefits, overhead, G&A), and profit margin before you start. For best-value contracts, don't race to the bottom — underpriced contracts lead to cost overruns, poor performance ratings, and potential termination for default. Use historical contract data from USASpending.gov to understand what the government has paid for similar work.",
      },
      {
        heading: "Compliance Review",
        body: "The day before submission, run a compliance matrix: list every requirement from Section L (instructions) and check them against your proposal. Common disqualifiers: exceeding the page limit, missing required forms (SF-1449, representations and certifications), wrong font size, missing subcontracting plan (required over $750K on non-set-aside contracts). Compliance is table stakes — you can't win if you're thrown out for non-compliance.",
      },
    ],
  },
  {
    id: "teaming",
    step: "06",
    color: "red",
    title: "Teaming & Subcontracting",
    icon: "M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z",
    summary: "You don't have to go it alone. Strategic teaming is how small businesses punch above their weight class in federal contracting.",
    content: [
      {
        heading: "Prime vs. Subcontractor",
        body: "As the prime contractor, you sign the contract with the government, own the relationship, and are responsible for performance. As a subcontractor, you work under another prime — less risk, faster path to revenue and past performance, but lower margins and no direct agency relationship. Early in your contracting career, subcontracting under an experienced prime is often the fastest path to building past performance and learning the flow of a federal contract.",
      },
      {
        heading: "Teaming Agreements",
        body: "A teaming agreement is a contract between two companies to jointly pursue a specific opportunity, defining who will be the prime, what work each party performs, and what happens if you win. Key terms to nail down: each party's workshare percentage (the government scrutinizes this — SDVOSB primes must self-perform a minimum percentage), exclusivity (can your teammate also team with your competitor on the same bid?), and what happens if one party withdraws. Get a federal contracting attorney to review any teaming agreement before signing.",
      },
      {
        heading: "SBA Mentor-Protégé Program",
        body: "The SBA Mentor-Protégé Program pairs small businesses (protégés) with experienced federal contractors (mentors). Benefits: the mentor can own up to 40% of a joint venture with the protégé without affecting the protégé's small business status, the JV can compete for set-aside contracts reserved for the protégé's socioeconomic category, and the mentor provides technical/management assistance. This is one of the most powerful growth mechanisms available to veteran small businesses.",
      },
      {
        heading: "Finding Teaming Partners",
        body: "Search SAM.gov's Dynamic Small Business Search (DSBS) by NAICS code and certifications to find potential partners. GovWin IQ and similar platforms track who is pursuing which opportunities. Industry events — SAME (Society of American Military Engineers) small business expos, agency-specific small business outreach events — are where teaming relationships actually form. Show up, exchange capability statements, and follow up with specific opportunities in mind.",
      },
      {
        heading: "Large Business Subcontracting Plans",
        body: "Federal contracts over $750,000 awarded to large businesses require subcontracting plans with specific goals for awarding subcontracts to small businesses, SDVOSBs, VOSBs, and other categories. This is your opening. Large prime contractors actively seek qualified veteran-owned subs to meet these requirements. Target large primes working in your NAICS codes and offer your capabilities — you're solving their compliance problem.",
      },
    ],
  },
];

const COLOR_MAP = {
  brand:  { step: "bg-brand-600",  border: "border-brand-200",  bg: "bg-brand-50",  text: "text-brand-700" },
  indigo: { step: "bg-indigo-600", border: "border-indigo-200", bg: "bg-indigo-50", text: "text-indigo-700" },
  green:  { step: "bg-green-600",  border: "border-green-200",  bg: "bg-green-50",  text: "text-green-700" },
  teal:   { step: "bg-teal-600",   border: "border-teal-200",   bg: "bg-teal-50",   text: "text-teal-700" },
  orange: { step: "bg-orange-500", border: "border-orange-200", bg: "bg-orange-50", text: "text-orange-700" },
  red:    { step: "bg-red-600",    border: "border-red-200",    bg: "bg-red-50",    text: "text-red-700" },
};

/* ─── Sub-components ───────────────────────────────────────────────────── */

function SetAsideTable({ rows }) {
  return (
    <div className="overflow-x-auto mt-2">
      <table className="w-full text-sm border-collapse">
        <thead>
          <tr className="bg-gray-50 text-left">
            <th className="px-3 py-2 font-semibold text-gray-600 text-xs uppercase tracking-wide border-b border-gray-200 w-28">Code</th>
            <th className="px-3 py-2 font-semibold text-gray-600 text-xs uppercase tracking-wide border-b border-gray-200">Name</th>
            <th className="px-3 py-2 font-semibold text-gray-600 text-xs uppercase tracking-wide border-b border-gray-200">Notes</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(r => (
            <tr key={r.code} className="border-b border-gray-100 last:border-0 hover:bg-gray-50">
              <td className="px-3 py-2.5">
                <span className="font-mono text-xs bg-brand-50 text-brand-700 px-2 py-0.5 rounded font-bold">{r.code}</span>
              </td>
              <td className="px-3 py-2.5 font-medium text-gray-800">{r.label}</td>
              <td className="px-3 py-2.5 text-gray-500 text-xs leading-relaxed">{r.note}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Checklist({ items, negative }) {
  return (
    <ul className="mt-2 space-y-2">
      {items.map((item, i) => (
        <li key={i} className="flex gap-2.5 text-sm text-gray-700">
          <span className={`mt-0.5 shrink-0 w-4 h-4 rounded-full flex items-center justify-center text-white text-[10px] font-bold ${negative ? "bg-red-400" : "bg-green-500"}`}>
            {negative ? "✕" : "✓"}
          </span>
          <span className="leading-relaxed">{item}</span>
        </li>
      ))}
    </ul>
  );
}

function PhaseTimeline({ phases }) {
  return (
    <div className="relative mt-2">
      <div className="absolute left-5 top-6 bottom-6 w-0.5 bg-gray-200" />
      <div className="space-y-4">
        {phases.map(phase => (
          <div key={phase.num} className="flex gap-4 relative">
            <div className={`shrink-0 w-10 h-10 rounded-full flex items-center justify-center text-xs font-bold z-10 ${phase.color}`}>
              {phase.num}
            </div>
            <div className="flex-1 pb-2">
              <p className="font-semibold text-gray-800 text-sm mt-2">{phase.name}</p>
              <p className="text-xs text-gray-500 mt-1 leading-relaxed">{phase.detail}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function ContentBlock({ block }) {
  return (
    <div className="py-3 border-b border-gray-100 last:border-0">
      {block.heading && (
        <p className="text-sm font-semibold text-gray-800 mb-1">{block.heading}</p>
      )}
      {block.body && (
        <p className="text-sm text-gray-600 leading-relaxed">{block.body}</p>
      )}
      {block.table && <SetAsideTable rows={block.table} />}
      {block.checklist && <Checklist items={block.checklist} negative={block.negative} />}
      {block.phases && <PhaseTimeline phases={block.phases} />}
    </div>
  );
}

function SectionCard({ section }) {
  const [open, setOpen] = useState(false);
  const c = COLOR_MAP[section.color];

  return (
    <div className={`rounded-xl border ${c.border} overflow-hidden`}>
      <button
        className={`w-full flex items-start gap-4 px-5 py-4 ${c.bg} text-left`}
        onClick={() => setOpen(o => !o)}
      >
        <span className={`${c.step} text-white text-xs font-bold px-2.5 py-1 rounded-full shrink-0 mt-0.5`}>
          {section.step}
        </span>
        <div className="flex-1 min-w-0">
          <p className={`font-bold text-base ${c.text}`}>{section.title}</p>
          <p className="text-xs text-gray-500 mt-0.5 leading-relaxed">{section.summary}</p>
        </div>
        <svg className={`w-5 h-5 ${c.text} transition-transform shrink-0 mt-1 ${open ? "rotate-180" : ""}`}
          fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {open && (
        <div className="px-5 bg-white">
          {section.content.map((block, i) => (
            <ContentBlock key={i} block={block} />
          ))}
        </div>
      )}
    </div>
  );
}

/* ─── Page ──────────────────────────────────────────────────────────────── */

export default function ContractPrimerPage() {
  return (
    <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10 flex-1">

      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-2 text-sm text-brand-600 font-medium mb-3">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16H9m3 0h3" />
          </svg>
          Veteran Contracting Primer
        </div>
        <h1 className="text-2xl font-bold text-gray-900">How to Win a Government Contract</h1>
        <p className="text-gray-500 mt-2 text-sm leading-relaxed">
          A field guide for service members and veterans entering the federal marketplace. This is the
          "how does it actually work" that nobody hands you at ETS — covering set-asides, the bid
          lifecycle, proposal writing, and teaming strategy.
        </p>
        <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-xl text-sm text-blue-800">
          <strong>Quick orientation:</strong> The{" "}
          <Link to="/licensing" className="underline font-semibold">Licensing & Certs guide</Link>{" "}
          covers registrations and certifications (SAM.gov, SDVOSB, 8(a), etc.). This page covers
          what happens after you're registered — finding, bidding, and winning contracts.
        </div>
      </div>

      {/* Key terms strip */}
      <div className="mb-6 p-4 bg-white border border-gray-200 rounded-xl shadow-sm">
        <p className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-3">Key Terms at a Glance</p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-2">
          {[
            ["NAICS Code", "6-digit code identifying your industry. Determines which contracts you're eligible to bid."],
            ["UEI", "Unique Entity Identifier — your SAM.gov registration number. Required on all bids."],
            ["RFP / RFQ / IFB", "Request for Proposals / Quotes / Bids — the solicitation document you respond to."],
            ["SOW / PWS", "Statement of Work / Performance Work Statement — defines what the contract requires."],
            ["CPARS", "Contractor Performance Assessment Reporting System — your federal performance record."],
            ["LPTA", "Lowest Price Technically Acceptable — cheapest compliant bid wins."],
            ["Best Value", "Agency weighs technical quality against price — not purely lowest cost."],
            ["Incumbent", "The company currently holding the contract you're competing for."],
            ["CO / COR", "Contracting Officer / Contracting Officer's Representative — your government contacts."],
            ["Option Year", "A contract extension the government can exercise at its discretion."],
          ].map(([term, def]) => (
            <div key={term} className="flex gap-2 text-sm">
              <span className="font-semibold text-gray-800 shrink-0 w-28 text-xs mt-0.5">{term}</span>
              <span className="text-gray-500 text-xs leading-relaxed">{def}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Section cards */}
      <div className="space-y-4">
        {SECTIONS.map(s => <SectionCard key={s.id} section={s} />)}
      </div>

      {/* Action cards */}
      <div className="mt-10">
        <p className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-4">Next Steps</p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Link to="/"
            className="flex items-start gap-3 bg-brand-50 rounded-xl border border-brand-200 p-4 shadow-sm hover:shadow-md hover:border-brand-400 transition group">
            <div className="mt-0.5 w-8 h-8 bg-brand-100 rounded-lg flex items-center justify-center shrink-0 group-hover:bg-brand-200 transition">
              <svg className="w-4 h-4 text-brand-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <div>
              <p className="font-semibold text-brand-800 text-sm">Search Active Contracts</p>
              <p className="text-xs text-brand-600 mt-0.5">Find SDVOSB and veteran set-aside opportunities on SAM.gov right now.</p>
            </div>
          </Link>

          <Link to="/licensing"
            className="flex items-start gap-3 bg-white rounded-xl border border-gray-200 p-4 shadow-sm hover:shadow-md hover:border-brand-200 transition group">
            <div className="mt-0.5 w-8 h-8 bg-brand-50 rounded-lg flex items-center justify-center shrink-0 group-hover:bg-brand-100 transition">
              <svg className="w-4 h-4 text-brand-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
            </div>
            <div>
              <p className="font-semibold text-gray-800 text-sm group-hover:text-brand-700 transition">Licensing & Certification Guide</p>
              <p className="text-xs text-gray-500 mt-0.5">LLC formation, SAM.gov registration, SDVOSB certification, industry licenses.</p>
            </div>
          </Link>

          {[
            { title: "Dynamic Small Business Search", sub: "Search for teaming partners by NAICS code and certifications", href: "https://dsbs.sba.gov" },
            { title: "USASpending.gov", sub: "Research past awards, expiring contracts, and agency spending", href: "https://www.usaspending.gov" },
            { title: "SBA Learning Center", sub: "Free courses on government contracting basics", href: "https://www.sba.gov/learning-center" },
            { title: "Procurement Technical Assistance Centers", sub: "Free local counseling — they'll review your proposals", href: "https://www.aptac-us.org/find-a-ptac/" },
          ].map(r => (
            <a key={r.href} href={r.href} target="_blank" rel="noopener noreferrer"
              className="flex items-start gap-3 bg-white rounded-xl border border-gray-200 p-4 shadow-sm hover:shadow-md hover:border-brand-200 transition group">
              <div className="mt-0.5 w-8 h-8 bg-brand-50 rounded-lg flex items-center justify-center shrink-0 group-hover:bg-brand-100 transition">
                <svg className="w-4 h-4 text-brand-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                </svg>
              </div>
              <div>
                <p className="font-semibold text-gray-800 text-sm group-hover:text-brand-700 transition">{r.title} ↗</p>
                <p className="text-xs text-gray-500 mt-0.5">{r.sub}</p>
              </div>
            </a>
          ))}
        </div>
      </div>

      <p className="mt-8 text-xs text-gray-400 text-center">
        This guide reflects general federal acquisition practice under the FAR. Requirements vary by agency and contract type.
        For contract-specific legal advice, consult a federal procurement attorney.
      </p>
    </main>
  );
}
