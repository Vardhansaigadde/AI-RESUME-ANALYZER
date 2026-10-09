// Resume strength report: a letter grade per section plus the weakest
// bullets, computed in the browser from the editable resume so it updates
// live while editing. Uses the bullet-coach rules for bullet quality.
import { coachBullet } from './bulletCoach';

const POINTS = { A: 4, B: 3, C: 2, D: 1 };
const words = (text) => (text || '').trim().split(/\s+/).filter(Boolean).length;

function gradeEntries(entries, { emptyGrade, emptyNote, minEntries }) {
  if (!entries.length) return { grade: emptyGrade, notes: [emptyNote] };
  const bullets = entries.flatMap((e) => e.bullets || []).filter((b) => b.trim());
  const notes = [];
  if (entries.length < minEntries) notes.push(`Add ${minEntries - entries.length} more to show range.`);
  const withoutBullets = entries.filter((e) => !(e.bullets || []).some((b) => b.trim())).length;
  if (withoutBullets) notes.push(`${withoutBullets} entr${withoutBullets > 1 ? 'ies have' : 'y has'} no bullet points.`);
  if (!bullets.length) return { grade: 'C', notes };
  const good = bullets.filter((b) => coachBullet(b).level !== 'weak').length / bullets.length;
  const numbers = bullets.filter((b) => /\d/.test(b)).length;
  if (numbers === 0) notes.push('No bullet shows a number or result.');
  if (good < 0.5) notes.push('Most bullets need a stronger verb or a result.');
  let grade = good >= 0.8 && numbers > 0 ? 'A' : good >= 0.5 ? 'B' : 'C';
  if (entries.length < minEntries && grade === 'A') grade = 'B';
  return { grade, notes: notes.length ? notes : ['Clear bullets with results.'] };
}

/**
 * @returns {{ grade: string, score: number, sections: {name, grade, notes}[], weakest: {text, where, issues, tip}[] }}
 */
export function resumeStrength(resume, { studentMode = false } = {}) {
  const r = resume || {};
  const sections = [];

  // Contact
  const contactMissing = [];
  if (!r.email) contactMissing.push('email');
  if (!r.phone) contactMissing.push('phone');
  if (!(r.links || []).some((l) => l.trim())) contactMissing.push('LinkedIn / GitHub link');
  sections.push({
    name: 'Contact',
    grade: !r.email ? 'D' : contactMissing.length === 0 ? 'A' : contactMissing.length === 1 ? 'B' : 'C',
    notes: contactMissing.length ? [`Missing: ${contactMissing.join(', ')}.`] : ['Email, phone and a profile link.'],
  });

  // Summary
  const summaryWords = words(r.summary);
  sections.push({
    name: 'Summary',
    grade: summaryWords >= 25 && summaryWords <= 80 ? 'A' : summaryWords >= 10 && summaryWords <= 120 ? 'B' : summaryWords ? 'C' : 'D',
    notes: [
      !summaryWords
        ? 'Add 2–3 lines on who you are, what you are good at and what role you want.'
        : summaryWords < 25
          ? `Only ${summaryWords} words; aim for 25–80.`
          : summaryWords > 80
            ? `${summaryWords} words; keep it under 80.`
            : 'A focused 2–3 line summary.',
    ],
  });

  // Skills
  const skills = (r.skills || []).filter((s) => s.trim()).length;
  sections.push({
    name: 'Skills',
    grade: skills >= 10 ? 'A' : skills >= 6 ? 'B' : skills >= 3 ? 'C' : 'D',
    notes: [skills >= 10 ? `${skills} skills listed.` : `${skills} skills; list 10+ relevant tools and technologies.`],
  });

  // Experience and projects
  const experience = gradeEntries(r.experience || [], {
    emptyGrade: studentMode ? 'B' : 'C',
    emptyNote: studentMode
      ? 'No experience yet; fine for students if projects are strong. Internships or training help.'
      : 'No work experience listed.',
    minEntries: 1,
  });
  sections.push({ name: 'Experience', ...experience });
  const projects = gradeEntries(r.projects || [], {
    emptyGrade: studentMode ? 'D' : 'C',
    emptyNote: 'No projects listed; add 2–4 with the tech you used.',
    minEntries: studentMode ? 2 : 1,
  });
  sections.push({ name: 'Projects', ...projects });

  // Education
  const edu = r.education || [];
  const hasYear = edu.some((e) => /\b(19|20)\d{2}\b/.test(`${e.title} ${e.subtitle} ${e.date || ''}`));
  const hasGrade = edu.some((e) => /\b(c?gpa|cpi|percentage|%|\d\.\d{1,2}\s*\/\s*(10|4))/i.test(`${e.title} ${e.subtitle} ${(e.bullets || []).join(' ')}`));
  const eduNotes = [
    !hasYear && 'Add the years (e.g. 2023 – 2027).',
    studentMode && !hasGrade && 'Add your CGPA if it is good.',
  ].filter(Boolean);
  sections.push({
    name: 'Education',
    grade: !edu.length ? 'D' : hasYear && (hasGrade || !studentMode) ? 'A' : hasYear ? 'B' : 'C',
    notes: !edu.length ? ['Add your degree, college and years.'] : eduNotes.length ? eduNotes : ['Degree, college and dates.'],
  });

  const avg = sections.reduce((sum, s) => sum + POINTS[s.grade], 0) / sections.length;
  const grade = avg >= 3.5 ? 'A' : avg >= 2.75 ? 'B' : avg >= 2 ? 'C' : 'D';

  const weakest = [...(r.experience || []), ...(r.projects || [])]
    .flatMap((e) => (e.bullets || []).map((b) => ({ text: b, where: e.title || 'Untitled entry', ...coachBullet(b) })))
    .filter((b) => b.level === 'weak')
    .sort((a, b) => b.issues.length - a.issues.length)
    .slice(0, 3);

  return { grade, score: Math.round((avg / 4) * 100), sections, weakest };
}
