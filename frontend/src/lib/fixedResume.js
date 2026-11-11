// Rebuild a "Generate a fixed resume" result in the browser as the student keeps or undoes
// changes, so every click is instant. It mirrors app/services/resume_tailor.py: each change
// carries a `patch`, and `skill_catalog` gives every candidate skill's row in display order.

const LABEL = /^\s*([A-Za-z &/+.-]{2,40}):\s*(.*)$/;

/** Skill names from a skills section, without row labels ("Languages: Python, SQL"). */
export function typedSkills(skills = []) {
  const names = [];
  for (const item of skills) {
    const label = LABEL.exec(item);
    const body = label ? label[2] : item;
    for (const raw of body.split(/\s*[,|•;]\s*/)) {
      const name = raw.replace(/^[\s.]+|[\s.]+$/g, '');
      if (name && !names.some((n) => n.toLowerCase() === name.toLowerCase())) names.push(name);
    }
  }
  return names;
}

function groupedRows(catalog, names) {
  const wanted = new Set(names.map((n) => n.toLowerCase()));
  const rows = [];
  let last = null;
  for (const { name, group } of catalog) {
    if (!wanted.has(name.toLowerCase())) continue;
    rows.push(group !== last ? `${group}: ${name}` : name);
    last = group;
  }
  return rows;
}

/** A stable key for "which changes are kept and which skills were confirmed". */
export function selectionKey(kept, confirmed) {
  return JSON.stringify([[...kept].sort(), [...confirmed].sort()]);
}

/** What to send the server for this selection (Word download, re-score). */
export function selectionPayload(data, kept) {
  const skip = [];
  const accept = [];
  for (const change of data.changes) {
    if (change.kind === 'suggestion') {
      if (kept.has(change.id)) accept.push(change.id);
    } else if (!kept.has(change.id) && change.id !== 'skills-confirmed') {
      skip.push(change.id);
    }
  }
  return { skip, accept };
}

/** The original resume with only the kept changes and the confirmed skills applied. */
export function applyChanges(original, data, kept, confirmed) {
  const resume = structuredClone(original);
  const byId = Object.fromEntries(data.changes.map((c) => [c.id, c]));
  const isKept = (id) => byId[id] && kept.has(id);

  if (isKept('dates')) {
    for (const { section, index, date } of byId.dates.patch.entries) resume[section][index].date = date;
  }
  for (const change of data.changes) {
    if (!kept.has(change.id)) continue;
    const p = change.patch;
    if (change.id.startsWith('bullet:')) resume[p.section][p.index].bullets[p.bullet] = p.text;
    if (change.id.startsWith('tech:')) resume[p.section][p.index].subtitle = p.subtitle;
  }
  if (isKept('summary')) resume.summary = byId.summary.patch.summary;
  if (isKept('headline')) resume.headline = byId.headline.patch.headline;

  // Skills: the student's own list, + skills used in projects (if kept), + the ones they confirmed
  const typed = typedSkills(original.skills);
  const names = [...typed];
  const added = [];
  const add = (list) => {
    for (const name of list) {
      if (!names.some((n) => n.toLowerCase() === name.toLowerCase())) {
        names.push(name);
        added.push(name);
      }
    }
  };
  if (isKept('skills-used')) add(byId['skills-used'].patch.add);
  add(confirmed);
  const grouped = groupedRows(data.skill_catalog, names);
  const changed = grouped.map((s) => s.toLowerCase()).join('|') !== (original.skills || []).map((s) => s.toLowerCase()).join('|');
  resume.skills = isKept('skills-group') && changed ? grouped : [...(original.skills || []), ...added];

  if (isKept('projects-order')) resume.projects = byId['projects-order'].patch.order.map((i) => resume.projects[i]);
  return resume;
}
