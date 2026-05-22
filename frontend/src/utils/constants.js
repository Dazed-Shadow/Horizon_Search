export const SET_ASIDES = [
  // Veteran-specific — shown first
  { code: "SDVOSBC", label: "SDVOSB — Competitive", group: "Veteran" },
  { code: "SDVOSBS", label: "SDVOSB — Sole Source", group: "Veteran" },
  { code: "VSB",     label: "Veteran-Owned Small Business", group: "Veteran" },
  { code: "VOSB",   label: "VOSB", group: "Veteran" },
  // Small Business
  { code: "8AN",    label: "8(a) — Competitive", group: "Small Business" },
  { code: "8A",     label: "8(a) — Sole Source", group: "Small Business" },
  { code: "SBA",    label: "Small Business Set-Aside", group: "Small Business" },
  { code: "SBP",    label: "Small Business (Partial)", group: "Small Business" },
  { code: "HZC",    label: "HUBZone — Competitive", group: "Small Business" },
  { code: "HZS",    label: "HUBZone — Sole Source", group: "Small Business" },
  // Women-Owned
  { code: "WOSB",   label: "WOSB Set-Aside", group: "Women-Owned" },
  { code: "WOSBSS", label: "WOSB Sole Source", group: "Women-Owned" },
  { code: "EDWOSB", label: "EDWOSB Set-Aside", group: "Women-Owned" },
  { code: "EDWOSBSS", label: "EDWOSB Sole Source", group: "Women-Owned" },
  // Other
  { code: "IEE",    label: "Indian Economic Enterprise", group: "Other" },
  { code: "ISBEE",  label: "Indian Small Business EE", group: "Other" },
];

export const SOLICITATION_TYPES = [
  { code: "o", label: "Solicitation (RFP/RFQ/IFB)" },
  { code: "k", label: "Combined Synopsis/Solicitation" },
  { code: "p", label: "Pre-Solicitation" },
  { code: "r", label: "Sources Sought / RFI" },
  { code: "s", label: "Special Notice" },
  { code: "i", label: "Intent to Bundle (DoD)" },
  { code: "a", label: "Award Notice" },
  { code: "u", label: "Justification (J&A)" },
];

export const US_STATES = [
  ["AL","Alabama"],["AK","Alaska"],["AZ","Arizona"],["AR","Arkansas"],
  ["CA","California"],["CO","Colorado"],["CT","Connecticut"],["DE","Delaware"],
  ["FL","Florida"],["GA","Georgia"],["HI","Hawaii"],["ID","Idaho"],
  ["IL","Illinois"],["IN","Indiana"],["IA","Iowa"],["KS","Kansas"],
  ["KY","Kentucky"],["LA","Louisiana"],["ME","Maine"],["MD","Maryland"],
  ["MA","Massachusetts"],["MI","Michigan"],["MN","Minnesota"],["MS","Mississippi"],
  ["MO","Missouri"],["MT","Montana"],["NE","Nebraska"],["NV","Nevada"],
  ["NH","New Hampshire"],["NJ","New Jersey"],["NM","New Mexico"],["NY","New York"],
  ["NC","North Carolina"],["ND","North Dakota"],["OH","Ohio"],["OK","Oklahoma"],
  ["OR","Oregon"],["PA","Pennsylvania"],["RI","Rhode Island"],["SC","South Carolina"],
  ["SD","South Dakota"],["TN","Tennessee"],["TX","Texas"],["UT","Utah"],
  ["VT","Vermont"],["VA","Virginia"],["WA","Washington"],["WV","West Virginia"],
  ["WI","Wisconsin"],["WY","Wyoming"],["DC","District of Columbia"],
  ["PR","Puerto Rico"],["GU","Guam"],["VI","U.S. Virgin Islands"],
];

// Top NAICS codes relevant to veteran-owned businesses
export const COMMON_NAICS = [
  { code: "236220", label: "Commercial & Institutional Building Construction" },
  { code: "237310", label: "Highway, Street, and Bridge Construction" },
  { code: "238990", label: "All Other Specialty Trade Contractors" },
  { code: "336411", label: "Aircraft Manufacturing" },
  { code: "336992", label: "Military Armored Vehicle Manufacturing" },
  { code: "488190", label: "Other Support Activities for Air Transportation" },
  { code: "511210", label: "Software Publishers" },
  { code: "517110", label: "Wired Telecommunications Carriers" },
  { code: "518210", label: "Data Processing & Hosting" },
  { code: "519290", label: "Web Search Portals, All Other Info Services" },
  { code: "541211", label: "Offices of Certified Public Accountants" },
  { code: "541310", label: "Architectural Services" },
  { code: "541330", label: "Engineering Services" },
  { code: "541511", label: "Custom Computer Programming" },
  { code: "541512", label: "Computer Systems Design" },
  { code: "541513", label: "Computer Facilities Management" },
  { code: "541519", label: "Other Computer Related Services" },
  { code: "541611", label: "Administrative Management Consulting" },
  { code: "541612", label: "Human Resources Consulting" },
  { code: "541620", label: "Environmental Consulting" },
  { code: "541690", label: "Other Scientific & Technical Consulting" },
  { code: "541711", label: "R&D in Biotechnology" },
  { code: "541715", label: "R&D in Physical, Engineering Sciences" },
  { code: "541990", label: "All Other Professional, Scientific Services" },
  { code: "561110", label: "Office Administrative Services" },
  { code: "561210", label: "Facilities Support Services" },
  { code: "561320", label: "Temporary Staffing Agencies" },
  { code: "561612", label: "Security Guard & Patrol Services" },
  { code: "561621", label: "Security Systems Services" },
  { code: "561720", label: "Janitorial Services" },
  { code: "561730", label: "Landscaping Services" },
  { code: "561990", label: "All Other Support Services" },
  { code: "621111", label: "Offices of Physicians" },
  { code: "621399", label: "Offices of Other Health Practitioners" },
  { code: "621910", label: "Ambulance Services" },
  { code: "622110", label: "General Medical & Surgical Hospitals" },
  { code: "811212", label: "Computer & Office Machine Repair" },
  { code: "811310", label: "Commercial Equipment Repair & Maintenance" },
];

export const SET_ASIDE_COLORS = {
  Veteran:       "bg-green-100 text-green-800",
  "Small Business": "bg-blue-100 text-blue-800",
  "Women-Owned": "bg-purple-100 text-purple-800",
  Other:         "bg-gray-100 text-gray-700",
};

export const VETERAN_CODES = new Set(["SDVOSBC", "SDVOSBS", "VSB", "VOSB"]);

// Plain-language explanations for newcomers — shown via the "What does this mean?" toggle on each card.
export const SET_ASIDE_PLAIN = {
  SDVOSBC:  { who: "Service-Disabled Veteran-Owned Small Business (SDVOSB)", plain: "Only SDVOSBs compete for this contract. You must be VA-verified as a SDVOSB to submit a bid.", canBid: true },
  SDVOSBS:  { who: "Service-Disabled Veteran-Owned Small Business (SDVOSB)", plain: "The agency selected one SDVOSB directly — no open competition. This is a sole-source award.", canBid: false },
  VOSB:     { who: "Veteran-Owned Small Business (VOSB)", plain: "Only VA-verified VOSBs can bid. You must hold an active VOSB certification through the VA's VetCert program.", canBid: true },
  VSB:      { who: "Veteran-Owned Small Business (VOSB)", plain: "Only VA-verified VOSBs can bid. You must hold an active VOSB certification through the VA's VetCert program.", canBid: true },
  "8AN":    { who: "SBA 8(a) Certified Small Business", plain: "Open competition, but only businesses enrolled in the SBA's 8(a) Business Development Program can bid.", canBid: true },
  "8A":     { who: "SBA 8(a) Certified Small Business", plain: "The agency selected a specific 8(a) firm directly. No open competition — sole-source award.", canBid: false },
  SBA:      { who: "Small Business (any)", plain: "Open to any small business that meets SBA's size standards for this industry (NAICS code). No veteran certification required.", canBid: true },
  SBP:      { who: "Small Business (partial set-aside)", plain: "Part of this contract is reserved for small businesses; the rest is unrestricted. Check SAM.gov for the split details.", canBid: true },
  HZC:      { who: "HUBZone Certified Business", plain: "Only businesses certified in a Historically Underutilized Business Zone (HUBZone) can compete.", canBid: true },
  HZS:      { who: "HUBZone Certified Business", plain: "Sole-source to a specific HUBZone firm. No competition.", canBid: false },
  WOSB:     { who: "Woman-Owned Small Business (WOSB)", plain: "Only WOSB-certified businesses can bid. Certification comes from SBA or an SBA-approved third party.", canBid: true },
  WOSBSS:   { who: "Woman-Owned Small Business (WOSB)", plain: "Sole-source to a specific WOSB — no open competition.", canBid: false },
  EDWOSB:   { who: "Economically Disadvantaged WOSB (EDWOSB)", plain: "Similar to WOSB but for businesses in industries where women are economically disadvantaged. EDWOSB certification required.", canBid: true },
  EDWOSBSS: { who: "Economically Disadvantaged WOSB (EDWOSB)", plain: "Sole-source to a specific EDWOSB — no open competition.", canBid: false },
};

export const SOLICITATION_TYPE_PLAIN = {
  o: { label: "Active Solicitation", plain: "You can submit a bid. This is a formal request for proposals (RFP), quotes (RFQ), or bids (IFB). Read the full solicitation on SAM.gov before responding.", canBid: true },
  k: { label: "Combined Synopsis / Solicitation", plain: "A streamlined format that combines the public notice and the solicitation in one document. You can submit a bid directly.", canBid: true },
  p: { label: "Pre-Solicitation Notice", plain: "The agency is signaling a contract is coming soon but hasn't released the full solicitation yet. Bookmark this and check back — you'll want to bid when it opens.", canBid: false },
  r: { label: "Sources Sought / Market Research", plain: "The agency is researching vendors before writing a solicitation. Responding here is not a bid — it's a chance to introduce your company and shape the requirements. Highly recommended.", canBid: false },
  s: { label: "Special Notice", plain: "An informational announcement from the agency — conference invites, industry days, or other updates. Not a solicitation.", canBid: false },
  i: { label: "Intent to Bundle (DoD)", plain: "The Department of Defense is notifying it plans to combine contracts. This affects small business opportunities. Not a solicitation.", canBid: false },
  a: { label: "Award Notice", plain: "This contract was already awarded to another company. You cannot bid — it is closed.", canBid: false },
  u: { label: "Justification & Approval (J&A)", plain: "The agency is justifying a sole-source or limited-competition award. Generally not open for bidding.", canBid: false },
};
