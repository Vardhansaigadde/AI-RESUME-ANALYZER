import { AnimatePresence, motion } from 'framer-motion';
import { Gauge, GraduationCap, Lightbulb, PencilLine, RotateCcw, ScanText, UserRound, X } from 'lucide-react';
import { useMemo, useState } from 'react';
import { downloadResumeDocx, fetchRoleGap, recheckResume } from '../../lib/api';
import { snapshot, withIds } from '../../lib/resume';
import Button from '../ui/Button';
import Switch from '../ui/Switch';
import Tabs from '../ui/Tabs';
import AddJobCard from './AddJobCard';
import AtsTab from './AtsTab';
import EditTab from './EditTab';
import LearnTab from './LearnTab';
import MatchTab, { Roles, Suggestions } from './MatchTab';
import ProfileTab from './ProfileTab';
import SummaryCards from './SummaryCards';

export default function ResultsView({
  result,
  original,
  jobText,
  onResult,
  onStartOver,
  notify,
  canReanalyze,
  onReanalyze,
  onJobText,
}) {
  const resumeOnly = result.mode === 'resume_only';
  const [tab, setTab] = useState(resumeOnly ? 'profile' : 'match');
  const [draft, setDraft] = useState(() => withIds(result.resume || {}));
  const [checkedSnapshot, setCheckedSnapshot] = useState(() => snapshot(result.resume || {}));
  const [checking, setChecking] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [roleLoading, setRoleLoading] = useState(false);
  const [hideStudentHint, setHideStudentHint] = useState(false);

  const studentMode = Boolean(result.student_mode);
  const targetRole = result.role_gap?.role || null;
  const dirty = snapshot(draft) !== checkedSnapshot;
  const pristine = canReanalyze && result === original && !dirty;
  const issues = useMemo(
    () => (result.ats?.checks || []).filter((c) => c.status === 'fail' || c.status === 'warn').length,
    [result.ats],
  );

  const recheck = async ({ mode = studentMode, job = jobText, quiet = false } = {}) => {
    setChecking(true);
    try {
      const updated = await recheckResume(draft, job, mode, targetRole);
      setCheckedSnapshot(snapshot(draft));
      onResult(updated);
      if (!quiet) {
        notify({ tone: 'success', message: 'Re-checked. Your scores are updated above.' });
        setTab(updated.mode === 'resume_only' ? 'profile' : 'match');
        window.scrollTo({ top: 0, behavior: 'smooth' });
      }
      return updated;
    } catch (err) {
      notify({ tone: 'error', message: err.message });
      return null;
    } finally {
      setChecking(false);
    }
  };

  // While nothing was edited, re-run on the original file (keeps the file's
  // layout checks); otherwise analyze the edited version.
  const changeStudentMode = (mode) => {
    if (pristine) onReanalyze({ studentMode: mode });
    else recheck({ mode, quiet: true });
  };

  const addJob = async (job) => {
    onJobText(job);
    if (pristine) {
      onReanalyze({ job });
      return;
    }
    const updated = await recheck({ job, quiet: true });
    if (updated) {
      setTab('match');
      notify({ tone: 'success', message: 'Matched with the job. See your score above.' });
    }
  };

  const changeRole = async (role) => {
    setRoleLoading(true);
    try {
      const { role_gap: roleGap, learning_plan: plan } = await fetchRoleGap(draft, role);
      // Without a job, the learning plan follows the target role
      onResult({ ...result, role_gap: roleGap, learning_plan: resumeOnly ? plan : result.learning_plan });
    } catch (err) {
      notify({ tone: 'error', message: err.message });
    } finally {
      setRoleLoading(false);
    }
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
    ...(resumeOnly ? [] : [{ id: 'match', label: 'Match', short: 'Match', icon: Gauge }]),
    { id: 'profile', label: 'Profile', short: 'Profile', icon: UserRound },
    { id: 'ats', label: 'ATS check', short: 'ATS', icon: ScanText, badge: issues || null },
    { id: 'edit', label: 'Edit & re-check', short: 'Edit', icon: PencilLine },
    { id: 'learn', label: 'Skill plan', short: 'Learn', icon: Lightbulb, badge: planSize || null },
  ];
  const activeTab = tabs.some((t) => t.id === tab) ? tab : tabs[0].id;

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
            {original === result ? (resumeOnly ? 'Resume-only check' : 'Your results') : 'Updated after your changes'}
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
          <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }} className="overflow-hidden">
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
              <button type="button" onClick={() => setHideStudentHint(true)} className="cursor-pointer rounded-lg p-1 text-muted hover:text-ink" aria-label="Dismiss">
                <X className="size-4" />
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <SummaryCards
        key={`${result.mode}-${result.match_score}-${result.ats?.score}`}
        result={result}
        original={original}
        draft={draft}
        onAddJob={() => {
          setTab('profile');
          setTimeout(() => document.getElementById('add-job')?.scrollIntoView({ behavior: 'smooth', block: 'center' }), 250);
        }}
      />

      <div className="sticky top-16 z-20 -mx-1 mt-6 bg-paper/85 px-1 py-2 backdrop-blur-md">
        <Tabs tabs={tabs} active={activeTab} onChange={setTab} idPrefix="results" />
      </div>

      <div className="mt-4">
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            role="tabpanel"
            id={`results-panel-${activeTab}`}
            aria-labelledby={`results-${activeTab}`}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            transition={{ duration: 0.2 }}
          >
            {activeTab === 'match' && <MatchTab result={result} />}
            {activeTab === 'profile' && (
              <ProfileTab result={result} draft={draft} onRoleChange={changeRole} roleLoading={roleLoading} onEdit={() => setTab('edit')}>
                {resumeOnly && (
                  <div id="add-job" className="lg:col-span-2">
                    <AddJobCard onSubmit={addJob} loading={checking} />
                  </div>
                )}
              </ProfileTab>
            )}
            {activeTab === 'profile' && resumeOnly && (
              <motion.div initial="hidden" animate="show" variants={{ show: { transition: { staggerChildren: 0.07 } } }} className="mt-5 grid gap-5 lg:grid-cols-2">
                <Suggestions suggestions={result.suggestions} />
                <Roles roles={result.suggested_roles} confidence={result.confidence} />
              </motion.div>
            )}
            {activeTab === 'ats' && <AtsTab ats={result.ats} onEdit={() => setTab('edit')} />}
            {activeTab === 'edit' && (
              <EditTab
                draft={draft}
                setDraft={setDraft}
                missingSkills={resumeOnly ? result.role_gap?.missing || [] : result.missing_skills}
                missingLabel={resumeOnly && targetRole ? `Core ${targetRole} skills not in your resume. Only add the ones you really have:` : undefined}
                dirty={dirty}
                checking={checking}
                downloading={downloading}
                onRecheck={() => recheck()}
                onDownload={download}
                onReset={resetDraft}
              />
            )}
            {activeTab === 'learn' && (
              <LearnTab plan={result.learning_plan} missingCount={resumeOnly ? result.role_gap?.missing.length || 0 : result.missing_skills.length} role={resumeOnly ? targetRole : null} />
            )}
          </motion.div>
        </AnimatePresence>
      </div>
    </motion.main>
  );
}
