import { motion } from 'framer-motion';
import { ArrowRight, ScanSearch } from 'lucide-react';
import { useState } from 'react';
import JobsTab from '../results/JobsTab';

const KINDS = ['all', 'internship', 'entry', 'hackathon'];

/** Find jobs & internships: live openings plus prefilled searches on the big job sites. */
export default function JobsPage({ resume, onNavigate }) {
  const params = new URLSearchParams(window.location.search);
  const kind = KINDS.includes(params.get('kind')) ? params.get('kind') : 'all';
  const [state, setState] = useState({ loading: false, error: null, params: null, data: null });
  const scored = Boolean(resume);

  return (
    <motion.main
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
      className="mx-auto w-full max-w-6xl px-4 pt-8 sm:px-6 sm:pt-10"
    >
      <h1 className="font-display text-4xl font-bold tracking-tight">Find jobs, internships & hackathons</h1>
      <p className="mt-2 max-w-2xl text-lg text-muted">
        Live openings with what employers ask for, one-click searches on LinkedIn, Internshala, Unstop, Naukri and more,
        and open hackathons on Unstop, Devfolio, Devpost and MLH.
      </p>

      {scored ? (
        <p className="mt-4 text-sm text-muted">
          Each opening is scored against your resume{resume.name ? ` (${resume.name})` : ''}.
        </p>
      ) : (
        <a
          href="/check"
          onClick={(e) => {
            e.preventDefault();
            onNavigate('/check');
          }}
          className="mt-5 flex items-center gap-3 rounded-2xl border border-dashed border-accent/50 bg-accent-soft/40 px-4 py-3 text-sm transition hover:bg-accent-soft"
        >
          <ScanSearch className="size-5 shrink-0 text-accent" aria-hidden />
          <span className="flex-1">
            <span className="font-semibold">See your fit score on every job.</span> Check your resume first; we'll score each
            opening against it.
          </span>
          <ArrowRight className="size-4 text-accent" aria-hidden />
        </a>
      )}

      <div className="mt-6">
        <JobsTab
          resume={resume}
          defaultQuery={params.get('q') || 'Software Engineer'}
          defaultKind={kind}
          state={state}
          setState={setState}
        />
      </div>
    </motion.main>
  );
}
