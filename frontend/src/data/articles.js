// ---------------------------------------------------------------------------
// ARTICLES — curated links to veteran business coverage.
//
// Sourcing priority: SBA Boots to Business archive, Inc. Vet 100, Forbes,
// Task & Purpose, We Are The Mighty, HBR, veteran podcasts.
//
// Inclusion bar (all three required):
//   1. Subject is a verifiable U.S. military veteran.
//   2. Story is about post-service building — a business, a contract won,
//      a creative venture — not a combat retrospective.
//   3. Source is reputable (no content farms).
//
// Buckets: "Funding & Contracts" | "Founder Profiles" | "Media & Creators"
//          | "Leadership Lessons" | "Policy & Programs"
//
// featured_figure_slug: ties this article to a Trailblazer card so it
// appears in the drawer's "Related reading" section.
//
// IMPORTANT: URLs marked verify:true need a real link before publishing.
// Replace the placeholder url with the actual article URL.
// ---------------------------------------------------------------------------

export const articles = [
  {
    id: "sba-vosb-set-aside-guide",
    title: "Guide to Veteran-Owned Small Business Set-Asides",
    source: "U.S. Small Business Administration",
    sourceShort: "SBA",
    author: "SBA Office of Veterans Business Development",
    published: "2024",
    url: "https://www.sba.gov/federal-contracting/contracting-assistance-programs/veteran-assistance-programs",
    summary: "The official SBA breakdown of every veteran set-aside program — SDVOSB, VOSB, eligibility requirements, and how to apply. The authoritative starting point for any veteran entering federal contracting.",
    bucket: "Policy & Programs",
    featured_figure_slug: null,
    verify: false,
  },
  {
    id: "sba-boots-to-business",
    title: "Boots to Business: From Service to Entrepreneurship",
    source: "U.S. Small Business Administration",
    sourceShort: "SBA",
    author: "SBA Boots to Business Program",
    published: "2024",
    url: "https://www.sba.gov/offices/headquarters/ovbd/resources/1504",
    summary: "SBA's entrepreneurship education program for transitioning service members. Free two-day course, online follow-on, and access to a national network of veteran business advisors.",
    bucket: "Policy & Programs",
    featured_figure_slug: null,
    verify: false,
  },
  {
    id: "inc-vet-100-2023",
    title: "Inc. Vet100 2023: The Fastest-Growing Veteran-Led Businesses Unveiled",
    source: "Inc. / IVMF at Syracuse University",
    sourceShort: "Inc. / IVMF",
    author: "IVMF Communications",
    published: "2023",
    url: "https://ivmf.syracuse.edu/2023/11/02/inc-business-medias-vet100-2024-list-unveiled/",
    summary: "Annual ranking of the 100 fastest-growing veteran-owned businesses in America, co-produced by Inc. and the Institute for Veterans and Military Families at Syracuse University. A benchmark list for veteran entrepreneurs tracking what's possible — and which industries are growing fastest.",
    bucket: "Founder Profiles",
    featured_figure_slug: null,
    verify: false,
  },
  {
    id: "forbes-veteran-founders",
    title: "Vetrepreneur: Veterans in Business — Forbes Coverage",
    source: "Forbes",
    sourceShort: "Forbes",
    author: "Forbes Staff",
    published: "Ongoing",
    url: "https://www.forbes.com/vetrepreneur/",
    summary: "Forbes' dedicated section covering veteran entrepreneurs — profiles of veterans who translated military experience in logistics, leadership under pressure, and team cohesion into business success at scale.",
    bucket: "Founder Profiles",
    featured_figure_slug: "fred-smith",
    verify: false,
  },
  {
    id: "hbr-military-leadership",
    title: "Veterans Can Bring a Rare Set of Skills to Your Organization",
    source: "Harvard Business Review",
    sourceShort: "HBR",
    author: "Mike Erwin & Raymond Coia",
    published: "2021",
    url: "https://hbr.org/2021/11/veterans-can-bring-a-rare-set-of-skills-to-your-organization",
    summary: "HBR analysis of the specific competencies — mission clarity, decentralized decision-making, subordinate development — that military training builds and that translate into measurable business outcomes.",
    bucket: "Leadership Lessons",
    featured_figure_slug: "jocko-willink",
    verify: false,
  },
  {
    id: "task-purpose-sdvosb",
    title: "Veteran-Owned Businesses Can and Should Be a Force for Good",
    source: "Task & Purpose",
    sourceShort: "Task & Purpose",
    author: "Task & Purpose Staff",
    published: "2022",
    url: "https://taskandpurpose.com/military-life/veteran-owned-businesses-can-force-good/",
    summary: "On-the-ground coverage of veteran entrepreneurs and why veteran-owned businesses have an outsized opportunity — and responsibility — to shape their communities and industries.",
    bucket: "Funding & Contracts",
    featured_figure_slug: null,
    verify: false,
  },
  {
    id: "jocko-podcast-leadership",
    title: "Extreme Ownership — Leadership in Business and War",
    source: "Jocko Podcast",
    sourceShort: "Podcast",
    author: "Jocko Willink & Leif Babin",
    published: "2022",
    url: "https://jockopodcast.com",
    summary: "Episode series on applying the Extreme Ownership framework to business — decentralized command, cover and move, prioritize and execute. One of the most listened-to veteran leadership resources available.",
    bucket: "Leadership Lessons",
    featured_figure_slug: "jocko-willink",
    verify: false,
  },
  {
    id: "wearethemighty-adam-driver-aitaf",
    title: "Adam Driver Is Funding Theater on Military Bases Through AITAF",
    source: "We Are The Mighty",
    sourceShort: "WATM",
    author: "We Are The Mighty Staff",
    published: "2022",
    url: "https://www.wearethemighty.com/mighty-trending/adam-driver-fund-military-bases/",
    summary: "Profile of Arts in the Armed Forces (AITAF) — the nonprofit Driver founded after his medical discharge — and the Action Fund that brought live theater to troops on military bases worldwide.",
    bucket: "Media & Creators",
    featured_figure_slug: "adam-driver",
    verify: false,
  },
  {
    id: "13-hours-legacy",
    title: "About Mark 'Oz' Geist and the Shadow Warriors Project",
    source: "Shadow Warriors Project",
    sourceShort: "SWP",
    author: "Shadow Warriors Project",
    published: "2022",
    url: "https://shadowwarriorsproject.org/about-mark-oz-geist/",
    summary: "How a Benghazi survivor built a nonprofit to support intelligence community veterans overlooked by traditional veteran services — and what it means to serve in the shadows.",
    bucket: "Founder Profiles",
    featured_figure_slug: "mark-geist",
    verify: false,
  },
];

export const BUCKETS = [
  "All",
  "Funding & Contracts",
  "Founder Profiles",
  "Media & Creators",
  "Leadership Lessons",
  "Policy & Programs",
];
