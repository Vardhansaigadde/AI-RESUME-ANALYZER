import { motion } from 'framer-motion';
import {
  Cloud,
  CloudOff,
  Download,
  FilePlus2,
  FileText,
  FileUp,
  FolderOpen,
  LayoutTemplate,
  LoaderCircle,
  Palette,
  RotateCcw,
  ScanSearch,
  Sparkles,
} from 'lucide-react';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { downloadResumeDocx, parseResumeFile } from '../../lib/api';
import { useAuth } from '../../lib/authContext';
import { loadResume, saveResume } from '../../lib/cloud';
import { snapshot, withIds } from '../../lib/resume';
import { KEYS, readStorage, writeStorage } from '../../lib/storage';
import { DEFAULT_TEMPLATE, EMPTY_RESUME, loadTemplateFonts, SAMPLE_RESUME, templateById, TEMPLATES } from '../../lib/templates';
import PrintResume from '../resume/PrintResume';
import ResumeForm from '../resume/ResumeForm';
import ResumeLibrary from '../resume/ResumeLibrary';
import ScaledPage from '../resume/ScaledPage';
import TemplateGallery from '../resume/TemplateGallery';
import Button from '../ui/Button';

const ACCENTS = ['#1d4ed8', '#047857', '#0f766e', '#9f1239', '#7c3aed', '#c2410c', '#111827'];
const plain = (resume) => JSON.parse(snapshot(resume));
const hasContent = (r) =>
  Boolean(r && (r.name?.trim() || r.summary?.trim() || r.experience?.length || r.projects?.length || r.education?.length));

function StartChoice({ icon: Icon, title, text, onClick, busy, children }) {
  return (
    <motion.button
      type="button"
      onClick={onClick}
      whileHover={{ y: -4 }}
      disabled={busy}
      className="card flex cursor-pointer flex-col items-start p-6 text-left hover:border-ink/30 disabled:cursor-wait"
    >
      <span className="grid size-11 place-items-center rounded-2xl bg-accent-soft text-accent">
        {busy ? <LoaderCircle className="size-5 animate-spin" aria-hidden /> : <Icon className="size-5" aria-hidden />}
      </span>
      <span className="mt-4 font-display text-xl font-semibold">{title}</span>
      <span className="mt-1 text-sm text-muted">{text}</span>
      {children}
    </motion.button>
  );
}

/** Resume builder: pick an ATS-friendly template, edit with a live preview, download. */
export default function BuilderPage({ notify, onCheck, seed, onSeedUsed }) {
  const saved = useMemo(() => readStorage(KEYS.builder), []);
  const params = new URLSearchParams(window.location.search);
  const [resume, setResume] = useState(() => {
    if (seed) return withIds(seed);
    // /build?start=sample opens the sample right away (dashboard quick start)
    if (params.get('start') === 'sample') return withIds(SAMPLE_RESUME);
    return saved?.resume ? withIds(saved.resume) : null;
  });
  const [template, setTemplate] = useState(() => {
    const fromUrl = params.get('template');
    return TEMPLATES.some((t) => t.id === fromUrl) ? fromUrl : saved?.template || DEFAULT_TEMPLATE;
  });
  const [accent, setAccent] = useState(() => saved?.accent || null);
  // Signed in: the draft is also saved to the account (resumes table)
  const fresh = Boolean(seed) || params.get('start') === 'sample';
  const [cloudId, setCloudId] = useState(() => (fresh ? null : saved?.cloudId || null));
  const [title, setTitle] = useState(() => (fresh ? 'My resume' : saved?.title || 'My resume'));
  const [sync, setSync] = useState('idle'); // idle | pending | saving | saved | error
  const [library, setLibrary] = useState(false);
  const { user, enabled, openSignIn } = useAuth();
  const cloudIdRef = useRef(cloudId);
  const queue = useRef(Promise.resolve());
  const lastSaved = useRef(null);
  const [gallery, setGallery] = useState(false);
  const [view, setView] = useState('edit');
  const [pages, setPages] = useState(1);
  const [busy, setBusy] = useState(null); // 'upload' | 'docx' | 'check'
  const fileInput = useRef(null);
  const t = templateById(template);

  useEffect(() => {
    loadTemplateFonts();
    if (seed) onSeedUsed?.();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Autosave in this browser
  useEffect(() => {
    if (!resume) return undefined;
    const id = setTimeout(() => writeStorage(KEYS.builder, { resume: plain(resume), template, accent, cloudId, title }), 400);
    return () => clearTimeout(id);
  }, [resume, template, accent, cloudId, title]);

  // Autosave to the account when signed in. Saves run one at a time, so a new
  // resume is created once; nothing is saved just for opening the page.
  const saveKey = resume && user ? JSON.stringify([user.id, title, template, accent, snapshot(resume)]) : null;
  useEffect(() => {
    if (!saveKey || !hasContent(resume)) return undefined;
    if (lastSaved.current === null && cloudIdRef.current) lastSaved.current = saveKey; // opened as it was
    if (saveKey === lastSaved.current) return undefined;
    setSync('pending');
    const id = setTimeout(() => {
      queue.current = queue.current.then(async () => {
        setSync('saving');
        try {
          const row = await saveResume({ id: cloudIdRef.current, title, template, accent, data: plain(resume) });
          cloudIdRef.current = row.id;
          setCloudId(row.id);
          lastSaved.current = saveKey;
          setSync('saved');
        } catch {
          // Deleted on another device, or offline: the next edit saves it as a new resume
          cloudIdRef.current = null;
          setCloudId(null);
          setSync('error');
        }
      });
    }, 1500);
    return () => clearTimeout(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [saveKey]);

  const openSaved = async (id) => {
    try {
      const row = await loadResume(id);
      const data = withIds({ ...EMPTY_RESUME, ...row.data });
      cloudIdRef.current = row.id;
      lastSaved.current = JSON.stringify([user.id, row.title, row.template, row.accent || null, snapshot(data)]);
      setResume(data);
      setTemplate(row.template);
      setAccent(row.accent || null);
      setTitle(row.title);
      setCloudId(row.id);
      setSync('saved');
      setLibrary(false);
    } catch (err) {
      notify({ tone: 'error', message: err.message });
    }
  };

  const saveAsNew = () => {
    cloudIdRef.current = null;
    setCloudId(null);
    setTitle((x) => `${x} (copy)`.slice(0, 80));
    setLibrary(false);
    notify({ tone: 'success', message: 'Saving a new version. Rename it next to the title.' });
  };

  const start = (data) => {
    setResume(withIds({ ...EMPTY_RESUME, ...data }));
    window.scrollTo({ top: 0 });
  };

  const upload = async (file) => {
    if (!file) return;
    setBusy('upload');
    try {
      start(await parseResumeFile(file));
      notify({ tone: 'success', message: 'Imported your resume. Check each section, then pick a template.' });
    } catch (err) {
      notify({ tone: 'error', message: err.message });
    } finally {
      setBusy(null);
    }
  };

  const downloadPdf = () => {
    const title = document.title;
    document.title = `${(resume.name || 'resume').trim().replace(/\s+/g, '_')}_resume`;
    window.print();
    document.title = title;
  };

  const downloadDocx = async () => {
    setBusy('docx');
    try {
      await downloadResumeDocx(plain(resume), { template, accent });
      notify({ tone: 'success', message: `Downloaded your resume in the ${t.name} template.` });
    } catch (err) {
      notify({ tone: 'error', message: err.message });
    } finally {
      setBusy(null);
    }
  };

  const check = async () => {
    setBusy('check');
    try {
      await onCheck(plain(resume));
    } finally {
      setBusy(null);
    }
  };

  const startOver = () => {
    if (!window.confirm('Start a new resume? Your current draft will be cleared from this browser.')) return;
    writeStorage(KEYS.builder, null);
    cloudIdRef.current = null;
    lastSaved.current = null;
    setCloudId(null);
    setTitle('My resume');
    setSync('idle');
    setResume(null);
  };

  const onPages = useCallback((n) => setPages(n), []);

  // Start screen
  if (!resume) {
    return (
      <motion.main
        initial={{ opacity: 0, y: 14 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0 }}
        className="mx-auto w-full max-w-5xl px-4 pt-10 sm:px-6"
      >
        <h1 className="font-display text-4xl font-bold tracking-tight">Build your resume</h1>
        <p className="mt-2 max-w-2xl text-lg text-muted">
          {TEMPLATES.length} ATS-friendly templates, a live preview and instant PDF or Word download. Your draft is saved in this
          browser.
        </p>
        <div className="mt-8 grid gap-4 md:grid-cols-3">
          <StartChoice
            icon={FileUp}
            title="Import my resume"
            text="Upload a PDF or Word file and we'll fill in the sections for you."
            onClick={() => fileInput.current?.click()}
            busy={busy === 'upload'}
          />
          <StartChoice icon={Sparkles} title="Start from a sample" text="A complete student resume you can edit into your own." onClick={() => start(SAMPLE_RESUME)} />
          <StartChoice icon={FilePlus2} title="Start blank" text="An empty resume with all the standard sections." onClick={() => start(EMPTY_RESUME)} />
        </div>
        {user ? (
          <Button variant="secondary" icon={FolderOpen} className="mt-4" onClick={() => setLibrary(true)}>
            Open one of my saved resumes
          </Button>
        ) : (
          enabled && (
            <p className="mt-4 text-sm text-muted">
              <button
                type="button"
                onClick={() => openSignIn('Sign in to keep your resumes in your account and edit them on any device.')}
                className="cursor-pointer font-semibold text-accent hover:underline"
              >
                Sign in
              </button>{' '}
              to keep your resumes in your account.
            </p>
          )
        )}
        <ResumeLibrary open={library} onClose={() => setLibrary(false)} currentId={cloudId} onOpen={openSaved} onDuplicate={() => setLibrary(false)} notify={notify} />
        <input
          ref={fileInput}
          type="file"
          accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
          className="hidden"
          onChange={(e) => {
            upload(e.target.files?.[0]);
            e.target.value = '';
          }}
        />

        <h2 className="mt-12 mb-4 font-display text-2xl font-semibold">The templates</h2>
        <ul className="grid grid-cols-2 gap-4 md:grid-cols-4">
          {TEMPLATES.map((tpl) => (
            <li key={tpl.id}>
              <button
                type="button"
                onClick={() => {
                  setTemplate(tpl.id);
                  start(SAMPLE_RESUME);
                }}
                className="group w-full cursor-pointer text-left"
              >
                <div className="h-56 overflow-hidden rounded-lg bg-white shadow-[0_1px_4px_rgba(0,0,0,0.18)] transition group-hover:-translate-y-1">
                  <ScaledPage resume={SAMPLE_RESUME} templateId={tpl.id} />
                </div>
                <span className="mt-2 block font-semibold">{tpl.name}</span>
                <span className="block text-xs text-muted">{tpl.best_for.join(' · ')}</span>
              </button>
            </li>
          ))}
        </ul>
      </motion.main>
    );
  }

  const preview = (
    <div className="card p-3 sm:p-4">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2 px-1">
        <button
          type="button"
          onClick={() => setGallery(true)}
          className="inline-flex cursor-pointer items-center gap-1.5 text-sm font-semibold hover:text-accent"
        >
          <LayoutTemplate className="size-4" aria-hidden />
          {t.name} template
        </button>
        <span
          className={`rounded-full px-2 py-0.5 text-xs font-bold ${pages === 1 ? 'bg-ok-soft text-ok' : 'bg-warn-soft text-warn'}`}
          title={pages === 1 ? '' : 'Most student and fresher resumes should fit on one page.'}
        >
          {pages === 1 ? 'Fits on 1 page' : `${pages} pages`}
        </span>
      </div>
      <div className="overflow-hidden rounded-lg shadow-[0_1px_6px_rgba(0,0,0,0.15)]">
        <ScaledPage resume={resume} templateId={template} accent={accent} showPages onPages={onPages} />
      </div>
      {pages > 1 && (
        <p className="mt-2 px-1 text-xs text-muted">
          Over one page. For students, trim older or weaker bullets, or try a compact template (Campus, Engineer).
        </p>
      )}
    </div>
  );

  return (
    <motion.main
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
      className="mx-auto w-full max-w-7xl px-4 pt-6 pb-24 sm:px-6"
    >
      {/* Toolbar */}
      <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
        <div className="min-w-0">
          <h1 className="font-display text-3xl font-bold tracking-tight">Resume builder</h1>
          {user ? (
            <div className="mt-1 flex flex-wrap items-center gap-2 text-sm">
              <label htmlFor="resume-title" className="sr-only">
                Resume name
              </label>
              <input
                id="resume-title"
                value={title}
                maxLength={80}
                onChange={(e) => setTitle(e.target.value)}
                className="w-48 rounded-lg border border-transparent bg-transparent px-1.5 py-0.5 font-semibold hover:border-line focus:border-line"
              />
              <span className={`inline-flex items-center gap-1 text-xs ${sync === 'error' ? 'text-pen' : 'text-muted'}`} aria-live="polite">
                {sync === 'error' ? <CloudOff className="size-3.5" aria-hidden /> : <Cloud className="size-3.5" aria-hidden />}
                {sync === 'saving' || sync === 'pending'
                  ? 'Saving…'
                  : sync === 'error'
                    ? 'Not saved to your account; will retry when you edit'
                    : cloudId
                      ? 'Saved to your account'
                      : 'Edit to save to your account'}
              </span>
            </div>
          ) : (
            <p className="text-sm text-muted">
              Saved in this browser as you type.
              {enabled && (
                <>
                  {' '}
                  <button
                    type="button"
                    onClick={() => openSignIn('Sign in to keep your resumes in your account and edit them on any device.')}
                    className="cursor-pointer font-semibold text-accent hover:underline"
                  >
                    Sign in
                  </button>{' '}
                  to save it to your account.
                </>
              )}
            </p>
          )}
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {user && (
            <Button variant="secondary" icon={FolderOpen} onClick={() => setLibrary(true)}>
              My resumes
            </Button>
          )}
          <Button variant="secondary" icon={LayoutTemplate} onClick={() => setGallery(true)}>
            Templates
          </Button>
          <Button variant="secondary" icon={FileText} onClick={downloadPdf}>
            PDF
          </Button>
          <Button variant="secondary" icon={Download} loading={busy === 'docx'} onClick={downloadDocx}>
            Word
          </Button>
          <Button variant="primary" icon={ScanSearch} loading={busy === 'check'} onClick={check} disabled={!hasContent(resume)}>
            Check my score
          </Button>
          <Button variant="ghost" icon={RotateCcw} onClick={startOver} title="Start a new resume">
            New
          </Button>
        </div>
      </div>

      {/* Accent colour */}
      <div className="mb-5 flex flex-wrap items-center gap-2">
        <Palette className="size-4 text-muted" aria-hidden />
        <span className="mr-1 text-sm text-muted">Accent</span>
        {[null, ...ACCENTS].map((color) => {
          const value = color || t.accent;
          const active = (accent || null) === color;
          return (
            <button
              key={color || 'default'}
              type="button"
              onClick={() => setAccent(color)}
              aria-label={color ? `Accent ${color}` : 'Template default accent'}
              aria-pressed={active}
              title={color ? color : 'Template default'}
              className={`grid size-7 cursor-pointer place-items-center rounded-full border-2 transition ${active ? 'border-ink' : 'border-transparent'}`}
            >
              <span className="size-5 rounded-full" style={{ background: value }}>
                {!color && <span className="sr-only">Default</span>}
              </span>
            </button>
          );
        })}
      </div>

      {/* Phones: switch between editing and the preview */}
      <div role="tablist" aria-label="Builder view" className="mb-4 inline-flex rounded-xl bg-sunken p-1 lg:hidden">
        {['edit', 'preview'].map((v) => (
          <button
            key={v}
            type="button"
            role="tab"
            aria-selected={view === v}
            onClick={() => setView(v)}
            className={`cursor-pointer rounded-lg px-4 py-1.5 text-sm font-semibold capitalize ${view === v ? 'bg-card shadow-sm' : 'text-muted'}`}
          >
            {v}
          </button>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,34rem)]">
        <div className={view === 'edit' ? '' : 'hidden lg:block'}>
          <ResumeForm draft={resume} setDraft={setResume} />
        </div>
        <div className={view === 'preview' ? '' : 'hidden lg:block'}>
          <div className="lg:sticky lg:top-24">{preview}</div>
        </div>
      </div>

      <TemplateGallery
        open={gallery}
        onClose={() => setGallery(false)}
        resume={hasContent(resume) ? resume : SAMPLE_RESUME}
        selected={template}
        onSelect={setTemplate}
      />
      <PrintResume resume={resume} templateId={template} accent={accent} />
      <ResumeLibrary open={library} onClose={() => setLibrary(false)} currentId={cloudId} onOpen={openSaved} onDuplicate={saveAsNew} notify={notify} />
    </motion.main>
  );
}
