export const REPO_URL = 'https://github.com/Vardhansaigadde/AI-RESUME-ANALYZER';

export default function Footer({ onNavigate }) {
  const link = (path, label) => (
    <a
      href={path}
      onClick={(e) => {
        e.preventDefault();
        onNavigate(path);
      }}
      className="hover:text-ink"
    >
      {label}
    </a>
  );

  return (
    <footer className="mt-16 border-t border-line/70">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-6 text-sm text-muted sm:px-6">
        <p>© {new Date().getFullYear()} FitLens</p>
        <nav className="flex items-center gap-4" aria-label="Footer">
          {link('/privacy', 'Privacy')}
          {link('/terms', 'Terms')}
          <a href={REPO_URL} target="_blank" rel="noreferrer" className="hover:text-ink">
            GitHub
          </a>
        </nav>
      </div>
    </footer>
  );
}
