import { contactLink, groupSkills, linkLabel, safeUrl, splitLinks } from '../../lib/richText';
import { DENSITY, FONTS, ORDERS, templateById } from '../../lib/templates';
import { ExternalIcon, GithubIcon, LinkedinIcon, LinkIcon, MailIcon, PhoneIcon, PinIcon } from './ResumeIcons';

const INK = '#1f2328';
const MUTED = '#555b63';
const RULE_GREY = '#b8bec6';

/** The colour mixed with white, as the .docx shaded heading band. */
function tint(hex, amount = 0.88) {
  const value = hex.replace('#', '');
  const channels = [0, 2, 4].map((i) => parseInt(value.slice(i, i + 2), 16));
  return `rgb(${channels.map((c) => Math.round(c + (255 - c) * amount)).join(',')})`;
}

const clean = (items) => (items || []).filter((x) => x && String(x).trim());
// Links look like the text around them on paper (no blue, no underline) but stay clickable in the PDF
const linkStyle = { color: 'inherit', textDecoration: 'none' };

/** The icon for a contact link, chosen from its address. */
function iconForLink(value) {
  const v = String(value || '').toLowerCase();
  if (v.includes('github.com')) return GithubIcon;
  if (v.includes('linkedin.com')) return LinkedinIcon;
  return LinkIcon;
}

/** Text with [label](url) turned into links. */
function RichText({ text }) {
  return splitLinks(text).map((part, i) =>
    part.url ? (
      <a key={i} href={part.url} target="_blank" rel="noreferrer" style={linkStyle}>
        {part.text}
      </a>
    ) : (
      <span key={i}>{part.text}</span>
    ),
  );
}
const hasEntries = (entries) => (entries || []).some((e) => e.title?.trim() || e.subtitle?.trim() || clean(e.bullets).length);

/**
 * A resume drawn in one of the templates, in points, matching the .docx export.
 * It is always "paper": white background and dark ink, in light and dark mode.
 */
export default function ResumeDocument({ resume, templateId, accent, print = false }) {
  const t = templateById(templateId);
  const color = accent || t.accent;
  const density = DENSITY[t.density];
  const h = t.heading;
  const tone = (name) => (name === 'accent' ? color : name === 'muted' ? MUTED : INK);
  // A colour the user picked shows on every template: name, headings and their rules.
  // "Template default" (no accent) keeps each template's own black or grey headings.
  const picked = Boolean(accent);
  const headingColor = picked ? color : tone(h.color);
  const nameColor = picked ? color : tone(t.name_color);
  const pt = (n) => `${n}pt`;

  const ruleColor =
    h.rule_color === 'ink' && !picked
      ? INK
      : picked || h.color === 'accent' || h.rule_color === 'accent'
        ? color
        : h.rule === 'thick'
          ? INK
          : RULE_GREY;
  const headingStyle = {
    fontSize: pt(h.size),
    fontWeight: 700,
    color: headingColor,
    margin: `${pt(density.before)} 0 ${pt(4)}`,
    paddingBottom: h.rule !== 'none' ? pt(1.5) : 0,
    textTransform: h.case === 'upper' ? 'uppercase' : 'none',
    fontVariant: h.case === 'small-caps' ? 'small-caps' : 'normal',
    textDecoration: h.underline ? 'underline' : 'none',
    borderBottom:
      h.rule === 'single'
        ? `0.75pt solid ${ruleColor}`
        : h.rule === 'double'
          ? `2.25pt double ${ruleColor}`
          : h.rule === 'thick'
            ? `2pt solid ${ruleColor}`
            : 'none',
    borderLeft: h.bar ? `3pt solid ${color}` : 'none',
    paddingLeft: h.bar ? pt(6) : h.band ? pt(3) : 0,
    background: h.band ? tint(color) : 'transparent',
    breakAfter: 'avoid',
    letterSpacing: h.case === 'upper' && h.rule === 'none' && !h.band && !h.bar ? '0.06em' : 'normal',
  };

  const Heading = ({ children }) => <h2 style={headingStyle}>{children}</h2>;

  const Bullets = ({ items }) =>
    clean(items).length ? (
      <ul style={{ margin: `${pt(1)} 0 0`, paddingLeft: '1.25em', listStyle: 'disc' }}>
        {clean(items).map((item, i) => (
          <li key={i} style={{ marginBottom: pt(1) }}>
            <RichText text={item} />
          </li>
        ))}
      </ul>
    ) : null;

  const Entries = ({ heading, entries }) =>
    hasEntries(entries) ? (
      <section>
        <Heading>{heading}</Heading>
        {entries
          .filter((e) => e.title?.trim() || e.subtitle?.trim() || clean(e.bullets).length)
          .map((entry, i) => (
            <div key={entry._id || i} style={{ marginTop: i ? pt(5) : pt(2) }}>
              {(entry.title?.trim() || entry.date?.trim() || safeUrl(entry.link)) && (
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: '12pt', breakAfter: 'avoid' }}>
                  <span>
                    <strong>
                      <RichText text={entry.title} />
                    </strong>
                    {safeUrl(entry.link) && (
                      <a
                        href={safeUrl(entry.link)}
                        target="_blank"
                        rel="noreferrer"
                        style={{ ...linkStyle, color: MUTED, fontSize: '0.9em', marginLeft: '0.5em', whiteSpace: 'nowrap' }}
                      >
                        {t.icons && (
                          <>
                            <ExternalIcon />{' '}
                          </>
                        )}
                        {linkLabel(entry.link)}
                      </a>
                    )}
                  </span>
                  {entry.date?.trim() && <span style={{ color: MUTED, whiteSpace: 'nowrap' }}>{entry.date}</span>}
                </div>
              )}
              {entry.subtitle?.trim() && (
                <div style={{ color: MUTED, fontStyle: t.subtitle === 'italic' ? 'italic' : 'normal', marginBottom: pt(1) }}>
                  <RichText text={entry.subtitle} />
                </div>
              )}
              <Bullets items={entry.bullets} />
            </div>
          ))}
      </section>
    ) : null;

  const Lines = ({ heading, items }) =>
    clean(items).length ? (
      <section>
        <Heading>{heading}</Heading>
        <Bullets items={items} />
      </section>
    ) : null;

  const sections = {
    summary: () =>
      resume.summary?.trim() ? (
        <section key="summary">
          <Heading>Summary</Heading>
          <p style={{ margin: 0 }}>
            <RichText text={resume.summary} />
          </p>
        </section>
      ) : null,
    skills: () => {
      const groups = groupSkills(resume.skills);
      if (!groups.length) return null;
      // "Languages: Python, Java" rows when the skills are grouped, one line otherwise
      const labelled = groups.some((g) => g.label);
      return (
        <section key="skills">
          <Heading>Skills</Heading>
          {labelled ? (
            groups.map((g, i) => (
              <div key={i} style={{ marginBottom: pt(1) }}>
                {g.label && <strong>{g.label}: </strong>}
                {g.items.join(', ')}
              </div>
            ))
          ) : (
            <p style={{ margin: 0 }}>{groups[0].items.join(', ')}</p>
          )}
        </section>
      );
    },
    experience: () => <Entries key="experience" heading="Experience" entries={resume.experience} />,
    projects: () => <Entries key="projects" heading="Projects" entries={resume.projects} />,
    education: () => <Entries key="education" heading="Education" entries={resume.education} />,
    certifications: () => <Lines key="certifications" heading="Certifications" items={resume.certifications} />,
    achievements: () => <Lines key="achievements" heading="Achievements" items={resume.achievements} />,
  };

  // Contact details: clickable email, phone and links, with icons in the templates that use them
  const contact = [
    { text: resume.email, url: safeUrl(resume.email), Icon: MailIcon },
    { text: resume.phone, url: resume.phone?.trim() ? `tel:${resume.phone.replace(/[^0-9+]/g, '')}` : null, Icon: PhoneIcon },
    { text: resume.location, url: null, Icon: PinIcon },
    ...(resume.links || []).map((l) => {
      const { text, url, address } = contactLink(l);
      return { text, url, Icon: iconForLink(address) };
    }),
  ].filter((c) => c.text?.trim());
  // Icon templates put the links on their own line, like LaTeX resumes
  const linkCount = (resume.links || []).filter((l) => l?.trim()).length;
  const contactRows =
    t.icons && linkCount && contact.length > linkCount
      ? [contact.slice(0, contact.length - linkCount), contact.slice(contact.length - linkCount)]
      : contact.length
        ? [contact]
        : [];
  const align = t.align === 'center' ? 'center' : 'left';

  return (
    <article
      className="resume-doc"
      style={{
        background: '#fff',
        color: INK,
        fontFamily: FONTS[t.font].css,
        fontSize: pt(t.size),
        lineHeight: t.line_height || 1.3,
        // On screen the page margin is padding; when printing, @page sets it
        padding: print ? 0 : pt(density.margin),
        width: print ? 'auto' : '595.3pt',
        minHeight: print ? 0 : '841.9pt',
        boxSizing: 'border-box',
        textAlign: 'left',
      }}
    >
      {resume.name?.trim() && (
        <h1
          style={{
            fontSize: pt(t.name_size),
            fontWeight: t.name_weight || 700,
            margin: `0 0 ${pt(2)}`,
            lineHeight: 1.1,
            textAlign: align,
            color: nameColor,
            textTransform: t.name_case === 'upper' ? 'uppercase' : 'none',
            letterSpacing: t.name_spacing ? `${t.name_spacing}em` : 'normal',
          }}
        >
          {resume.name}
        </h1>
      )}
      {resume.headline?.trim() && <p style={{ margin: 0, color: MUTED, textAlign: align }}>{resume.headline}</p>}
      {contactRows.map((row, r) => (
        <p key={r} style={{ margin: `${pt(r ? 0 : 2)} 0 0`, fontSize: pt(Math.max(t.size - 1, 9)), textAlign: align }}>
          {row.map(({ text, url, Icon }, i) => (
            // inline-block: an item never splits, but the line can wrap between items
            <span key={i} style={{ display: 'inline-block', whiteSpace: 'nowrap' }}>
              {i > 0 && <span style={{ whiteSpace: 'pre', color: MUTED }}>{t.separator}</span>}
              {t.icons && (
                <>
                  <Icon />{' '}
                </>
              )}
              {url ? (
                <a href={url} target="_blank" rel="noreferrer" style={linkStyle}>
                  {text.trim()}
                </a>
              ) : (
                text.trim()
              )}
            </span>
          ))}
        </p>
      ))}

      {ORDERS[t.order].map((key) => sections[key]())}
      {(resume.additional || [])
        .filter((x) => x.heading?.trim())
        .map((extra, i) => (
          <Lines key={extra._id || `extra-${i}`} heading={extra.heading} items={extra.items} />
        ))}
    </article>
  );
}
