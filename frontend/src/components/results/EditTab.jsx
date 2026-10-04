import { AnimatePresence, motion } from 'framer-motion';
import { Download, Info, LayoutTemplate, RefreshCw, RotateCcw } from 'lucide-react';
import ResumeForm from '../resume/ResumeForm';
import Button from '../ui/Button';

export default function EditTab({
  draft,
  setDraft,
  missingSkills,
  missingLabel,
  dirty,
  checking,
  downloading,
  onRecheck,
  onDownload,
  onReset,
  onOpenBuilder,
}) {
  return (
    <div className="pb-28">
      <p className="mb-5 flex items-center gap-2 text-sm text-muted">
        <Info className="size-4 shrink-0" aria-hidden />
        We split your resume into sections automatically; check each one, then re-check or download.
      </p>

      <ResumeForm draft={draft} setDraft={setDraft} missingSkills={missingSkills} missingLabel={missingLabel} />

      {/* Sticky action bar */}
      <motion.div
        initial={{ y: 80, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ type: 'spring', stiffness: 260, damping: 24, delay: 0.2 }}
        className="fixed inset-x-0 bottom-20 z-30 flex justify-center px-4 md:bottom-4"
      >
        <div className="flex w-full max-w-2xl flex-wrap items-center gap-2 rounded-2xl border border-line bg-card/95 p-2.5 shadow-[var(--shadow-lift)] backdrop-blur">
          <AnimatePresence>
            {dirty && (
              <motion.span
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0 }}
                className="flex items-center gap-1.5 px-2 text-xs font-semibold text-warn"
              >
                <span className="size-2 animate-pulse rounded-full bg-warn" aria-hidden />
                Not checked yet
              </motion.span>
            )}
          </AnimatePresence>
          <div className="ml-auto flex flex-wrap gap-2">
            <Button variant="ghost" size="md" icon={RotateCcw} onClick={onReset}>
              Reset
            </Button>
            {onOpenBuilder && (
              <Button variant="secondary" size="md" icon={LayoutTemplate} onClick={onOpenBuilder} title="Pick a template, then download as PDF or Word">
                Templates
              </Button>
            )}
            <Button variant="secondary" size="md" icon={Download} loading={downloading} onClick={onDownload}>
              Download .docx
            </Button>
            <Button variant="primary" size="md" icon={RefreshCw} loading={checking} onClick={onRecheck}>
              Re-check score
            </Button>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
