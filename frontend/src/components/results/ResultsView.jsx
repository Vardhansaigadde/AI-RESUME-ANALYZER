import { AnimatePresence, motion } from 'framer-motion';
import { ArrowRight, Briefcase, GraduationCap, LayoutDashboard, Lightbulb, PencilLine, RotateCcw, ScanText, Wand2 } from 'lucide-react';
import { useMemo, useState } from 'react';
import { downloadResumeDocx, fetchRoleGap, recheckResume } from '../../lib/api';
import { snapshot, withIds } from '../../lib/resume';
import { formatSkill } from '../../utils/format';
import Button from '../ui/Button';
import Switch from '../ui/Switch';
import Tabs from '../ui/Tabs';
import AtsTab from './AtsTab';
import EditTab from './EditTab';
import FixedResume from './FixedResume';
import JobsTab from './JobsTab';
import LearnTab from './LearnTab';
import OverviewTab from './OverviewTab';
import SummaryCards from './SummaryCards';
import { HelpfulPrompt } from '../ui/Feedback';

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
  onOpenBuilder,
  file,
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
  const [githubCheck, setGithubCheck] = useState({ loading: false, error: null, data: null, username: '' });
  const [fixing, setFixing] = useState(false);

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
      const { role_gap: roleGap, learning_plan: plan, project_picks: picks } = await fetchRoleGap(draft, role);
      // Without a job, the learning plan and project picks follow the target role
      onResult(
        resumeOnly
          ? { ...result, role_gap: roleGap, learning_plan: plan, project_picks: picks }
          : { ...result, role_gap: roleGap },
      );
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

  const addSkills = (skills) => {
    setDraft((d) => {
      const have = new Set((d.skills || []).map((s) => s.toLowerCase()));
      return { ...d, skills: [...(d.skills || []), ...skills.map(formatSkill).filter((s) => !have.has(s.toLowerCase()))] };
    });
    notify({
      tone: 'success',
      message: `Added ${skills.map(formatSkill).join(', ')} to your Skills. Re-check in the Edit tab to update your scores.`,
    });
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

      {fixing ? (
        <div className="mt-6">
          <FixedResume
            resume={JSON.parse(snapshot(draft))}
            jobText={resumeOnly ? '' : jobText}
            defaultRole={targetRole}
            roles={result.role_gap?.available_roles || []}
            file={pristine ? file : null}
            notify={notify}
            onBack={() => {
              setFixing(false);
              window.scrollTo({ top: 0, behavior: 'smooth' });
            }}
            onOpenBuilder={onOpenBuilder}
          />
        </div>
      ) : (
        <>
          <button
            type="button"
            onClick={() => {
              setFixing(true);
              window.scrollTo({ top: 0, behavior: 'smooth' });
            }}
            className="group mt-5 flex w-full cursor-pointer items-center gap-3 rounded-2xl border border-accent/40 bg-accent-soft/50 px-4 py-3 text-left transition hover:bg-accent-soft"
          >
            <Wand2 className="size-5 shrink-0 text-accent" aria-hidden />
            <span className="flex-1 text-sm">
              <span className="font-semibold">Generate a fixed resume{resumeOnly ? '' : ' for this job'}.</span>{' '}
              <span className="text-muted">
                We fix the issues in this report and show every change so you can keep or undo it.
              </span>
            </span>
            <ArrowRight className="size-4 text-accent transition group-hover:translate-x-0.5" aria-hidden />
          </button>

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
                    github={{ state: githubCheck, setState: setGithubCheck, onAddSkills: addSkills }}
                    onAddSkills={addSkills}
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
                    onOpenBuilder={onOpenBuilder ? () => onOpenBuilder(JSON.parse(snapshot(draft))) : undefined}
                  />
                )}
                {tab === 'learn' && (
                  <LearnTab
                    plan={result.learning_plan}
                    projects={result.project_picks || []}
                    missingCount={resumeOnly ? result.role_gap?.missing.length || 0 : result.missing_skills.length}
                    role={resumeOnly ? targetRole : null}
                    roleRoadmap={result.role_gap?.roadmap}
                    roadmapRole={targetRole}
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
        </>
      )}
      <HelpfulPrompt page="results" question="Was this report helpful?" />
    </motion.main>
  );
}
