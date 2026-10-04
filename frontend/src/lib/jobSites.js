// One-click searches on the big job sites. We can't read their listings (no
// public API, and scraping breaks their terms), but their search pages take the
// role, city and job type in the URL, so we open them already filled in.

const slug = (text) =>
  text
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '');

// Internshala and Naukri use their own city slugs for a few cities
const CITY_SLUGS = { bengaluru: 'bangalore', gurugram: 'gurgaon', 'new delhi': 'delhi' };
const citySlug = (city) => {
  const key = city.trim().toLowerCase();
  return slug(CITY_SLUGS[key] || key);
};

/**
 * Search links for a role. `kind` is all | internship | entry; `city` is optional
 * ("Remote" means work from home); `country` is the job search's country name.
 */
export function jobSiteLinks({ query, kind = 'all', city = '', country = 'India' }) {
  const role = query.trim();
  const remote = /^(remote|work from home|wfh)$/i.test(city.trim());
  const place = remote ? '' : city.trim();
  const internship = kind === 'internship';
  const q = encodeURIComponent;
  const where = place || country || '';

  const linkedin = new URLSearchParams({ keywords: role, location: remote ? 'India' : where });
  if (internship) linkedin.set('f_E', '1');
  if (kind === 'entry') linkedin.set('f_E', '2');
  if (remote) linkedin.set('f_WT', '2');

  const internshalaPath = internship
    ? remote
      ? `internships/work-from-home-${slug(role)}-internships/`
      : `internships/${slug(role)}-internship${place ? `-in-${citySlug(place)}` : ''}/`
    : `jobs/${slug(role)}-jobs${place ? `-in-${citySlug(place)}` : ''}/`;

  const naukriRole = internship ? `${role} internship` : role;

  return [
    {
      name: 'LinkedIn',
      note: 'Biggest network; easy apply',
      url: `https://www.linkedin.com/jobs/search/?${linkedin}`,
    },
    {
      name: 'Internshala',
      note: 'Internships and fresher jobs in India',
      url: `https://internshala.com/${internshalaPath}`,
    },
    {
      name: 'Unstop',
      note: 'Internships, hackathons and campus contests',
      url: `https://unstop.com/${internship ? 'internships' : 'jobs'}?searchTerm=${q(role)}`,
    },
    {
      name: 'Naukri',
      note: "India's largest job site",
      url: `https://www.naukri.com/${slug(naukriRole)}-jobs${place ? `-in-${citySlug(place)}` : ''}`,
    },
    {
      name: 'Indeed',
      note: 'Listings from company sites',
      url: `https://in.indeed.com/jobs?q=${q(internship ? `${role} internship` : role)}&l=${q(remote ? 'remote' : place)}`,
    },
    {
      name: 'foundit',
      note: 'Formerly Monster India',
      url: `https://www.foundit.in/srp/results?query=${q(role)}${place ? `&locations=${q(place)}` : ''}`,
    },
    {
      name: 'Cutshort',
      note: 'Tech jobs at startups',
      url: `https://cutshort.io/jobs/${slug(role)}-jobs`,
    },
    {
      name: 'Instahyre',
      note: 'Recruiters reach out to you',
      url: `https://www.instahyre.com/search-jobs/?designation=${q(role)}`,
    },
  ];
}
