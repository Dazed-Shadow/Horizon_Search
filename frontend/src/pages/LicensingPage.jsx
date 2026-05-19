import React, { useState } from "react";

const STEPS = [
  {
    step: "01",
    title: "Form Your LLC",
    color: "brand",
    items: [
      { label: "Choose a state to register in", note: "Most veteran contractors register in their home state. Delaware and Wyoming offer favorable LLC laws.", link: null },
      { label: "File Articles of Organization", note: "File with your state's Secretary of State office. Typical cost: $50–$500.", link: "https://www.sba.gov/business-guide/launch-your-business/register-your-business" },
      { label: "Get an EIN (Employer Identification Number)", note: "Free from the IRS — apply online in minutes. Required to open a business bank account.", link: "https://www.irs.gov/businesses/small-businesses-self-employed/apply-for-an-employer-identification-number-ein-online" },
      { label: "Open a dedicated business bank account", note: "Keeps personal and business finances separate — required for DCAA-compliant accounting.", link: null },
      { label: "Draft your LLC Operating Agreement", note: "Critical for veteran certifications — must show veteran owns 51%+ and holds the highest officer role.", link: null },
    ],
  },
  {
    step: "02",
    title: "Federal Registration (Required for All Contracts)",
    color: "indigo",
    items: [
      { label: "Register on SAM.gov (System for Award Management)", note: "Free. Mandatory for any federal contract or grant. Assigns your UEI and CAGE code automatically. Renew annually.", link: "https://sam.gov/content/home" },
      { label: "Unique Entity Identifier (UEI)", note: "Assigned during SAM.gov registration. Replaced the old DUNS number in 2022. Required on all bids.", link: "https://sam.gov" },
      { label: "CAGE Code", note: "Commercial and Government Entity code — automatically assigned with SAM.gov registration. Used by DoD agencies.", link: null },
      { label: "Set up NAICS codes in SAM.gov", note: "Register all NAICS codes that match your business activities. These determine which contracts you appear eligible for.", link: "https://www.census.gov/naics/" },
    ],
  },
  {
    step: "03",
    title: "Veteran Business Certifications",
    color: "green",
    items: [
      { label: "VOSB Self-Certification (SBA)", note: "Veteran-Owned Small Business. Self-certify via SBA's MySBA portal. Grants access to VOSB set-aside contracts across all agencies.", link: "https://certify.sba.gov" },
      { label: "SDVOSB Certification (SBA)", note: "Service-Disabled Veteran-Owned Small Business. Requires VA disability rating. Highest-priority federal set-aside. Apply through SBA CVE.", link: "https://veterans.certify.sba.gov" },
      { label: "VA CVE Verification", note: "Required specifically for VA contracts (VAAR 819.70). Separate from SBA certification. Expect a thorough document review.", link: "https://veteransmallbiz.va.gov" },
      { label: "SBA 8(a) Business Development Program", note: "9-year program for socially/economically disadvantaged businesses. Includes veteran pathways. Provides mentorship and sole-source contract access.", link: "https://certify.sba.gov/apply/8a" },
      { label: "HUBZone Certification", note: "Historically Underutilized Business Zone. Based on business location + employee residency in qualifying areas. Check eligibility map first.", link: "https://www.sba.gov/federal-contracting/contracting-assistance-programs/hubzone-program" },
    ],
  },
  {
    step: "04",
    title: "Industry-Specific Licenses",
    color: "orange",
    subsections: [
      {
        title: "IT & Cybersecurity",
        items: [
          { label: "CMMC (Cybersecurity Maturity Model Certification)", note: "Required for DoD contracts handling Controlled Unclassified Information (CUI). Level 1 (self-assess) to Level 3 (third-party audit).", link: "https://www.acq.osd.mil/cmmc/" },
          { label: "CompTIA Security+", note: "DoD 8570 baseline certification for IT security roles. Widely required on federal IT contracts.", link: "https://www.comptia.org/certifications/security" },
          { label: "FedRAMP Authorization", note: "Required for cloud service providers selling to federal agencies. Costly but opens significant revenue.", link: "https://www.fedramp.gov" },
        ],
      },
      {
        title: "Construction & Engineering",
        items: [
          { label: "State Contractor's License", note: "Required in most states for construction work. Each state has its own board and exam. Check your state's contractor licensing board.", link: "https://www.contractors-license.org" },
          { label: "SBA Bonding Assistance Program", note: "Surety bonding is required for most federal construction contracts. SBA's program helps veteran small businesses get bonded.", link: "https://www.sba.gov/federal-contracting/contracting-assistance-programs/surety-bond-guarantee-program" },
          { label: "Professional Engineer (PE) License", note: "Required for engineering firms signing off on designs. State-specific; requires passing the PE exam.", link: "https://ncees.org/engineering/pe/" },
        ],
      },
      {
        title: "Security Services",
        items: [
          { label: "State Security Guard License", note: "Required for private security services. Each state has its own requirements — many veterans qualify via military experience.", link: null },
          { label: "Armed Contractor Overseas (ACO)", note: "Required for armed security on overseas DoD contracts (e.g., LOGCAP). State firearm permits + DoD vetting.", link: null },
          { label: "Facility Security Clearance (FCL)", note: "Required to perform classified work. Sponsor is the contracting agency — you can't apply alone. Starts with a contract award.", link: "https://www.dcsa.mil/mc/pv/mbi/fac/" },
        ],
      },
      {
        title: "Healthcare & Medical",
        items: [
          { label: "State Medical / Clinical Licenses", note: "Required for healthcare staffing contracts (VA, DoD medical facilities). Must be current in the state of performance.", link: null },
          { label: "HIPAA Compliance Program", note: "Required for any contract handling protected health information. Document your policies and procedures.", link: "https://www.hhs.gov/hipaa/for-professionals/index.html" },
          { label: "Joint Commission Accreditation", note: "Often required for VA healthcare facility contracts. Demonstrates quality standards.", link: "https://www.jointcommission.org" },
        ],
      },
      {
        title: "Professional Services & Consulting",
        items: [
          { label: "GSA Schedule (Federal Supply Schedule)", note: "Pre-negotiated contract vehicle — agencies can buy from you without a full competition. Significant effort to obtain but opens ongoing revenue.", link: "https://www.gsa.gov/buying-selling/purchasing-programs/gsa-schedules/selling-through-gsa-schedules" },
          { label: "ISO 9001 Certification", note: "Quality management standard often required on larger federal contracts, especially for manufacturing and technical services.", link: "https://www.iso.org/iso-9001-quality-management.html" },
          { label: "DCAA-Compliant Accounting System", note: "Required for cost-reimbursable contracts. Not a license — a financial systems audit. Use compliant software (QuickBooks with DCAA settings, Unanet, Deltek).", link: "https://www.dcaa.mil/guidance/accounting-and-finance-topics/" },
        ],
      },
    ],
  },
  {
    step: "05",
    title: "Security Clearances",
    color: "red",
    items: [
      { label: "Personnel Security Clearance (PCL) — Secret", note: "Most common DoD clearance. Initiated by the contracting agency after award. Background investigation typically takes 3–6 months.", link: "https://www.dcsa.mil/mc/pv/mbi/" },
      { label: "Personnel Security Clearance — Top Secret / SCI", note: "Required for sensitive intelligence and classified programs. More extensive investigation. Can take 6–18 months.", link: "https://www.dcsa.mil/mc/pv/mbi/" },
      { label: "Facility Security Clearance (FCL)", note: "Your company must have an FCL to hold classified contracts. Requires a cleared employee serving as Facility Security Officer (FSO).", link: "https://www.dcsa.mil/mc/pv/mbi/fac/" },
      { label: "Important: You cannot self-sponsor for clearance", note: "A government agency or cleared prime contractor must sponsor you. The path is: win a contract that requires cleared staff → the agency sponsors the clearance.", link: null },
    ],
  },
];

const COLOR_MAP = {
  brand:  { step: "bg-brand-600",  border: "border-brand-200",  bg: "bg-brand-50",  text: "text-brand-700",  dot: "bg-brand-500" },
  indigo: { step: "bg-indigo-600", border: "border-indigo-200", bg: "bg-indigo-50", text: "text-indigo-700", dot: "bg-indigo-500" },
  green:  { step: "bg-green-600",  border: "border-green-200",  bg: "bg-green-50",  text: "text-green-700",  dot: "bg-green-500" },
  orange: { step: "bg-orange-500", border: "border-orange-200", bg: "bg-orange-50", text: "text-orange-700", dot: "bg-orange-400" },
  red:    { step: "bg-red-600",    border: "border-red-200",    bg: "bg-red-50",    text: "text-red-700",    dot: "bg-red-500" },
};

function LicenseItem({ label, note, link }) {
  return (
    <div className="flex gap-3 py-3 border-b border-gray-100 last:border-0">
      <div className="mt-1 w-2 h-2 rounded-full bg-gray-300 shrink-0" />
      <div className="flex-1">
        <div className="flex items-start justify-between gap-2">
          <p className="text-sm font-semibold text-gray-800">{label}</p>
          {link && (
            <a href={link} target="_blank" rel="noopener noreferrer"
              className="shrink-0 text-xs text-brand-600 hover:underline font-medium">
              Apply / Learn ↗
            </a>
          )}
        </div>
        {note && <p className="text-xs text-gray-500 mt-0.5 leading-relaxed">{note}</p>}
      </div>
    </div>
  );
}

function StepCard({ step: s }) {
  const [open, setOpen] = useState(true);
  const c = COLOR_MAP[s.color];

  return (
    <div className={`rounded-xl border ${c.border} overflow-hidden`}>
      <button
        className={`w-full flex items-center gap-4 px-5 py-4 ${c.bg} text-left`}
        onClick={() => setOpen(o => !o)}
      >
        <span className={`${c.step} text-white text-xs font-bold px-2.5 py-1 rounded-full shrink-0`}>
          {s.step}
        </span>
        <span className={`font-bold text-base ${c.text} flex-1`}>{s.title}</span>
        <svg className={`w-5 h-5 ${c.text} transition-transform ${open ? "rotate-180" : ""}`}
          fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {open && (
        <div className="px-5 bg-white">
          {s.items && s.items.map(item => <LicenseItem key={item.label} {...item} />)}
          {s.subsections && s.subsections.map(sub => (
            <div key={sub.title} className="mb-4 last:mb-0">
              <p className="text-xs font-bold text-gray-500 uppercase tracking-widest mt-4 mb-1">{sub.title}</p>
              {sub.items.map(item => <LicenseItem key={item.label} {...item} />)}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function LicensingPage() {
  return (
    <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10 flex-1">
      {/* Page header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Licensing & Certification Guide</h1>
        <p className="text-gray-500 mt-1 text-sm">
          A step-by-step roadmap for veteran-owned businesses to qualify for and win government contracts.
          Each section is collapsible — expand what's relevant to your business type.
        </p>
        <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-xl text-sm text-yellow-800">
          <strong>Disclaimer:</strong> This guide is for informational purposes only and does not constitute legal advice.
          Requirements vary by agency, contract type, and state. Consult a federal contracting attorney for your specific situation.
        </div>
      </div>

      {/* Step cards */}
      <div className="space-y-4">
        {STEPS.map(s => <StepCard key={s.step} step={s} />)}
      </div>

      {/* Bottom resource links */}
      <div className="mt-10 grid grid-cols-1 sm:grid-cols-2 gap-4">
        {[
          { title: "SBA Veteran Programs", sub: "SDVOSB, VOSB, 8(a) certification portal", href: "https://veterans.certify.sba.gov" },
          { title: "SAM.gov Registration", sub: "Required first step — free, renew annually", href: "https://sam.gov" },
          { title: "CMMC Resource Center", sub: "DoD cybersecurity certification requirements", href: "https://www.acq.osd.mil/cmmc/" },
          { title: "Procurement Technical Assistance Centers (PTACs)", sub: "Free local counseling for government contracting", href: "https://www.aptac-us.org/find-a-ptac/" },
          { title: "VA Office of Small & Disadvantaged Business", sub: "VA-specific contracting programs and support", href: "https://www.va.gov/osdbu/" },
          { title: "SBA Mentor-Protégé Program", sub: "Partner with larger firms on set-aside contracts", href: "https://www.sba.gov/federal-contracting/contracting-assistance-programs/sba-mentor-protege-program" },
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
    </main>
  );
}
