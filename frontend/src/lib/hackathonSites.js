// Where to find open hackathons. These platforms don't offer a public API, and
// their terms forbid scraping (Devpost's does explicitly), so we can't list
// their events here. Instead we open each platform's own live listing, with the
// topic and online/in-person filter already applied where the site supports it.

/** MLH seasons run July to June and are named after the year they end in. */
export function mlhSeason(today = new Date()) {
  return today.getMonth() >= 6 ? today.getFullYear() + 1 : today.getFullYear();
}

/**
 * Links to live hackathon listings. `topic` is optional (e.g. "AI", "web3");
 * `mode` is any | online | in-person; `city` narrows the web search when in person.
 */
export function hackathonSiteLinks({ topic = '', mode = 'any', city = '', today = new Date() } = {}) {
  const term = topic.trim();
  const q = encodeURIComponent;

  const devpost = new URLSearchParams();
  if (term) devpost.set('search', term);
  devpost.append('status[]', 'upcoming');
  devpost.append('status[]', 'open');
  if (mode === 'online') devpost.append('challenge_type[]', 'online');
  if (mode === 'in-person') devpost.append('challenge_type[]', 'in-person');

  const where = mode === 'online' ? 'online' : mode === 'in-person' ? city.trim() || 'India' : 'India';
  const webSearch = `${term ? `${term} ` : ''}hackathon ${where} ${today.getFullYear()} registration open`;

  return [
    {
      name: 'Unstop',
      note: 'Most college and company hackathons in India',
      url: `https://unstop.com/hackathons${term ? `?searchTerm=${q(term)}` : ''}`,
    },
    {
      name: 'Devfolio',
      note: 'Student-run hackathons across India',
      url: 'https://devfolio.co/hackathons',
    },
    {
      name: 'Devpost',
      note: 'Global, many online with prizes',
      url: `https://devpost.com/hackathons?${devpost}`,
    },
    {
      name: 'MLH',
      note: 'Major League Hacking official events',
      url: `https://www.mlh.com/seasons/${mlhSeason(today)}/events`,
    },
    {
      name: 'HackerEarth',
      note: 'Company-sponsored hackathons',
      url: 'https://www.hackerearth.com/challenges/hackathon/',
    },
    {
      name: 'Hack2skill',
      note: 'Government and big-tech hackathons',
      url: 'https://hack2skill.com/',
    },
    {
      name: 'Kaggle',
      note: 'Data science and ML competitions',
      url: `https://www.kaggle.com/competitions${term ? `?search=${q(term)}` : ''}`,
    },
    {
      name: 'Smart India Hackathon',
      note: 'National, through your college',
      url: 'https://sih.gov.in/',
    },
    {
      name: 'Web search',
      note: mode === 'in-person' ? `Events near ${where}` : 'Anything the sites above missed',
      url: `https://www.google.com/search?q=${q(webSearch)}`,
    },
  ];
}
