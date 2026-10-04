// Helpers for the editable resume draft and score colours.

let nextId = 0;
/** Stable client-side ids for list items (the API ignores unknown fields). */
export const newId = () => `i${++nextId}`;

/** Add client-side ids to list entries so they animate and reorder cleanly. */
export function withIds(resume) {
  const tag = (items) => (items || []).map((item) => ({ ...item, _id: newId() }));
  return {
    ...resume,
    experience: tag(resume.experience),
    projects: tag(resume.projects),
    education: tag(resume.education),
    additional: tag(resume.additional),
  };
}

/** Serialize a draft for change detection, ignoring the client-only ids. */
export const snapshot = (resume) => JSON.stringify(resume, (key, value) => (key === '_id' ? undefined : value));

/** Colour tokens for a 0-100 score. */
export function scoreTone(score) {
  if (score >= 75) return { text: 'text-ok', bg: 'bg-ok-soft', stroke: 'var(--color-ok)' };
  if (score >= 50) return { text: 'text-warn', bg: 'bg-warn-soft', stroke: 'var(--color-warn)' };
  return { text: 'text-pen', bg: 'bg-pen-soft', stroke: 'var(--color-pen)' };
}

/** The GitHub username from a resume link such as github.com/asha-dev, if any. */
export function githubFromLinks(links = []) {
  for (const link of links) {
    const match = /github\.com\/([A-Za-z0-9-]{1,39})(?:[/?#]|$)/i.exec(link);
    if (match) return match[1];
  }
  return '';
}
