// Bullet coach: instant, rule-based feedback on one resume bullet point.
// Runs in the browser so it can update on every keystroke.
// The verb list mirrors ACTION_VERBS in app/services/ats_checker.py.

const ACTION_VERBS = new Set(
  `accelerated achieved administered analyzed architected assembled assessed audited automated balanced boosted built
  calculated championed coached collaborated completed conducted configured consolidated constructed consulted
  contributed coordinated created cut debugged decreased defined delivered deployed designed developed devised
  diagnosed directed drafted drove earned eliminated enabled engineered enhanced established evaluated executed
  expanded facilitated forecasted formulated founded generated grew guided handled headed identified implemented
  improved increased initiated innovated installed instructed integrated introduced investigated launched led
  maintained managed maximized mentored migrated minimized modeled modernized monitored negotiated optimized
  orchestrated organized oversaw participated performed pioneered planned prepared presented prioritized processed
  produced programmed proposed prototyped published raised redesigned reduced refactored resolved restructured
  revamped reviewed saved scaled secured simplified solved spearheaded standardized streamlined strengthened
  supervised supported surpassed taught tested trained transformed troubleshot upgraded utilized validated wrote`.split(/\s+/),
);

// Openers that describe duties instead of achievements
const WEAK_OPENERS = [
  'responsible for',
  'worked on',
  'working on',
  'helped',
  'helping',
  'assisted',
  'assisting',
  'involved in',
  'participated in',
  'tasked with',
  'duties included',
  'in charge of',
  'did',
  'made',
  'was',
  'were',
];

const SUGGESTED_VERBS = ['Built', 'Developed', 'Designed', 'Led', 'Improved', 'Automated', 'Reduced', 'Increased'];

/**
 * Analyze one bullet.
 * @returns {{ level: 'empty'|'strong'|'ok'|'weak', good: string[], issues: string[], tip: string }}
 */
export function coachBullet(raw) {
  const text = (raw || '').trim();
  if (!text) return { level: 'empty', good: [], issues: [], tip: '' };

  const lower = text.toLowerCase();
  const words = text.split(/\s+/);
  const first = words[0].toLowerCase().replace(/[^a-z]/g, '');
  const good = [];
  const issues = [];

  const weakOpener = WEAK_OPENERS.find((w) => lower.startsWith(w));
  if (ACTION_VERBS.has(first)) good.push('Strong verb');
  else if (weakOpener) issues.push(`Weak start ("${weakOpener.trim()}")`);
  else issues.push('Start with an action verb');

  if (/\d/.test(text)) good.push('Has a number');
  else issues.push('No measurable result');

  if (/\b(?:was|were|been|being)\s+\w+ed\b/i.test(text)) issues.push('Passive voice');
  if (/(^|\s)(?:i|my|me)\s/i.test(` ${lower} `)) issues.push('Drop "I" and "my"');
  if (words.length > 30) issues.push(`Too long (${words.length} words)`);
  else if (words.length < 5) issues.push('Too short to show impact');

  let tip = '';
  if (issues.some((i) => i.startsWith('Weak start') || i.startsWith('Start with'))) {
    tip = `Lead with what you did: ${SUGGESTED_VERBS.slice(0, 5).join(', ')}…`;
  } else if (issues.includes('No measurable result')) {
    tip = 'Add a number: users, %, time saved, team size, accuracy, rank.';
  } else if (issues.some((i) => i.startsWith('Too long'))) {
    tip = 'Keep it to one line: action + what + result.';
  }

  const level = issues.length === 0 ? 'strong' : issues.length === 1 && good.length > 0 ? 'ok' : 'weak';
  return { level, good, issues, tip };
}

/** Count weak bullets across experience and project entries. */
export function weakBulletCount(resume) {
  const bullets = [...(resume.experience || []), ...(resume.projects || [])].flatMap((e) => e.bullets || []);
  return bullets.filter((b) => coachBullet(b).level === 'weak').length;
}
