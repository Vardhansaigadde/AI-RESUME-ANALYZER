import { AnimatePresence, motion } from 'framer-motion';
import { Gauge, PencilLine, RotateCcw, ScanText } from 'lucide-react';
import { useMemo, useState } from 'react';
import { downloadResumeDocx, recheckResume } from '../../lib/api';
import Button from '../ui/Button';
import Tabs from '../ui/Tabs';
import AtsTab from './AtsTab';
import { snapshot, withIds } from '../../lib/resume';
import EditTab from './EditTab';
import MatchTab from './MatchTab';
import SummaryCards from './SummaryCards';

export default function ResultsView({ result, original, jobText, onResult, onStartOver, notify }) {
  const [tab, setTab] = useState('match');
  const [draft, setDraft] = useState(() => withIds(result.resume || {}));
  const [checkedSnapshot, setCheckedSnapshot] = useState(() => snapshot(result.resume || {}));
  const [checking, setChecking] = useState(false);
  const [downloading, setDownloading] = useState(false);

  const dirty = snapshot(draft) !== checkedSnapshot;
  const issues = useMemo(() => (result.ats?.checks || []).filter((c) => c.status === 'fail' || c.status === 'warn').length, [result.ats]);

  const recheck = async () => {
    setChecking(true);
    try {
      const updated = await recheckResume(draft, jobText);
      setCheckedSnapshot(snapshot(draft));
      onResult(updated);
      notify({ tone: 'success', message: 'Re-checked. Your scores are updated above.' });
      setTab('match');
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (err) {
      notify({ tone: 'error', message: err.message });
    } finally {
      setChecking(false);
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

  const tabs = [
    { id: 'match', label: 'Match', short: 'Match', icon: Gauge },
    { id: 'ats', label: 'ATS check', short: 'ATS', icon: ScanText, badge: issues || null },
    { id: 'edit', label: 'Edit & re-check', short: 'Edit', icon: PencilLine },
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
          <p className="text-xs font-semibold tracking-wide text-accent uppercase">{original === result ? 'Your results' : 'Updated after your edits'}</p>
          <h1 className="font-display text-3xl font-bold tracking-tight sm:text-4xl">Resume report</h1>
        </div>
        <Button id="try-another-job-btn" variant="secondary" icon={RotateCcw} onClick={onStartOver}>
          Start over
        </Button>
      </div>

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
                onRecheck={recheck}
                onDownload={download}
                onReset={resetDraft}
              />
            )}
          </motion.div>
        </AnimatePresence>
      </div>
    </motion.main>
  );
}
