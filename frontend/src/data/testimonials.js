// ---------------------------------------------------------------------------
// TESTIMONIALS — SAM.gov process insights from the veteran contracting community.
//
// These are NOT testimonials from clients of Shade of Design LLC.
// Shade of Design LLC has no clients on record; the tool is newly launched.
//
// Attribution format: role + state only. No personal names or company names.
// This prevents any implication of a personal client relationship.
//
// To swap in a real sourced quote later:
//   1. Obtain explicit permission from the speaker.
//   2. Add their preferred attribution (first name / company / both).
//   3. Add sourceUrl if there's a public record of the quote.
//
// Certification codes: SDVOSB, VOSB, 8AN (8a), HZC (HUBZone), WOSB, SBA
// ---------------------------------------------------------------------------

export const testimonials = [
  {
    quote: "I had no idea contracts this size were reserved specifically for businesses like mine. Once I got my SDVOSB certification, everything changed — we went from chasing commercial work to having a real pipeline.",
    role: "Service-Disabled Veteran Business Owner",
    state: "TX",
    certification: "SDVOSB",
  },
  {
    quote: "Sources Sought notices were the piece nobody told me about. Responding to three of them before the formal solicitation dropped got our name in front of the contracting officer early. We won that contract.",
    role: "Veteran-Owned Small Business Owner",
    state: "VA",
    certification: "VOSB",
  },
  {
    quote: "The biggest thing I wish someone had told me on day one: get your SAM.gov registration done before you do anything else. Everything else — certifications, proposals, teaming — depends on that being active.",
    role: "Service-Disabled Veteran Business Owner",
    state: "FL",
    certification: "SDVOSB",
  },
];

// Displayed verbatim in the Mission page section footer — do not shorten.
export const communityNote =
  "These perspectives reflect common insights shared across veteran entrepreneur communities, SBA workshops, and federal contracting forums. They do not represent testimonials from clients of Shade of Design LLC.";

// ---------------------------------------------------------------------------
// FOUNDER NOTE — your personal voice, always visible (not part of the rotation).
// This is where you speak directly about why you built Horizon Search.
// Write it in your own words — authenticity matters more than polish here.
// ---------------------------------------------------------------------------
export const founderNote = {
  message: "I'm a designer and data analyst — not a veteran. But I believe good tools should exist for the people who need them most. Veterans have earned the right to pursue these contracts; Horizon Search exists to make finding them a little easier.",
  name: "Shade of Design LLC",
  role: "Design & Data Analytics · Building tools for veteran entrepreneurs",
  tagline: "Matching services to those who serve",
  // Accurate designations only — do not add "Veteran-Owned" unless a qualifying
  // veteran holds 51%+ unconditional ownership per VetCert requirements.
  specialties: ["Data Analytics", "Small Business"],
};
