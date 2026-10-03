import { motion } from 'framer-motion';
import { ArrowLeft } from 'lucide-react';
import { REPO_URL } from '../layout/Footer';
import Button from '../ui/Button';

const ISSUES_URL = `${REPO_URL}/issues`;

function LegalPage({ title, effective, onHome, children }) {
  return (
    <motion.main
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
      className="mx-auto w-full max-w-3xl px-4 pt-10 sm:px-6"
    >
      <Button variant="ghost" size="sm" icon={ArrowLeft} onClick={onHome}>
        Back to FitLens
      </Button>
      <article className="card prose-legal mt-4 p-6 sm:p-10">
        <h1 className="font-display text-4xl font-bold tracking-tight">{title}</h1>
        <p className="mt-2 text-sm text-muted">Effective {effective}</p>
        {children}
        <h2>Contact</h2>
        <p>
          Questions or requests? Open an issue on{' '}
          <a href={ISSUES_URL} target="_blank" rel="noreferrer" className="font-semibold text-accent underline underline-offset-4">
            the FitLens GitHub repository
          </a>
          .
        </p>
      </article>
    </motion.main>
  );
}

export function PrivacyPage({ onHome }) {
  return (
    <LegalPage title="Privacy Policy" effective="October 2026" onHome={onHome}>
      <h2>What you send us</h2>
      <ul>
        <li>
          <strong>Your resume file</strong> (PDF or DOCX) and the text extracted from it.
        </li>
        <li>
          <strong>The job description</strong> you paste.
        </li>
        <li>
          <strong>Edited resume content</strong>, when you re-check your score or download a .docx from the editor.
        </li>
      </ul>

      <h2>How it is handled</h2>
      <ul>
        <li>
          <strong>Used only for your request.</strong> Files and text are processed to produce your result and discarded
          when the response is sent. Uploads over 1 MB may sit in a temporary file on the server during that request;
          nothing is kept afterwards.
        </li>
        <li>
          <strong>No database, no accounts, no history.</strong> We do not store resumes, job descriptions or results.
        </li>
        <li>
          <strong>Not in our logs.</strong> Server logs record operational details such as request paths, status codes and
          file types, never resume content.
        </li>
        <li>
          <strong>Your theme choice</strong> (light or dark) is saved in your own browser only.
        </li>
      </ul>

      <h2>Models and third parties</h2>
      <ul>
        <li>
          The scoring and classification models were trained on public datasets before deployment.{' '}
          <strong>Your data is never used to train them.</strong>
        </li>
        <li>
          All analysis runs on our own server. Your resume is <strong>not sent to any AI provider</strong> or analytics
          service, and we never sell or share it.
        </li>
        <li>The site is hosted on Vercel (frontend) and Render (backend), which process requests to deliver the service.</li>
      </ul>
    </LegalPage>
  );
}

export function TermsPage({ onHome }) {
  return (
    <LegalPage title="Terms of Use" effective="October 2026" onHome={onHome}>
      <h2>An informational tool</h2>
      <p>
        FitLens helps you assess and improve your own resume. Match scores, ATS checks, skill comparisons, suggestions and
        job categories are automated estimates from machine-learning models and rules. They are not career advice or a
        hiring decision.
      </p>

      <h2>No guarantee of outcomes</h2>
      <p>
        A high score or ATS rating does not guarantee an interview or job. Real applicant tracking systems and recruiters
        differ. You are responsible for making sure everything on your resume is accurate and true. Only add skills you
        actually have.
      </p>

      <h2>Your content</h2>
      <ul>
        <li>
          <strong>You keep all rights</strong> to your resume and the documents you download.
        </li>
        <li>
          <strong>Limited use:</strong> by uploading, you let FitLens process your content only to produce your result.
        </li>
      </ul>

      <h2>As-is service</h2>
      <p>
        FitLens is provided “as is” and “as available”, without warranties of any kind. To the extent permitted by law, its
        creators are not liable for any damages arising from its use.
      </p>
    </LegalPage>
  );
}

export function NotFoundPage({ onHome }) {
  return (
    <motion.main initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mx-auto flex max-w-md flex-col items-center px-4 pt-24 text-center">
      <motion.p
        initial={{ rotate: -20, scale: 0.6 }}
        animate={{ rotate: -6, scale: 1 }}
        transition={{ type: 'spring', stiffness: 300, damping: 10 }}
        className="font-mono text-7xl font-bold"
      >
        <span className="marker px-2">404</span>
      </motion.p>
      <h1 className="mt-6 font-display text-3xl font-bold">This page isn’t on the resume</h1>
      <p className="mt-2 text-muted">The link may be broken or the page may have moved.</p>
      <Button className="mt-6" icon={ArrowLeft} onClick={onHome}>
        Back to FitLens
      </Button>
    </motion.main>
  );
}
