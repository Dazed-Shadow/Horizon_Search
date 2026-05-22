// ---------------------------------------------------------------------------
// TRAILBLAZERS — verified veteran entrepreneurs and public figures.
//
// All bios are drawn from publicly documented sources. Before adding a new
// figure, confirm: (1) military service via Wikipedia/official bio, (2) business
// details via company website or press coverage, (3) book details via publisher.
//
// To add a figure: copy one object, fill every field, set slug to a URL-safe
// lowercase-hyphenated version of the name. The slug becomes the ?figure= URL.
//
// Photo: we use initials avatars until real photos are sourced. Add a photoUrl
// field pointing to a CDN-hosted image when available.
// ---------------------------------------------------------------------------

export const trailblazers = [
  {
    slug: "fred-smith",
    name: "Fred Smith",
    initials: "FS",
    avatarColor: "bg-brand-700",
    branch: "U.S. Marine Corps",
    yearsServed: "1966 – 1969",
    era: "Vietnam War",
    role: "Founder & Executive Chairman, FedEx",
    oneLineHook: "Wrote the FedEx concept at Yale, then built it after two combat tours in Vietnam.",
    tags: ["Logistics", "Fortune 500", "Vietnam"],
    bio: `Fred Smith enlisted in the U.S. Marine Corps after graduating from Yale University in 1966. He served two tours in Vietnam as a forward air controller and infantry officer, flying more than 200 combat missions before being honorably discharged in 1969. His military experience — coordinating logistics under pressure across complex, distributed operations — directly shaped the hub-and-spoke model at the heart of Federal Express.

Smith founded FedEx in 1971 and launched operations in 1973 with 14 aircraft serving 25 cities. The company lost money for its first two years; Smith famously flew to Las Vegas with the company's last $5,000 and won enough at blackjack to make payroll. FedEx grew into one of the world's largest logistics companies, employing over 500,000 people, and Smith remained its executive chairman until 2022. He is widely cited as proof that military operational thinking translates directly into business architecture.`,
    resources: [
      {
        type: "book",
        title: "Changing How the World Does Business: FedEx's Incredible Journey to Success",
        author: "Roger Frock",
        description: "Written by FedEx's original COO — the inside story of building the company from scratch.",
        url: "https://www.amazon.com/dp/1576753794",
      },
      {
        type: "article",
        title: "Fred Smith — Biography",
        author: "Wikipedia",
        description: "Comprehensive sourced biography covering military service and FedEx founding.",
        url: "https://en.wikipedia.org/wiki/Fred_Smith_(businessman)",
      },
    ],
    externalLinks: {
      website: "https://www.fedex.com",
      wikipedia: "https://en.wikipedia.org/wiki/Fred_Smith_(businessman)",
    },
  },
  {
    slug: "jocko-willink",
    name: "Jocko Willink",
    initials: "JW",
    avatarColor: "bg-gray-800",
    branch: "U.S. Navy SEALs",
    yearsServed: "1990 – 2010",
    era: "Gulf War · Global War on Terror",
    role: "Co-founder, Echelon Front · Founder, Origin USA",
    oneLineHook: "Led the most decorated special operations unit of the Iraq War, then built a leadership empire.",
    tags: ["Leadership", "Consulting", "Manufacturing", "Podcast"],
    bio: `Jocko Willink served 20 years as a U.S. Navy SEAL, retiring as a Commander in 2010. He commanded Task Unit Bruiser in Ramadi, Iraq during the 2006 Battle of Ramadi — the bloodiest urban combat of the Iraq War — for which his unit received more combat decorations than any other Naval Special Warfare unit since Vietnam. His after-action analysis of friendly-fire miscommunication in that campaign became the foundation of *Extreme Ownership*.

After retiring, Willink co-founded Echelon Front with fellow SEAL Leif Babin — a leadership consulting firm whose clients include Fortune 500 companies and the U.S. military. He also founded Origin USA, a manufacturing company in Strong, Maine that produces American-made apparel, gear, and supplements, providing jobs in a rural community. His podcast has accumulated hundreds of millions of downloads and he maintains one of the largest social media followings of any veteran entrepreneur.`,
    resources: [
      {
        type: "book",
        title: "Extreme Ownership: How U.S. Navy SEALs Lead and Win",
        author: "Jocko Willink & Leif Babin",
        description: "The leadership principles distilled from SEAL Team Three's experience in Ramadi — now a standard text in business schools.",
        url: "https://www.amazon.com/dp/1250183863",
      },
      {
        type: "book",
        title: "Discipline Equals Freedom: Field Manual",
        author: "Jocko Willink",
        description: "A practical operating philosophy on building the habits that create freedom.",
        url: "https://www.amazon.com/dp/1250274435",
      },
      {
        type: "podcast",
        title: "Jocko Podcast",
        author: "Jocko Willink",
        description: "One of the most-downloaded veteran podcasts — covers war, leadership, business, and discipline.",
        url: "https://jockopodcast.com",
      },
    ],
    externalLinks: {
      website: "https://jocko.com",
      wikipedia: "https://en.wikipedia.org/wiki/Jocko_Willink",
    },
  },
  {
    slug: "david-goggins",
    name: "David Goggins",
    initials: "DG",
    avatarColor: "bg-red-800",
    branch: "U.S. Army · U.S. Navy SEALs",
    yearsServed: "1994 – 2016",
    era: "Global War on Terror",
    role: "Author · Speaker · Ultra-Endurance Athlete",
    oneLineHook: "Started in Army Airborne, became a SEAL, then set a world pull-up record — and wrote the book on mental toughness.",
    tags: ["Army", "Special Forces", "Author", "Social Media"],
    bio: `David Goggins enlisted in the U.S. Army and served with the 2nd Ranger Battalion as a Tactical Air Control Party specialist before transitioning to the U.S. Navy and completing BUD/S training with Class 235. He is one of the few people to have completed Army Ranger School, BUD/S, and Air Force SERE School. He deployed to Iraq and served in Afghanistan before retiring in 2016.

Post-service, Goggins built one of the most recognized personal brands of any living veteran. He set a Guinness World Record for completing 4,030 pull-ups in 17 hours, has finished over 60 ultra-marathons and triathlons including the Badwater 135, and his memoir *Can't Hurt Me* sold over five million copies — making it one of the best-selling veteran-authored books of all time. He has over 7 million Instagram followers and his content reaches an audience far beyond the veteran community, making him among the most effective bridges between military culture and civilian audiences.`,
    resources: [
      {
        type: "book",
        title: "Can't Hurt Me: Master Your Mind and Defy the Odds",
        author: "David Goggins",
        description: "Part memoir, part mental-toughness manual. One of the best-selling books ever written by a veteran.",
        url: "https://www.amazon.com/dp/1544512279",
      },
      {
        type: "book",
        title: "Never Finished: Unshackle Your Mind and Win the War Within",
        author: "David Goggins",
        description: "The follow-up — on what comes after you've broken every limit you thought you had.",
        url: "https://www.amazon.com/dp/1544534078",
      },
    ],
    externalLinks: {
      website: "https://davidgoggins.com",
      wikipedia: "https://en.wikipedia.org/wiki/David_Goggins",
    },
  },
  {
    slug: "mark-geist",
    name: 'Mark "Oz" Geist',
    initials: "MG",
    avatarColor: "bg-olive-600",
    branch: "U.S. Marine Corps",
    yearsServed: "1983 – 1993",
    era: "Cold War · Gulf War",
    role: "Author · Founder, Shadow Warriors Project",
    oneLineHook: "Survived the Benghazi attack, co-wrote the book that became a Michael Bay film, and never stopped advocating for the operators left behind.",
    tags: ["Marine Corps", "Author", "Nonprofit", "Film"],
    bio: `Mark Geist served in the U.S. Marine Corps before transitioning to private security contracting. On the night of September 11–12, 2012, he was one of six CIA security contractors at the Benghazi Annex when the facility came under coordinated attack. Despite being severely wounded — he lost significant use of his right arm — he fought for 13 hours alongside his team and survived.

Geist co-authored *13 Hours: The Inside Account of What Really Happened in Benghazi* (2014) with Mitchell Zuckoff and his five fellow team members. The book became a *New York Times* bestseller and the basis for the 2016 Michael Bay film *13 Hours: The Secret Soldiers of Benghazi*. He founded the Shadow Warriors Project, a nonprofit providing support and legal resources to intelligence community veterans and contractors. He now speaks nationally on leadership, sacrifice, and the obligations society owes to those who serve in the shadows of public awareness.`,
    resources: [
      {
        type: "book",
        title: "13 Hours: The Inside Account of What Really Happened in Benghazi",
        author: "Mitchell Zuckoff with the Annex Security Team",
        description: "The firsthand account from the six men who fought that night — a New York Times bestseller.",
        url: "https://www.amazon.com/dp/1455530050",
      },
      {
        type: "article",
        title: "Shadow Warriors Project",
        author: "shadowwarriorsproject.org",
        description: "The nonprofit Geist founded to support intelligence community veterans and contractors.",
        url: "https://shadowwarriorsproject.org",
      },
    ],
    externalLinks: {
      website: "https://shadowwarriorsproject.org",
      wikipedia: "https://en.wikipedia.org/wiki/2012_Benghazi_attack",
    },
  },
  {
    slug: "adam-driver",
    name: "Adam Driver",
    initials: "AD",
    avatarColor: "bg-indigo-800",
    branch: "U.S. Marine Corps",
    yearsServed: "2001 – 2003",
    era: "Post-9/11",
    role: "Actor · Founder, Arts in the Armed Forces (AITAF)",
    oneLineHook: "Enlisted after 9/11, was medically discharged before deployment, then built both a Hollywood career and a nonprofit that brings live theater to every corner of the U.S. military.",
    tags: ["Marine Corps", "Entertainment", "Nonprofit", "Arts"],
    bio: `Adam Driver enlisted in the U.S. Marine Corps at 17 in the weeks following September 11, 2001, serving with 1st Battalion, 1st Marines. He was preparing to deploy to Iraq when a mountain biking accident fractured his sternum; he received an honorable medical discharge in 2003 after two years of service. He then attended Juilliard School of Drama on his second application.

Driver went on to become one of the most critically recognized actors of his generation — known for Kylo Ren in the *Star Wars* sequel trilogy, an Academy Award nomination for *Marriage Story*, and roles in *BlacKkKlansman*, *House of Gucci*, and *Ferrari*. In 2008 he founded Arts in the Armed Forces (AITAF), a nonprofit that brings professional theater performances to active-duty military personnel, veterans, and their families on bases worldwide — every continent where U.S. forces are stationed. AITAF represents his belief that the arts are not a luxury but a tool for processing experience and building resilience, and it directly serves the veteran community he was briefly part of.`,
    resources: [
      {
        type: "article",
        title: "Arts in the Armed Forces",
        author: "artsinthearmedforces.org",
        description: "The nonprofit Driver founded — bringing professional theater to military communities globally.",
        url: "https://www.artsinthearmedforces.org",
      },
      {
        type: "article",
        title: "Adam Driver on His Time in the Marines",
        author: "The New Yorker",
        description: "A profile tracing the line from enlisting after 9/11 to Juilliard to founding AITAF.",
        url: "https://www.newyorker.com/magazine/2019/10/28/adam-drivers-method",
      },
    ],
    externalLinks: {
      website: "https://www.artsinthearmedforces.org",
      wikipedia: "https://en.wikipedia.org/wiki/Adam_Driver",
    },
  },
];
