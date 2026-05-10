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
