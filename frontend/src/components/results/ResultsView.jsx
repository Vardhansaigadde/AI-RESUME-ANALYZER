import { AnimatePresence, motion } from 'framer-motion';
import { Briefcase, GraduationCap, LayoutDashboard, Lightbulb, PencilLine, RotateCcw, ScanText } from 'lucide-react';
import { useMemo, useState } from 'react';
import { downloadResumeDocx, fetchRoleGap, recheckResume } from '../../lib/api';
import { snapshot, withIds } from '../../lib/resume';
import Button from '../ui/Button';
import Switch from '../ui/Switch';
import Tabs from '../ui/Tabs';
import AtsTab from './AtsTab';
import EditTab from './EditTab';
import JobsTab from './JobsTab';
import LearnTab from './LearnTab';
import OverviewTab from './OverviewTab';
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
  const [tab, setTab] = useState('overview');
  const [draft, setDraft] = useState(() => withIds(result.resume || {}));
  const [checkedSnapshot, setCheckedSnapshot] = useState(() => snapshot(result.resume || {}));
  const [checking, setChecking] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [roleLoading, setRoleLoading] = useState(false);
  const [addJobOpen, setAddJobOpen] = useState(false);
  const [jobSearch, setJobSearch] = useState({ loading: false, error: null, params: null, data: null });

  const studentMode = Boolean(result.student_mode);
  const targetRole = result.role_gap?.role || null;
  const dirty = snapshot(draft) !== checkedSnapshot;
  const pristine = canReanalyze && result === original && !dirty;
  const issues = useMemo(
    () => (result.ats?.checks || []).filter((c) => c.status === 'fail' || c.status === 'warn').length,
    [result.ats],
  );

  const showTab = (next) => {
    setTab(next);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const recheck = async ({ mode = studentMode, job = jobText, quiet = false } = {}) => {
    setChecking(true);
    try {
      const updated = await recheckResume(draft, job, mode, targetRole);
      setCheckedSnapshot(snapshot(draft));
      onResult(updated);
      if (!quiet) {
        notify({ tone: 'success', message: 'Re-checked. Your scores are updated above.' });
        showTab('overview');
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
    if (await recheck({ job, quiet: true })) {
      setAddJobOpen(false);
      notify({ tone: 'success', message: 'Matched with the job. See your score above.' });
      showTab('overview');
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
    { id: 'overview', label: 'Overview', short: 'Overview', icon: LayoutDashboard },
    { id: 'ats', label: 'ATS check', short: 'ATS', icon: ScanText, badge: issues || null },
    { id: 'edit', label: 'Edit & re-check', short: 'Edit', icon: PencilLine },
    { id: 'learn', label: 'Skill plan', short: 'Learn', icon: Lightbulb, badge: planSize || null },
    { id: 'jobs', label: 'Find jobs', short: 'Jobs', icon: Briefcase },
  ];

  return (
    <motion.main
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -12 }}
      className="mx-auto w-full max-w-6xl px-4 pt-8 sm:px-6 sm:pt-10"
    >
      <div className="mb-6 flex flex-wrap items-center justify-between gap-x-6 gap-y-4">
        <div>
          <h1 className="font-display text-3xl font-bold tracking-tight">Resume report</h1>
          <p className="mt-1 text-sm text-muted">
            {resumeOnly ? 'Resume-only check' : 'Matched against your job'}
            {original !== result && ' · updated after your changes'}
            {result.student_detected && !studentMode && (
              <>
                {' · '}
                <button
                  type="button"
                  onClick={() => changeStudentMode(true)}
                  disabled={checking}
                  className="inline-flex cursor-pointer items-center gap-1 font-semibold text-accent hover:underline"
                >
                  <GraduationCap className="size-4" aria-hidden />
                  Looks like a student resume: use student mode
                </button>
              </>
            )}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="rounded-xl border border-line bg-card px-3 py-2">
            <Switch checked={studentMode} onChange={changeStudentMode} disabled={checking} label="Student mode" />
          </div>
          <Button id="try-another-job-btn" variant="ghost" icon={RotateCcw} onClick={onStartOver}>
            Start over
          </Button>
        </div>
      </div>

      <SummaryCards key={`${result.mode}-${result.match_score}-${result.ats?.score}`} result={result} original={original} draft={draft} />

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
            {tab === 'overview' && (
              <OverviewTab
                result={result}
                draft={draft}
                onEdit={() => showTab('edit')}
                onRoleChange={changeRole}
                roleLoading={roleLoading}
                addJob={{ onSubmit: addJob, loading: checking, open: addJobOpen, setOpen: setAddJobOpen }}
              />
            )}
            {tab === 'ats' && <AtsTab ats={result.ats} onEdit={() => showTab('edit')} />}
            {tab === 'edit' && (
              <EditTab
                draft={draft}
                setDraft={setDraft}
                missingSkills={resumeOnly ? result.role_gap?.missing || [] : result.missing_skills}
                missingLabel={
                  resumeOnly && targetRole
                    ? `Core ${targetRole} skills not in your resume. Only add the ones you really have:`
                    : undefined
                }
                dirty={dirty}
                checking={checking}
                downloading={downloading}
                onRecheck={() => recheck()}
                onDownload={download}
                onReset={resetDraft}
              />
            )}
            {tab === 'learn' && (
              <LearnTab
                plan={result.learning_plan}
                missingCount={resumeOnly ? result.role_gap?.missing.length || 0 : result.missing_skills.length}
                role={resumeOnly ? targetRole : null}
              />
            )}
            {tab === 'jobs' && (
              <JobsTab
                resume={draft}
                defaultQuery={targetRole}
                studentMode={studentMode}
                state={jobSearch}
                setState={setJobSearch}
              />
            )}
          </motion.div>
        </AnimatePresence>
      </div>
    </motion.main>
  );
}
