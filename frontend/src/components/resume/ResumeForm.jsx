import { AnimatePresence, motion } from 'framer-motion';
import { Plus, Trash2 } from 'lucide-react';
import { weakBulletCount } from '../../lib/bulletCoach';
import { newId } from '../../lib/resume';
import { EntryList, LineList, TagInput, TextField } from '../results/edit/fields';
import Button from '../ui/Button';

function Section({ title, hint, children }) {
  return (
    <motion.section
      initial={{ opacity: 0, y: 12 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-40px' }}
      className="card p-5 sm:p-6"
    >
      <h3 className="font-display text-xl font-semibold">{title}</h3>
      {hint && <p className="mt-1 mb-4 text-sm text-muted">{hint}</p>}
      <div className={hint ? '' : 'mt-4'}>{children}</div>
    </motion.section>
  );
}

/** Every resume section as an editable form (used by the report's Edit tab and the resume builder). */
export default function ResumeForm({ draft, setDraft, missingSkills = [], missingLabel }) {
  const set = (key) => (value) => setDraft((d) => ({ ...d, [key]: value }));
  const weak = weakBulletCount(draft);

  return (
      <div className="space-y-5">
        <Section title="Contact" hint="Recruiters and ATS look for these at the top.">
          <div className="grid gap-4 sm:grid-cols-2">
            <TextField label="Full name" value={draft.name} onChange={set('name')} placeholder="Alex Sample" />
            <TextField label="Headline" value={draft.headline} onChange={set('headline')} placeholder="Computer Science student | Aspiring ML engineer" />
            <TextField label="Email" type="email" value={draft.email} onChange={set('email')} placeholder="you@example.com" />
            <TextField label="Phone" type="tel" value={draft.phone} onChange={set('phone')} placeholder="+91 98765 43210" />
            <TextField label="Location" value={draft.location} onChange={set('location')} placeholder="Hyderabad, India" />
          </div>
          <div className="mt-4">
            <LineList label="Links" items={draft.links} onChange={set('links')} placeholder="linkedin.com/in/you" addLabel="Add link" />
          </div>
        </Section>

        <Section title="Summary" hint="Two or three lines: who you are, what you're good at, what you want.">
          <TextField label="Summary" hideLabel multiline rows={4} value={draft.summary} onChange={set('summary')} />
        </Section>

        <Section title="Skills" hint="Type a skill and press Enter or comma.">
          <TagInput
            label="Skills"
            hideLabel
            tags={draft.skills}
            onChange={set('skills')}
            placeholder="Python, SQL, Docker…"
            suggestions={missingSkills}
            suggestionsLabel={missingLabel || 'In the job but not in your resume. Only add the ones you really have:'}
          />
        </Section>

        {weak > 0 && (
          <p className="rounded-2xl bg-warn-soft px-4 py-3 text-sm">
            <span className="font-semibold">
              {weak} bullet point{weak > 1 ? 's' : ''} need{weak > 1 ? '' : 's'} work.
            </span>{' '}
            The coach under each bullet shows what to change: start with an action verb and add a number.
          </p>
        )}

        <Section title="Experience" hint="Jobs and internships, most recent first.">
          <EntryList
            entries={draft.experience}
            onChange={set('experience')}
            titleLabel="Role & company"
            subtitleLabel="Location or team"
            titlePlaceholder="Software Intern, Acme Corp"
            subtitlePlaceholder="Hyderabad, India · Remote"
            datePlaceholder="May 2025 – Jul 2025"
            addLabel="Add experience"
          />
        </Section>

        <Section title="Projects">
          <EntryList
            entries={draft.projects}
            onChange={set('projects')}
            titleLabel="Project name"
            subtitleLabel="Tech used or link"
            titlePlaceholder="Event Registration Portal"
            subtitlePlaceholder="React, FastAPI · github.com/you/portal"
            datePlaceholder="2025"
            addLabel="Add project"
          />
        </Section>

        <Section title="Education">
          <EntryList
            entries={draft.education}
            onChange={set('education')}
            titleLabel="Degree"
            subtitleLabel="School & grade"
            titlePlaceholder="B.Tech in Computer Science"
            subtitlePlaceholder="State University · CGPA 8.6"
            datePlaceholder="2024 – 2028"
            addLabel="Add education"
          />
        </Section>

        <div className="grid gap-5 lg:grid-cols-2">
          <Section title="Certifications">
            <LineList items={draft.certifications} onChange={set('certifications')} placeholder="Python for Everybody (Coursera)" addLabel="Add certification" />
          </Section>
          <Section title="Achievements">
            <LineList items={draft.achievements} onChange={set('achievements')} placeholder="Top 5% in a national coding contest" addLabel="Add achievement" />
          </Section>
        </div>

        <Section title="Other sections" hint="Languages, interests, volunteering…">
          <ul className="space-y-4">
            <AnimatePresence initial={false}>
              {draft.additional.map((extra) => (
                <motion.li key={extra._id} layout initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0, x: 30 }} className="rounded-2xl border border-line bg-sunken/40 p-4">
                  <div className="flex items-end gap-2">
                    <div className="flex-1">
                      <TextField
                        label="Section heading"
                        value={extra.heading}
                        onChange={(v) => set('additional')(draft.additional.map((x) => (x._id === extra._id ? { ...x, heading: v } : x)))}
                      />
                    </div>
                    <button
                      type="button"
                      onClick={() => set('additional')(draft.additional.filter((x) => x._id !== extra._id))}
                      className="mb-1 cursor-pointer rounded-lg p-2 text-muted hover:bg-pen-soft hover:text-pen"
                      aria-label={`Remove ${extra.heading || 'section'}`}
                    >
                      <Trash2 className="size-4" />
                    </button>
                  </div>
                  <div className="mt-3">
                    <LineList
                      items={extra.items}
                      addLabel="Add line"
                      onChange={(items) => set('additional')(draft.additional.map((x) => (x._id === extra._id ? { ...x, items } : x)))}
                    />
                  </div>
                </motion.li>
              ))}
            </AnimatePresence>
          </ul>
          <Button
            variant="secondary"
            size="sm"
            icon={Plus}
            className="mt-3"
            onClick={() => set('additional')([...draft.additional, { _id: newId(), heading: 'Languages', items: [''] }])}
          >
            Add section
          </Button>
        </Section>
      </div>
  );
}
