// "Get a paid internship": every route an Indian student can take, for any year
// and any branch. Programs change their dates, pay and rules every year, so each
// route links to the official page and says "check current dates".

const q = encodeURIComponent;

export const YEARS = [
  { id: 'any', label: 'Any year' },
  { id: 'early', label: '1st–2nd year' },
  { id: 'third', label: '3rd year' },
  { id: 'final', label: 'Final year / graduate' },
];

export const FIELDS = [
  { id: 'any', label: 'Any field' },
  { id: 'cs', label: 'CS / IT / AI' },
  { id: 'electronics', label: 'ECE / EEE' },
  { id: 'core', label: 'Mech / Civil / Chem / other engg' },
  { id: 'science', label: 'Science (BSc / MSc)' },
  { id: 'business', label: 'Commerce / Management / Arts' },
];

export const SPEED = { fast: 'Fast: days to weeks', medium: 'A few weeks to months', slow: 'Plan months ahead' };

export const linkedinPosts = (role) =>
  `https://www.linkedin.com/search/results/content/?keywords=${q(`hiring intern ${role}`)}&sortBy=%22date_posted%22`;

/**
 * Each route: `years` and `fields` list who it suits (empty = everyone).
 * `pay` is what students commonly report; programs set their own amounts.
 */
export const ROUTES = [
  {
    id: 'portals',
    title: 'Apply early and in volume on Internshala and Unstop',
    speed: 'fast',
    pay: '₹2,000–25,000 a month (higher for tech roles)',
    years: [],
    fields: [],
    why: 'The quickest route for most students. Companies often shortlist the first 50–100 applicants, so speed matters more than marks.',
    steps: [
      'Make a one-page resume (FitLens Build) and a short “About me” you can reuse.',
      'Turn on alerts for 2–3 roles and apply within 24–48 hours of a post going up.',
      'Answer the screening question properly; most people paste one line.',
      'Apply to 5–10 a day for two weeks. Expect 1 reply for every 15–20 applications at first.',
      'Do assignments the same day they arrive: many companies hire the first good submission.',
    ],
    links: [
      { label: 'Internshala internships', href: 'https://internshala.com/internships/' },
      { label: 'Unstop internships', href: 'https://unstop.com/internships' },
    ],
  },
  {
    id: 'linkedin-posts',
    title: 'Reply to “hiring intern” posts on LinkedIn',
    speed: 'fast',
    pay: 'Varies; startups often ₹5,000–20,000 a month',
    years: [],
    fields: [],
    why: 'Founders and managers post openings as normal posts before they reach job sites. Few students search posts, so competition is lower.',
    steps: [
      'Use the “Recent hiring posts” link below with your role (it sorts by newest).',
      'Comment “Interested” AND message the poster with 3 lines: who you are, one relevant project, your resume link.',
      'Connect with 5 recruiters or founders in your field every day with a short note.',
      'Post your own “Looking for an internship” update with your skills and one project screenshot.',
    ],
    links: [{ label: 'Recent hiring posts (edit the role)', href: linkedinPosts('') }],
  },
  {
    id: 'startups',
    title: 'Message startup founders directly',
    speed: 'fast',
    pay: '₹5,000–30,000 a month, sometimes a job offer later',
    years: [],
    fields: [],
    why: 'Small startups hire whoever shows they can help, often without a formal process.',
    steps: [
      'Find startups on Wellfound, Work at a Startup (YC) and LinkedIn in your city or field.',
      'Use their product and note one thing you could improve or build.',
      'Message the founder with the cold message template: what you noticed, what you can do, a link to your work.',
      'Offer a small paid trial task (a week) instead of asking for “any internship”.',
    ],
    links: [
      { label: 'Wellfound (AngelList) jobs', href: 'https://wellfound.com/jobs' },
      { label: 'Work at a Startup (YC)', href: 'https://www.workatastartup.com/' },
    ],
  },
  {
    id: 'professors',
    title: 'Email professors for a research internship',
    speed: 'medium',
    pay: 'Often unpaid or a small stipend; project-funded roles pay. A strong letter and research credit either way.',
    years: [],
    fields: [],
    why: 'Works for any branch, including core engineering and science. Few students do it well, and one “yes” can turn into a paper and a recommendation letter.',
    steps: [
      'Pick 20–30 professors at IITs, NITs, IIITs, IISc or your own college whose work you find interesting (faculty pages, Google Scholar).',
      'Read the abstract of 1–2 of their recent papers.',
      'Send a short personal email (template below): one line about their work, why you fit, what you have done, resume attached as PDF.',
      'Send 3–5 emails a day, never one copied email to everyone. Follow up once after 7–10 days.',
      'Write 2–3 months before you want to start (October–February for summer).',
    ],
    links: [{ label: 'Google Scholar', href: 'https://scholar.google.com/' }],
  },
  {
    id: 'nptel',
    title: 'Top an NPTEL course for an IIT internship',
    speed: 'slow',
    pay: 'In-person NPTEL internships have paid about ₹7,500 for 2 weeks and ₹15,000 for 4 weeks (check current rates)',
    years: [],
    fields: [],
    why: 'Free courses taught by IIT and IISc professors. Course toppers and Elite + Gold scorers can be invited to intern with the course instructor.',
    steps: [
      'Pick an NPTEL course in your field that has a proctored exam this semester.',
      'Do every weekly assignment (they count toward your score) and aim for Elite + Gold.',
      'If you are among the toppers, NPTEL or the instructor contacts you to apply with your resume, grade sheets and a one-page statement.',
      'Even without the internship, the certificate is a strong resume line and many colleges give credit for it.',
    ],
    links: [
      { label: 'NPTEL courses', href: 'https://nptel.ac.in/courses' },
      { label: 'NPTEL internship rules', href: 'https://nptel.ac.in/internship' },
    ],
  },
  {
    id: 'summer-research',
    title: 'Summer research fellowships (IITs, IISc, science academies)',
    speed: 'slow',
    pay: 'Usually a monthly stipend, sometimes travel and hostel; amounts differ by program',
    years: ['early', 'third'],
    fields: ['cs', 'electronics', 'core', 'science'],
    why: 'Structured, paid research summers at top institutes, open to students from any college.',
    steps: [
      'Science academies (IAS-INSA-NASI) Summer Research Fellowship: applications usually close around the end of November.',
      'IIT summer programs (for example IIT Madras SFP, IIT Gandhinagar SRIP, IIT Hyderabad and IIT Delhi summer fellowships) usually open between December and March. Some, like IIT Kanpur SURGE, mainly take their own students; read each program’s eligibility.',
      'Prepare a statement of purpose, your grade sheets and a faculty recommendation in advance.',
      'Apply to several programs in the same season; acceptance rates are low.',
    ],
    links: [
      { label: 'Indian Academy of Sciences fellowships', href: 'https://www.ias.ac.in/' },
      { label: 'IIT Gandhinagar SRIP', href: 'https://srip.iitgn.ac.in/' },
      { label: 'IIT Madras Summer Fellowship', href: 'https://ssp.iitm.ac.in/' },
    ],
  },
  {
    id: 'abroad',
    title: 'Fully funded internships abroad',
    speed: 'slow',
    pay: 'Funded: travel and living costs covered (varies by program)',
    years: ['third', 'early'],
    fields: ['cs', 'electronics', 'core', 'science'],
    why: 'Competitive, but they take students from any Indian college with good grades and a clear research interest.',
    steps: [
      'Mitacs Globalink (Canada): 12-week research internships; apply in your third year, usually around September.',
      'DAAD WISE (Germany): research internships for science and engineering students, usually after the 2nd or 3rd year.',
      'Khorana Program and S.N. Bose Scholars (USA, through IUSSTF): summer research for science and engineering students.',
      'Start a year early: you need a professor’s recommendation and, for some, a host professor’s acceptance.',
    ],
    links: [
      { label: 'Mitacs Globalink', href: 'https://www.mitacs.ca/our-programs/globalink-research-internship-students/' },
      { label: 'DAAD India', href: 'https://www.daad.in/en/' },
      { label: 'IUSSTF (Khorana, S.N. Bose)', href: 'https://www.iusstf.org/' },
    ],
  },
  {
    id: 'government',
    title: 'Government internship portals',
    speed: 'medium',
    pay: 'Many are paid; the PM Internship Scheme pays a monthly stipend for a year',
    years: [],
    fields: [],
    why: 'Thousands of openings that many students never check.',
    steps: [
      'AICTE Internship Portal: internships from companies and government bodies, many with stipends.',
      'PM Internship Scheme: year-long internships in top companies with a monthly stipend. It is meant for young people not in full-time study or work (originally 21–24 years old); check the current rules on the official site.',
      'Ministries, RBI, NITI Aayog, ISRO and DRDO run internships too. Many are unpaid but carry a strong name; check each official site.',
    ],
    links: [
      { label: 'AICTE Internship Portal', href: 'https://internship.aicte-india.org/' },
      { label: 'PM Internship Scheme', href: 'https://pminternship.mca.gov.in/' },
    ],
  },
  {
    id: 'competitions',
    title: 'Win or place in hackathons and company competitions',
    speed: 'medium',
    pay: 'Internship and pre-placement offers, plus prize money',
    years: [],
    fields: ['cs', 'electronics', 'business'],
    why: 'Companies use competitions as hiring: doing well can skip the resume shortlist entirely.',
    steps: [
      'Smart India Hackathon (via your college), Flipkart GRiD, Myntra HackerRamp, TCS CodeVita and many others on Unstop.',
      'Business and case competitions on Unstop work the same way for management and commerce students.',
      'Form a team with complementary skills and build something that runs, even if it is small.',
      'Put every finalist result on your resume and LinkedIn.',
    ],
    links: [
      { label: 'Hackathons on Unstop', href: 'https://unstop.com/hackathons' },
      { label: 'Competitions on Unstop', href: 'https://unstop.com/competitions' },
      { label: 'Smart India Hackathon', href: 'https://www.sih.gov.in/' },
    ],
  },
  {
    id: 'open-source',
    title: 'Paid open-source programs',
    speed: 'slow',
    pay: 'Stipends: C4GT has offered about ₹1 lakh; GSoC and LFX pay in dollars',
    years: [],
    fields: ['cs', 'electronics'],
    why: 'Real work with mentors that counts like an internship, from your room.',
    steps: [
      'Google Summer of Code: open to beginners in open source (18+). Organisations are announced in early spring.',
      'Code for GovTech (C4GT): Indian open-source GovTech projects with a stipend, for students and professionals.',
      'LFX Mentorship (Linux Foundation) and Outreachy (for people under-represented in tech).',
      'Start 2–3 months early: fix small issues in the project before applying.',
    ],
    links: [
      { label: 'Google Summer of Code', href: 'https://summerofcode.withgoogle.com/' },
      { label: 'Code for GovTech', href: 'https://www.codeforgovtech.in/' },
      { label: 'LFX Mentorship', href: 'https://lfx.linuxfoundation.org/tools/mentorship/' },
      { label: 'Outreachy', href: 'https://www.outreachy.org/' },
    ],
  },
  {
    id: 'company-programs',
    title: 'Big-company programs for early-year students',
    speed: 'slow',
    pay: 'Well paid; very competitive',
    years: ['early'],
    fields: ['cs'],
    why: 'Some large companies run internships only for first- and second-year students, so you don’t compete with final years.',
    steps: [
      'Google STEP is the best known; read its current eligibility on the official page.',
      'Several companies run women-only programs and coding contests that lead to internships: watch their careers pages and Unstop.',
      'Practise data structures and algorithms and have one solid project before applying.',
    ],
    links: [{ label: 'Google STEP', href: 'https://buildyourfuture.withgoogle.com/programs/step' }],
  },
  {
    id: 'network',
    title: 'Seniors, alumni and your college T&P cell',
    speed: 'fast',
    pay: 'Depends on the company; referrals get many more interviews',
    years: [],
    fields: [],
    why: 'A referral moves your resume to the top. Seniors who interned last year know exactly who is hiring.',
    steps: [
      'Ask your T&P cell and department about internship drives and company tie-ups, including off-season ones.',
      'Open your college’s LinkedIn page, go to “Alumni”, filter by company or role, and message 5 alumni a week.',
      'Ask seniors which teams hired interns last summer and whether they can refer you.',
      'Ask professors with industry projects or consulting work; they often need interns.',
      'Check your college incubator: its startups need interns and know your college.',
    ],
    links: [],
  },
  {
    id: 'core-industry',
    title: 'Core industry training (plants, sites, PSUs)',
    speed: 'medium',
    pay: 'Often unpaid or a small stipend; valued by core companies',
    years: ['early', 'third'],
    fields: ['core', 'electronics'],
    why: 'For Mechanical, Civil, Electrical and Chemical students, real plant or site experience matters more than certificates.',
    steps: [
      'Write to the training or HR departments of PSUs and large plants (power, steel, railways, construction) for vocational training.',
      'Ask local contractors, builders, workshops and manufacturers for a summer site internship; walk in with your resume.',
      'Use relatives’ and alumni contacts in core companies; most of these openings are never posted online.',
      'Combine it with a CAD or simulation skill (AutoCAD, SolidWorks, ANSYS, STAAD Pro) to get paid design internships.',
    ],
    links: [],
  },
  {
    id: 'business-roles',
    title: 'Marketing, sales, content and operations internships',
    speed: 'fast',
    pay: '₹3,000–15,000 a month, often with incentives',
    years: [],
    fields: ['business', 'science'],
    why: 'Plenty of openings for any degree, with fast hiring. Good for building communication and business skills.',
    steps: [
      'Search Internshala for marketing, business development, content writing, HR and operations roles.',
      'Show one sample: a social media plan, a short market analysis or a blog post.',
      'Avoid roles that pay only commission or ask you to buy products to sell.',
      'Commerce students: ask CA firms and accountants for internships during tax season (February–July).',
    ],
    links: [{ label: 'Internshala: marketing internships', href: 'https://internshala.com/internships/marketing-internship/' }],
  },
  {
    id: 'freelance',
    title: 'Freelance first, then turn a client into an internship',
    speed: 'fast',
    pay: 'Paid per task from the first week',
    years: [],
    fields: [],
    why: 'A small paid project is the easiest proof you can work. Happy clients often offer internships or refer you.',
    steps: [
      'Use the Earn guide to pick a service and land a first client.',
      'Do great work for a startup or agency, then ask if they need an intern for a few months.',
      'List freelance work on your resume like an internship: client, what you did, the result.',
    ],
    links: [{ label: 'Open the Earn guide', href: '/earn' }],
  },
  {
    id: 'teaching',
    title: 'Paid teaching-assistant and doubt-solving roles',
    speed: 'fast',
    pay: 'Per hour or per answer',
    years: [],
    fields: [],
    why: 'EdTech companies and coaching centres pay students who are good at a subject to solve doubts, review code or assist classes.',
    steps: [
      'Look for “teaching assistant”, “subject matter expert” or “doubt solver” roles on Internshala and LinkedIn.',
      'Coaching centres near you often need part-time help for school students.',
      'Pass their subject test: brush up the basics first.',
    ],
    links: [{ label: 'Internshala: teaching internships', href: 'https://internshala.com/internships/teaching-internship/' }],
  },
];

export const BOOSTERS = [
  'One-page resume with projects first and numbers in every bullet: check it with FitLens before applying.',
  'One real project in your field, live or on GitHub/Drive, beats five certificates.',
  'A complete LinkedIn profile with a clear headline (“ECE student | Embedded systems | Arduino”).',
  'Free company job simulations (for example on Forage) are a quick resume line when you have no experience.',
  'Track every application in the FitLens tracker and follow up after a week.',
  'Summer internships are mostly filled between December and March. Start early.',
];

export const RED_FLAGS = [
  'Paying for an internship, a “certificate fee”, “training fee” or “registration fee”. Real internships pay you.',
  '“Internship certificate guaranteed” programs that sell certificates without real work.',
  'Commission-only “internships” where you must sell courses or products to friends and family.',
  'Offers that come only on WhatsApp or Telegram with no company website, email domain or interview.',
  'Asking for your bank login, OTP or Aadhaar before an offer letter.',
];

export const TEMPLATES = [
  {
    id: 'professor',
    title: 'Email to a professor',
    text: `Subject: Summer research internship – {your branch}, {college}

Dear Prof. {Last name},

I am {Your name}, a {year} {branch} student at {college}. I read your recent work on {paper/topic} and was interested in {one specific idea from it}.

I have {one relevant thing: a course, project or skill, e.g. "built a {project} using {tool}"}, and I would like to work on {their area} under your guidance this {summer/winter}, from {month} for {6–8} weeks.

My resume is attached. I would be grateful for any opportunity to contribute, remote or on campus.

Thank you for your time.
{Your name}
{phone} | {LinkedIn/GitHub}`,
  },
  {
    id: 'founder',
    title: 'Message to a startup founder',
    text: `Hi {name}, I'm {Your name}, a {year} {branch} student. I tried {product} and noticed {one specific thing you could improve}.

I can help with {what you can do, e.g. building landing pages / social media / data analysis}. Here's something similar I made: {link}

Would you be open to a short paid trial internship? I can start this week.`,
  },
  {
    id: 'alumni',
    title: 'Message to an alumnus for a referral',
    text: `Hi {name}, I'm {Your name}, a {year} {branch} student at {your college}, your college too. I'm applying for {role} internships and saw you work at {company}.

Could you share how interns are hired in your team? If my profile fits, I'd be grateful for a referral. My resume: {link}

Thank you!`,
  },
  {
    id: 'follow-up',
    title: 'Follow-up after a week',
    text: `Dear {name}, I wanted to follow up on my message from last week about an internship. I'm still very interested, and I've since {one new thing: finished a project, a course, a result}. Please let me know if there's a chance to contribute.

Thank you,
{Your name}`,
  },
];
