import { AnimatePresence, motion } from 'framer-motion';
import { Copy, FileText, LoaderCircle, Trash2, X } from 'lucide-react';
import { useEffect, useState } from 'react';
import { deleteResume, listResumes } from '../../lib/cloud';
import { templateById } from '../../lib/templates';

function ago(iso) {
  const minutes = Math.round((Date.now() - new Date(iso).getTime()) / 60000);
  if (minutes < 1) return 'just now';
  if (minutes < 60) return `${minutes} min ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours} h ago`;
  return new Date(iso).toLocaleDateString();
}

function useSavedResumes(notify) {
  const [items, setItems] = useState(null);
  useEffect(() => {
    let live = true;
    listResumes()
      .then((rows) => live && setItems(rows))
      .catch((err) => {
        notify({ tone: 'error', message: err.message });
        if (live) setItems([]);
      });
    return () => {
      live = false;
    };
  }, [notify]);
  return [items, setItems];
}

/** The signed-in user's saved resumes: open, duplicate (save as a new version) or delete. */
export default function ResumeLibrary({ open, ...props }) {
  useEffect(() => {
    if (!open) return undefined;
    const onKey = (e) => e.key === 'Escape' && props.onClose();
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [open, props]);
  return <AnimatePresence>{open && <LibraryPanel key="library" {...props} />}</AnimatePresence>;
}

function LibraryPanel({ onClose, currentId, onOpen, onDuplicate, notify }) {
  const [items, setItems] = useSavedResumes(notify);

  const remove = async (row) => {
    if (!window.confirm(`Delete “${row.title}” from your account?`)) return;
    try {
      await deleteResume(row.id);
      setItems((list) => list.filter((x) => x.id !== row.id));
    } catch (err) {
      notify({ tone: 'error', message: err.message });
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 grid place-items-center bg-ink/40 p-4 backdrop-blur-sm"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="library-title"
    >
      <motion.div
        initial={{ y: 20 }}
        animate={{ y: 0 }}
        exit={{ y: 20 }}
        onClick={(e) => e.stopPropagation()}
        className="card w-full max-w-lg p-5"
      >
        <div className="mb-4 flex items-center justify-between">
          <h2 id="library-title" className="font-display text-2xl font-semibold">
            My resumes
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="grid size-8 cursor-pointer place-items-center rounded-lg hover:bg-sunken"
            aria-label="Close"
          >
            <X className="size-4" />
          </button>
        </div>
        <p className="mb-4 text-sm text-muted">
          Keep a version per role, e.g. one for data jobs and one for developer jobs.
        </p>

        {items === null ? (
          <p className="flex items-center gap-2 py-6 text-sm text-muted">
            <LoaderCircle className="size-4 animate-spin" aria-hidden /> Loading…
          </p>
        ) : items.length === 0 ? (
          <p className="py-6 text-sm text-muted">No saved resumes yet. Your current draft is saved as you type.</p>
        ) : (
          <ul className="max-h-[50vh] space-y-2 overflow-y-auto">
            {items.map((row) => (
              <li
                key={row.id}
                className={`flex items-center gap-3 rounded-xl border p-3 ${row.id === currentId ? 'border-accent bg-accent-soft/40' : 'border-line'}`}
              >
                <FileText className="size-5 shrink-0 text-muted" aria-hidden />
                <button
                  type="button"
                  onClick={() => onOpen(row.id)}
                  className="min-w-0 flex-1 cursor-pointer text-left"
                >
                  <span className="block truncate font-semibold">{row.title}</span>
                  <span className="block text-xs text-muted">
                    {templateById(row.template).name} · edited {ago(row.updated_at)}
                    {row.id === currentId && ' · open now'}
                  </span>
                </button>
                <button
                  type="button"
                  onClick={() => remove(row)}
                  className="grid size-8 cursor-pointer place-items-center rounded-lg text-muted hover:bg-pen-soft hover:text-pen"
                  aria-label={`Delete ${row.title}`}
                >
                  <Trash2 className="size-4" />
                </button>
              </li>
            ))}
          </ul>
        )}

        <button
          type="button"
          onClick={onDuplicate}
          className="mt-4 inline-flex cursor-pointer items-center gap-1.5 text-sm font-semibold text-accent hover:underline"
        >
          <Copy className="size-4" aria-hidden />
          Save the open resume as a new version
        </button>
      </motion.div>
    </motion.div>
  );
}
