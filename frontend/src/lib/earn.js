// Content for the Earn page: freelancing for students, starting from zero.
// Prices are typical *starting* prices seen on Indian local work and on the big
// platforms; they change, so every service links to live searches where the
// student can check what others charge today.

const q = encodeURIComponent;
export const searchLinks = (term) => [
  { label: 'See gigs on Fiverr', href: `https://www.fiverr.com/search/gigs?query=${q(term)}` },
  { label: 'See jobs on Upwork', href: `https://www.upwork.com/nx/search/jobs/?q=${q(term)}` },
  { label: 'See jobs on Freelancer', href: `https://www.freelancer.com/jobs/?keyword=${q(term)}` },
];
export const tutorialLink = (term) => `https://www.youtube.com/results?search_query=${q(`${term} tutorial for beginners`)}`;

export const LEVELS = [
  { id: 'zero', label: 'I have zero skills', hint: 'AI tools do the hard part; you check and deliver.' },
  { id: 'basics', label: 'I know some basics', hint: 'Excel, Canva, good English or a school subject.' },
  { id: 'tech', label: 'I have tech skills', hint: 'Coding, data, design or engineering software.' },
];

/**
 * Services a student can sell. `skills` (lower-case) match resume skills, so a
 * checked resume can highlight the right ones.
 */
export const SERVICES = [
  // ------------------------------------------------------------------ zero skills
  {
    id: 'canva-posts',
    level: 'zero',
    title: 'Social media posts for local shops',
    what: 'Make Instagram and WhatsApp posts, festival greetings and offer banners for shops, salons, gyms, tuition centres and restaurants near you.',
    tools: ['Canva (free, Magic Design makes a post from one line)', 'ChatGPT or Gemini (captions and offer text)'],
    youDo: 'Pick colours that match the shop, fix the AI text, check spellings and prices with the owner.',
    price: '₹150–300 a post, or ₹1,500–3,000 a month for 12 posts',
    learn: '2–3 days',
    where: 'Shops in your area (walk in or WhatsApp them), Instagram, Fiverr',
    search: 'canva social media post design',
    samples: 'Make 3 Diwali/offer posts for a real shop near you (without their logo), and 3 for an imaginary café.',
    skills: ['canva', 'graphic design', 'social media'],
  },
  {
    id: 'data-entry',
    level: 'zero',
    title: 'Data entry and PDF / photo to Excel',
    what: 'Type or convert lists, bills, forms, scanned PDFs and photos of registers into clean Excel or Google Sheets.',
    tools: ['Google Lens or Gemini (reads text and tables from photos)', 'Google Sheets (free)'],
    youDo: 'Check every number and name against the original. Accuracy is the whole job.',
    price: '₹300–1,000 a small job; $5–15 on platforms',
    learn: '1–2 days',
    where: 'Coaching centres, shops, small offices, Upwork, Freelancer',
    search: 'data entry pdf to excel',
    samples: 'Convert a printed price list and a 2-page PDF table into neat sheets with headings and totals.',
    skills: ['excel', 'google sheets', 'data entry', 'microsoft office'],
  },
  {
    id: 'resumes',
    level: 'zero',
    title: 'Resume and LinkedIn makeovers',
    what: 'Turn juniors’ and friends’ messy resumes into clean, ATS-friendly ones and polish their LinkedIn headline and About section.',
    tools: ['FitLens Build (free templates, PDF and Word download)', 'FitLens Check (ATS score before and after)', 'ChatGPT (better bullet wording)'],
    youDo: 'Never invent experience. Ask them for real numbers and projects, then show the before/after ATS score.',
    price: '₹200–500 a resume; ₹300–700 with LinkedIn',
    learn: '1 day',
    where: 'Your college WhatsApp groups, juniors, LinkedIn, relatives finishing degrees',
    search: 'ats resume writing',
    samples: 'Redo your own resume and 2 friends’ (with permission). Keep the before/after scores as proof.',
    skills: [],
  },
  {
    id: 'reels',
    level: 'zero',
    title: 'Reels and Shorts editing with captions',
    what: 'Cut raw phone videos into 15–60 second reels with captions, music and text for shops, coaches, gyms and small creators.',
    tools: ['CapCut (free: auto captions, templates)', 'InShot', 'ChatGPT (hooks and captions)'],
    youDo: 'Pick the best moments, keep captions correct, use only music allowed by Instagram/YouTube.',
    price: '₹200–800 a reel; ₹3,000–8,000 a month for regular clients',
    learn: '3–5 days',
    where: 'Local businesses, coaching institutes, YouTubers, Fiverr',
    search: 'reels editing capcut',
    samples: 'Shoot 3 short videos around your college or a shop and edit them into reels with captions.',
    skills: ['video editing', 'premiere pro', 'after effects'],
  },
  {
    id: 'translation',
    level: 'zero',
    title: 'Translation and subtitles in your mother tongue',
    what: 'Translate menus, posters, product descriptions and YouTube videos between English and Telugu, Hindi, Tamil, Kannada and other languages.',
    tools: ['Google Translate or ChatGPT (first draft)', 'YouTube Studio / CapCut (subtitles)'],
    youDo: 'Fix the AI draft so it sounds natural; machine translation alone gets complaints.',
    price: '₹0.5–1 a word; $5–20 a short video',
    learn: '1–2 days',
    where: 'YouTubers, local businesses, Fiverr, Upwork',
    search: 'english to hindi translation',
    samples: 'Subtitle one 3-minute YouTube video and translate a restaurant menu.',
    skills: ['translation', 'hindi', 'telugu', 'tamil'],
  },
  {
    id: 'presentations',
    level: 'zero',
    title: 'Presentations and pitch decks',
    what: 'Design clean PPTs for startups, teachers, events and small companies from their notes.',
    tools: ['Gamma or Canva (AI slides)', 'ChatGPT (outline and speaker notes)', 'PowerPoint or Google Slides'],
    youDo: 'Keep one idea per slide, check facts, match the client’s colours. Don’t make other students’ graded assignments: that is cheating and can get them, and you, in trouble.',
    price: '₹300–1,500 a deck',
    learn: '2 days',
    where: 'Startups, teachers, event organisers, Fiverr',
    search: 'powerpoint presentation design',
    samples: 'Make a 10-slide pitch deck for an imaginary startup and a 6-slide deck for a college event.',
    skills: ['powerpoint', 'presentation'],
  },
  {
    id: 'listings',
    level: 'zero',
    title: 'Product photos and listings for online sellers',
    what: 'Clean product photos (white background) and write titles and descriptions for sellers on Meesho, Amazon, Flipkart and Instagram shops.',
    tools: ['Canva background remover or remove.bg', 'ChatGPT (titles, bullet points, keywords)'],
    youDo: 'Never claim features the product doesn’t have. Check sizes and materials with the seller.',
    price: '₹50–150 a product listing',
    learn: '1–2 days',
    where: 'Home businesses, local wholesalers, Instagram sellers, Fiverr',
    search: 'product listing amazon',
    samples: 'Photograph 5 things at home, clean the photos and write a listing for each.',
    skills: ['ecommerce', 'copywriting'],
  },
  {
    id: 'google-maps',
    level: 'zero',
    title: 'Google Maps business setup',
    what: 'Get local shops onto Google Maps with photos, hours and a WhatsApp link, so customers can find them.',
    tools: ['Google Business Profile (free)', 'Canva (cover photo)'],
    youDo: 'The owner creates or verifies the profile on their own Google account. Never ask for their password; ask them to add you as a manager.',
    price: '₹500–1,500 a shop',
    learn: '1 day',
    where: 'Shops, clinics, tuition centres and restaurants near you that aren’t on Maps',
    search: 'google business profile setup',
    samples: 'Help a relative’s or neighbour’s shop for free first and take before/after screenshots.',
    skills: ['seo', 'digital marketing'],
  },
  {
    id: 'transcription',
    level: 'zero',
    title: 'Transcription and notes',
    what: 'Turn interviews, lectures, podcasts and meetings into clean text and summaries.',
    tools: ['Google Docs voice typing or YouTube auto-transcript', 'ChatGPT (summary and clean-up)'],
    youDo: 'Listen again and fix names, numbers and mistakes. Ask before putting private recordings into any AI tool.',
    price: '$5–20 an hour of audio; ₹300–800 locally',
    learn: '1 day',
    where: 'Podcasters, YouTubers, researchers, Upwork',
    search: 'transcription',
    samples: 'Transcribe a 10-minute public podcast clip with timestamps and a 5-line summary.',
    skills: ['english', 'typing'],
  },
  {
    id: 'ai-training',
    level: 'zero',
    title: 'AI training tasks (rating and labelling)',
    what: 'Companies pay people to label images, rate chatbot answers and write example answers. Some need only good English; others pay more for subject experts.',
    tools: ['The company’s own task website'],
    youDo: 'Pass their test, follow the guidelines exactly. Work can stop without notice, so treat it as extra income.',
    price: 'Paid per task or per hour; varies a lot',
    learn: 'A test of 1–3 hours',
    where: 'Apply only on the company’s official website. Never pay a “registration fee”.',
    search: 'ai data annotation',
    samples: 'No samples needed; read their guidelines carefully before the test.',
    skills: [],
  },

  // ------------------------------------------------------------------ basics
  {
    id: 'excel-dashboards',
    level: 'basics',
    title: 'Excel and Google Sheets clean-up and dashboards',
    what: 'Fix messy sheets, add formulas, pivot tables, charts and simple dashboards for shops and small businesses.',
    tools: ['Excel or Google Sheets', 'ChatGPT (writes and explains formulas)'],
    youDo: 'Test every formula on real rows; keep a copy of the original file.',
    price: '₹500–3,000 a sheet; $10–50 on platforms',
    learn: '1 week',
    where: 'Shops, accountants, small offices, Upwork, Fiverr',
    search: 'excel dashboard',
    samples: 'Build a sales dashboard and a monthly expense tracker with charts.',
    skills: ['excel', 'google sheets', 'advanced excel', 'pivot tables'],
  },
  {
    id: 'writing',
    level: 'basics',
    title: 'Blog and website writing',
    what: 'Write blog posts, website pages and product descriptions in clear English (or your language).',
    tools: ['ChatGPT or Gemini (outline, research ideas)', 'Grammarly or Google Docs (grammar)'],
    youDo: 'Write in your own words and check facts. Many clients forbid AI-written text and check for it; tell them how you use AI.',
    price: '₹0.3–1 a word; $10–40 a blog post to start',
    learn: '1 week',
    where: 'Small websites, startups, Upwork, Contra, LinkedIn',
    search: 'blog writing',
    samples: 'Publish 3 posts on Medium or LinkedIn about topics you know (your branch, a city, a hobby).',
    skills: ['content writing', 'copywriting', 'blogging', 'english'],
  },
  {
    id: 'social-manager',
    level: 'basics',
    title: 'Social media management',
    what: 'Plan, design and post content every week for 1–3 local businesses, and reply to messages.',
    tools: ['Canva', 'Meta Business Suite (free scheduling)', 'ChatGPT (content calendar)'],
    youDo: 'Show the owner the plan each week and share simple results (followers, enquiries).',
    price: '₹3,000–8,000 a month per business',
    learn: '1 week',
    where: 'Local businesses, start with one you already did posts for',
    search: 'social media manager',
    samples: 'A 1-month content calendar and 6 posts for one real shop.',
    skills: ['social media', 'digital marketing', 'canva', 'social media marketing'],
  },
  {
    id: 'tutoring',
    level: 'basics',
    title: 'Online tutoring',
    what: 'Teach school subjects, spoken English, coding basics or exam preparation on video calls.',
    tools: ['Google Meet', 'A whiteboard app or a phone stand'],
    youDo: 'Prepare each class, give homework and tell parents how the child is doing.',
    price: '₹200–500 an hour; more for board exams and coding',
    learn: 'You already know the subject',
    where: 'Relatives, neighbours, school WhatsApp groups, local tuition centres',
    search: 'online tutor',
    samples: 'Record one 10-minute lesson on YouTube to show how you teach.',
    skills: ['teaching', 'tutoring', 'mathematics', 'physics', 'chemistry'],
  },
  {
    id: 'virtual-assistant',
    level: 'basics',
    title: 'Virtual assistant',
    what: 'Handle email, calendars, research, spreadsheets and bookings for busy founders and small businesses.',
    tools: ['Gmail, Google Calendar, Sheets', 'ChatGPT (drafts and research)'],
    youDo: 'Reply quickly and keep the client’s data private.',
    price: '$3–8 an hour to start',
    learn: '2–3 days',
    where: 'Upwork, LinkedIn, Contra',
    search: 'virtual assistant',
    samples: 'A short document showing a research task and a cleaned-up spreadsheet you made.',
    skills: ['microsoft office', 'communication', 'google workspace'],
  },

  // ------------------------------------------------------------------ tech
  {
    id: 'websites',
    level: 'tech',
    title: 'Websites and landing pages',
    what: 'Build fast one-page websites for shops, doctors, coaching centres and events, or fix existing ones.',
    tools: ['HTML/CSS, React or WordPress', 'Vercel or Netlify (free hosting)', 'AI coding assistants'],
    youDo: 'Make it work on phones, load fast and include WhatsApp and Maps buttons.',
    price: '₹3,000–15,000 a site; $50–300 on platforms',
    learn: 'If you know HTML/CSS: 1 week',
    where: 'Local businesses without a website, Fiverr, Upwork, Contra',
    search: 'landing page website',
    samples: 'Three live sites: a café, a clinic and a coaching centre (imaginary is fine).',
    skills: ['html', 'css', 'javascript', 'react', 'next.js', 'wordpress', 'tailwind css'],
  },
  {
    id: 'automation',
    level: 'tech',
    title: 'Python automation and small tools',
    what: 'Scripts that save people time: rename files, merge Excel sheets, send reports, fill PDFs, small bots.',
    tools: ['Python', 'pandas, openpyxl', 'AI coding assistants'],
    youDo: 'Explain how to run it, handle bad input and only automate sites that allow it.',
    price: '$20–100 a script',
    learn: 'If you know Python: a few days',
    where: 'Upwork, Freelancer, offices and accountants near you',
    search: 'python automation script',
    samples: 'Three scripts on GitHub with a README and a short screen recording.',
    skills: ['python', 'pandas', 'automation', 'selenium'],
  },
  {
    id: 'data',
    level: 'tech',
    title: 'Data analysis and dashboards',
    what: 'Clean data and build Power BI, Tableau or Excel dashboards and short reports for small companies.',
    tools: ['Power BI or Tableau (free versions)', 'Python / SQL', 'AI assistants (DAX and SQL help)'],
    youDo: 'Answer the client’s real question, not just make charts.',
    price: '$20–150 a project',
    learn: 'If you know Excel or SQL: 1–2 weeks',
    where: 'Upwork, Fiverr, LinkedIn',
    search: 'power bi dashboard',
    samples: 'Two dashboards from public data (Kaggle, data.gov.in) published online.',
    skills: ['power bi', 'tableau', 'sql', 'data analysis', 'excel', 'pandas'],
  },
  {
    id: 'ai-apps',
    level: 'tech',
    title: 'AI chatbots and ML projects',
    what: 'Build chatbots on a company’s documents, small ML models and AI features for websites.',
    tools: ['Python, LangChain or LlamaIndex', 'Hugging Face', 'Streamlit (quick demos)'],
    youDo: 'Keep client data private, test answers and explain the costs of any paid AI API.',
    price: '$50–300 a project',
    learn: 'If you know Python and ML basics: 1–2 weeks',
    where: 'Upwork, Contra, startups on LinkedIn',
    search: 'ai chatbot development',
    samples: 'A chatbot over a public PDF and one ML model, both as live Streamlit demos.',
    skills: ['machine learning', 'llms', 'langchain', 'rag', 'generative ai', 'deep learning', 'python', 'streamlit'],
  },
  {
    id: 'apps',
    level: 'tech',
    title: 'Mobile apps',
    what: 'Simple Android or Flutter apps, and fixes to existing apps for small businesses.',
    tools: ['Flutter or Android (Kotlin)', 'Firebase (free tier)'],
    youDo: 'Test on real phones and agree clearly on what is included.',
    price: '$100–500 a small app',
    learn: 'If you know Flutter/Android: 2 weeks',
    where: 'Upwork, Freelancer, local businesses',
    search: 'flutter app development',
    samples: 'Two small apps on GitHub with screenshots and an APK.',
    skills: ['flutter', 'android', 'kotlin', 'react native', 'dart'],
  },
  {
    id: 'design',
    level: 'tech',
    title: 'UI/UX and logo design',
    what: 'App and website screens, logos and brand kits for startups and small businesses.',
    tools: ['Figma (free)', 'Canva', 'AI image tools for ideas only'],
    youDo: 'Original work only; never copy other brands’ logos or paid fonts and images.',
    price: '$20–200 a project',
    learn: 'If you know Figma: 1 week',
    where: 'Behance, Dribbble, Fiverr, Contra',
    search: 'figma ui design',
    samples: 'Redesign 2 apps you use and a logo kit for an imaginary brand, posted on Behance.',
    skills: ['figma', 'ui/ux design', 'adobe photoshop', 'illustrator'],
  },
  {
    id: 'engineering',
    level: 'tech',
    title: 'CAD, drafting and engineering help',
    what: '2D drawings, 3D models, simulations and BOMs for workshops, startups and makers.',
    tools: ['AutoCAD, SolidWorks, CATIA, Fusion 360 (free for students)'],
    youDo: 'Follow the client’s standards and units; check every dimension.',
    price: '$15–150 a drawing or model',
    learn: 'If you know the software: a few days',
    where: 'Upwork, Freelancer, local fabrication shops',
    search: 'autocad drafting',
    samples: '3 drawings or models of everyday parts with dimensions.',
    skills: ['autocad', 'solidworks', 'catia', 'ansys', 'creo', 'fusion 360', 'staad pro'],
  },
  {
    id: 'bug-bounty',
    level: 'tech',
    title: 'Bug bounties',
    what: 'Companies pay for security bugs found in their own programs. Hard at first, but some students earn well.',
    tools: ['HackerOne, Bugcrowd, Intigriti', 'PortSwigger Web Security Academy (free training)'],
    youDo: 'Test only what a program’s rules allow. Testing other sites is illegal.',
    price: 'From $50 to thousands a bug; many weeks earn nothing',
    learn: 'Months',
    where: 'hackerone.com, bugcrowd.com, intigriti.com',
    search: 'bug bounty',
    samples: 'Finish the free PortSwigger labs and write up what you learned.',
    skills: ['cybersecurity', 'ethical hacking', 'penetration testing', 'networking'],
  },
  {
    id: 'open-source',
    level: 'tech',
    title: 'Paid open source and Kaggle',
    what: 'Stipends for open-source work (Google Summer of Code, LFX Mentorship, Outreachy) and prize money on Kaggle competitions.',
    tools: ['GitHub', 'Kaggle notebooks'],
    youDo: 'Start contributing months before applications open.',
    price: 'GSoC and LFX pay stipends in the thousands of dollars per term',
    learn: 'Start 2–3 months early',
    where: 'summerofcode.withgoogle.com, lfx.linuxfoundation.org, outreachy.org, kaggle.com',
    search: 'open source contribution',
    samples: 'Merged pull requests and public notebooks are your portfolio.',
    skills: ['git', 'github', 'python', 'machine learning', 'java', 'c++'],
  },
];

export const PLAN = [
  {
    week: 'Week 1',
    title: 'Pick one thing and make samples',
    days: [
      'Pick ONE service below. Just one: doing three at once is the most common reason people earn nothing.',
      'Watch one free beginner tutorial for its tool (the “Learn it free” link on the card).',
      'Make your first sample, copying a style you like.',
      'Make sample 2, then sample 3. Get a friend to point out what looks wrong and fix it.',
      'Put the 3 samples in one place: a Google Drive folder set to “Anyone with the link”, a free Canva website or Behance.',
    ],
  },
  {
    week: 'Week 2',
    title: 'Show up where clients are',
    days: [
      'Open the Fiverr / Upwork links on your service card and note what 5 beginners charge and how they describe it.',
      'Set your starting price a little below them (see Pricing).',
      'Create ONE platform profile with a clear photo, your real name and your 3 samples. Use the gig template below.',
      'Add a “Services” section to your LinkedIn and post your 3 samples on LinkedIn, Instagram and your WhatsApp status.',
    ],
  },
  {
    week: 'Week 3',
    title: 'Ask for work every day',
    days: [
      'Make a list of 30 local businesses or people who need your service (Google Maps, Instagram, your street).',
      'Message 10 a day with the local message template. Personalise the first line every time.',
      'On the platform, send 3–5 short proposals a day using the proposal template.',
      'Tell family, relatives and college groups what you now do. Your first client is often someone who already knows you.',
      'Follow up once after 3 days. Most replies come after the follow-up.',
    ],
  },
  {
    week: 'Week 4',
    title: 'Deliver, get paid, get a review',
    days: [
      'Before starting, confirm in writing what you will deliver, by when and for how much (template below).',
      'For local clients, ask for 50% in advance by UPI. On platforms, only work after the order or contract starts.',
      'Deliver on time, offer one round of changes, and say thank you.',
      'Ask for a review or a WhatsApp testimonial and a referral to one more person.',
      'After 3 happy clients, raise your price by 20–30%.',
    ],
  },
];

export const PLATFORMS = [
  {
    name: 'Local clients (WhatsApp, Instagram, walk-in)',
    best: 'Your first ₹. No fees, paid by UPI, and trust comes easily from people nearby.',
    fee: 'None',
    beginner: true,
    url: '',
  },
  {
    name: 'Fiverr',
    best: 'Small fixed-price services (“I will design 5 Instagram posts”). Buyers come to you.',
    fee: '20% of each order',
    beginner: true,
    url: 'https://www.fiverr.com',
  },
  {
    name: 'Upwork',
    best: 'Clients post jobs and you send proposals. Bigger and longer projects.',
    fee: '0–15% per contract (shown before you apply); proposals cost “Connects”',
    beginner: false,
    url: 'https://www.upwork.com',
  },
  {
    name: 'Freelancer.com',
    best: 'Many small projects and contests; lots of competition.',
    fee: 'About 10% per project',
    beginner: true,
    url: 'https://www.freelancer.com',
  },
  {
    name: 'Contra',
    best: 'Portfolio-first profiles for designers, writers and developers.',
    fee: 'No commission for freelancers',
    beginner: true,
    url: 'https://contra.com',
  },
  {
    name: 'Truelancer',
    best: 'Indian platform with many Indian clients, paid in rupees.',
    fee: 'A fee per payment; check before starting',
    beginner: true,
    url: 'https://www.truelancer.com',
  },
  {
    name: 'Internshala (work from home)',
    best: 'Paid work-from-home internships in content, design, marketing and development.',
    fee: 'None for students',
    beginner: true,
    url: 'https://internshala.com/internships/work-from-home-internships/',
  },
  {
    name: 'LinkedIn',
    best: 'Turn on the free Services page; startups and recruiters find you there.',
    fee: 'None',
    beginner: true,
    url: 'https://www.linkedin.com',
  },
  {
    name: 'Behance / Dribbble',
    best: 'Show design work; clients message you directly.',
    fee: 'None to show work',
    beginner: false,
    url: 'https://www.behance.net',
  },
];

export const TEMPLATES = [
  {
    id: 'local',
    title: 'Message to a local business',
    text: `Hi {Owner name}, I'm {Your name}, a student from {college/area}. I saw {shop name} on Instagram/Google Maps and really liked {something specific}.

I make {service, e.g. festival and offer posts} for local shops. Here are 3 samples: {link}

I can make {e.g. 4 posts for this week's offer} for ₹{price}. If you don't like them, you don't pay. Can I send you one free sample for your shop?`,
  },
  {
    id: 'local-hinglish',
    title: 'Same message in Hinglish',
    text: `Namaste {Owner name} ji, main {Your name}, {college/area} se student hoon. Maine {shop name} ka Instagram/Google Maps dekha, bahut accha laga.

Main local shops ke liye {service, jaise festival aur offer posts} banata/banati hoon. Mere 3 samples: {link}

Aapke liye {jaise is hafte ke offer ke 4 posts} sirf ₹{price} mein bana sakta/sakti hoon. Pasand na aaye toh paise mat dijiye. Kya main aapki shop ke liye ek free sample bhej doon?`,
  },
  {
    id: 'gig',
    title: 'Fiverr gig / profile description',
    text: `I will {do the service} for your {type of business}, delivered in {2} days.

What you get:
• {e.g. 5 custom Instagram posts in your brand colours}
• {e.g. captions with hashtags}
• {1} round of changes

Why me: I'm a student who answers quickly and checks every detail. See my samples in the gallery.

Send me a message before ordering so I can understand exactly what you need.`,
  },
  {
    id: 'proposal',
    title: 'Upwork / Freelancer proposal',
    text: `Hi {client name},

You need {repeat their exact problem in one line}. I can do this by {date}.

Here's how: {2–3 short steps of how you'll do it}.

Similar work I've done: {link to the closest sample}

One question so I get it right: {a smart question about their job}

Thanks,
{Your name}`,
  },
  {
    id: 'scope',
    title: 'Confirm the work before you start',
    text: `Hi {client}, just confirming before I start:
• Work: {exactly what you'll deliver}
• Delivery: by {date}
• Price: ₹{amount} ({50% now by UPI, 50% on delivery})
• Changes: {1} round included
Reply "OK" and I'll start today.`,
  },
  {
    id: 'follow-up',
    title: 'Follow-up after 3 days',
    text: `Hi {name}, just following up on my message about {service}. I made a quick free sample for {their business}: {link}. Happy to change anything. Should I go ahead?`,
  },
];

export const PRICING = [
  'Start a little below other beginners for your first 3 clients, not free. Free work brings clients who never pay.',
  'Price per piece (₹200 a post), not per hour, while you are slow and learning.',
  'Write down what is included (number of items, rounds of changes, delivery date) so the job can’t keep growing.',
  'Local work: 50% in advance by UPI. Platform work: start only after the order or contract is active.',
  'After 3 good reviews, raise prices by 20–30%. Raise again every few months.',
];

export const AI_RULES = [
  { ok: true, text: 'Use AI for first drafts, ideas, captions, formulas and code, then check and fix everything yourself.' },
  { ok: true, text: 'Tell the client you use AI tools if they ask, and follow their rules.' },
  { ok: true, text: 'Learn the skill while you work: each job should need less AI than the last.' },
  { ok: false, text: 'Don’t hand in AI output you haven’t checked: wrong prices, names or facts lose clients.' },
  { ok: false, text: 'Don’t use AI text where the client or platform says “no AI”.' },
  { ok: false, text: 'Don’t paste a client’s private data (customer lists, recordings, documents) into AI tools without permission.' },
  { ok: false, text: 'Don’t use copyrighted logos, images, music or fonts, and don’t do other students’ graded assignments.' },
];

export const PAYMENTS = [
  { title: 'UPI', text: 'For local and Indian clients. Free and instant. Send a simple bill (Canva has invoice templates).' },
  {
    title: 'Through the platform',
    text: 'Fiverr, Upwork and Freelancer pay to your Indian bank account, Payoneer or PayPal. Withdrawal fees and exchange rates differ, so compare.',
  },
  {
    title: 'Payoneer / PayPal',
    text: 'For foreign clients. Both charge a fee plus a currency conversion margin (often a few percent in total), and both offer a FIRA, the proof of foreign payment you may need for tax. Check current fees on their India pages.',
  },
  {
    title: 'What you need',
    text: 'You must be 18 or older for Fiverr, Upwork and PayPal. You also need a PAN card and a bank account in your own name. Under 18? Work with local clients with a parent’s help.',
  },
];

export const SCAMS = [
  'Anyone asking YOU to pay: a “registration fee”, “training fee”, “security deposit” or “kit”. Real clients pay you.',
  'Telegram or WhatsApp “tasks”: like videos, review hotels or rate products for money, then “invest” to unlock earnings. Always a scam.',
  'Clients who want to move off Fiverr or Upwork before paying, or pay by “cheque” and ask for a refund of the extra.',
  'Asking for your OTP, UPI PIN, bank login or Aadhaar copy “to send payment”. Receiving money never needs a PIN.',
  '“Data entry job, ₹30,000 a month from home, no skills, pay ₹2,000 to start.”',
  'Big work for free as a “test”. A small paid test is fine; a whole project for free is not.',
];

export const TAX = [
  'Freelance income is taxable like any income. Under the new tax regime (FY 2025-26), no tax is due if your total taxable income is up to ₹12 lakh, thanks to the Section 87A rebate.',
  'Many freelancers in professions such as design, writing, IT and engineering can use Section 44ADA, where only 50% of what they receive counts as income. A CA can confirm whether your work qualifies.',
  'Even when you owe no tax, filing an income tax return is a good record of your income (useful for visas, loans and education loans), and you may need it if you received money from abroad.',
  'Keep every invoice, platform statement and FIRA in one folder.',
  'GST registration is needed only when your yearly turnover crosses ₹20 lakh (₹10 lakh in some states).',
];
