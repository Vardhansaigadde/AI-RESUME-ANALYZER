import { AnimatePresence, motion } from 'framer-motion';
import { GraduationCap, Gauge, Lightbulb, PencilLine, RotateCcw, ScanText, X } from 'lucide-react';
import { useMemo, useState } from 'react';
import { downloadResumeDocx, recheckResume } from '../../lib/api';
import { snapshot, withIds } from '../../lib/resume';
import Button from '../ui/Button';
import Switch from '../ui/Switch';
import Tabs from '../ui/Tabs';
import AtsTab from './AtsTab';
import EditTab from './EditTab';
import LearnTab from './LearnTab';
import MatchTab from './MatchTab';
import SummaryCards from './SummaryCards';

export default function ResultsView({ result, original, jobText, onResult, onStartOver, notify, canReanalyze, onReanalyze }) {
  const [tab, setTab] = useState('match');
  const [draft, setDraft] = useState(() => withIds(result.resume || {}));
  const [checkedSnapshot, setCheckedSnapshot] = useState(() => snapshot(result.resume || {}));
  const [checking, setChecking] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [hideStudentHint, setHideStudentHint] = useState(false);

  const studentMode = Boolean(result.student_mode);
  const dirty = snapshot(draft) !== checkedSnapshot;
  const issues = useMemo(
    () => (result.ats?.checks || []).filter((c) => c.status === 'fail' || c.status === 'warn').length,
    [result.ats],
  );

  const recheck = async (mode = studentMode, { quiet = false } = {}) => {
    setChecking(true);
    try {
      const updated = await recheckResume(draft, jobText, mode);
      setCheckedSnapshot(snapshot(draft));
      onResult(updated);
      if (!quiet) {
        notify({ tone: 'success', message: 'Re-checked. Your scores are updated above.' });
        setTab('match');
        window.scrollTo({ top: 0, behavior: 'smooth' });
      }
    } catch (err) {
      notify({ tone: 'error', message: err.message });
    } finally {
      setChecking(false);
    }
  };

  // Re-run on the original file while nothing was edited (keeps the file's
  // layout checks); otherwise re-check the edited version.
  const changeStudentMode = (mode) => {
    if (canReanalyze && result === original && !dirty) onReanalyze(mode);
    else recheck(mode, { quiet: true });
  };

  const download = async () => {
    setDownloading(true);
    try {
      await downloadResumeDocx(draft);
      notify({ tone: 'success', message: 'Downloaded an ATS-friendly .docx of your resume.' });
    } catch (err) {
      notify({ tone: 'error', message: err.message });
    } finally {
      setDownloading(false);
    }
  };

  const resetDraft = () => {
    setDraft(withIds(original.resume || {}));
    notify({ tone: 'success', message: 'Editor reset to your original resume.' });
  };

  const planSize = result.learning_plan?.length || 0;
  const tabs = [
    { id: 'match', label: 'Match', short: 'Match', icon: Gauge },
    { id: 'ats', label: 'ATS check', short: 'ATS', icon: ScanText, badge: issues || null },
    { id: 'edit', label: 'Edit & re-check', short: 'Edit', icon: PencilLine },
    { id: 'learn', label: 'Skill plan', short: 'Learn', icon: Lightbulb, badge: planSize || null },
  ];

  return (
    <motion.main
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -12 }}
      className="mx-auto w-full max-w-6xl px-4 pt-8 sm:px-6 sm:pt-10"
    >
      <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-xs font-semibold tracking-wide text-accent uppercase">
            {original === result ? 'Your results' : 'Updated after your changes'}
          </p>
          <h1 className="font-display text-3xl font-bold tracking-tight sm:text-4xl">Resume report</h1>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <div className="card px-4 py-2.5">
            <Switch checked={studentMode} onChange={changeStudentMode} disabled={checking} label="Student mode" />
          </div>
          <Button id="try-another-job-btn" variant="secondary" icon={RotateCcw} onClick={onStartOver}>
            Start over
          </Button>
        </div>
      </div>

      <AnimatePresence>
        {result.student_detected && !studentMode && !hideStudentHint && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden"
          >
            <div className="mb-5 flex flex-wrap items-center gap-3 rounded-2xl border border-accent/30 bg-accent-soft/60 px-4 py-3">
              <motion.span animate={{ rotate: [0, -12, 12, 0] }} transition={{ duration: 0.8, delay: 0.4 }}>
                <GraduationCap className="size-6 text-accent" aria-hidden />
              </motion.span>
              <p className="flex-1 text-sm">
                <span className="font-semibold">This looks like a student or fresher resume.</span> Turn on student mode
                for a checklist that fits it (projects, internships, CGPA, GitHub, one page).
              </p>
              <Button size="sm" variant="accent" loading={checking} onClick={() => changeStudentMode(true)}>
                Turn on
              </Button>
              <button
                type="button"
                onClick={() => setHideStudentHint(true)}
                className="cursor-pointer rounded-lg p-1 text-muted hover:text-ink"
                aria-label="Dismiss"
              >
                <X className="size-4" />
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <SummaryCards key={`${result.match_score}-${result.ats?.score}`} result={result} original={original} />

      <div className="sticky top-16 z-20 -mx-1 mt-6 bg-paper/85 px-1 py-2 backdrop-blur-md">
        <Tabs tabs={tabs} active={tab} onChange={setTab} idPrefix="results" />
      </div>

      <div className="mt-4">
        <AnimatePresence mode="wait">
          <motion.div
            key={tab}
            role="tabpanel"
            id={`results-panel-${tab}`}
            aria-labelledby={`results-${tab}`}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            transition={{ duration: 0.2 }}
          >
            {tab === 'match' && <MatchTab result={result} />}
            {tab === 'ats' && <AtsTab ats={result.ats} onEdit={() => setTab('edit')} />}
            {tab === 'edit' && (
              <EditTab
                draft={draft}
                setDraft={setDraft}
                missingSkills={result.missing_skills}
                dirty={dirty}
                checking={checking}
                downloading={downloading}
                onRecheck={() => recheck()}
                onDownload={download}
                onReset={resetDraft}
              />
            )}
            {tab === 'learn' && <LearnTab plan={result.learning_plan} missingCount={result.missing_skills.length} />}
          </motion.div>
        </AnimatePresence>
      </div>
    </motion.main>
  );
}
