import { Component } from 'react';

/** Catches render errors and shows a friendly fallback instead of a blank page. */
export default class ErrorBoundary extends Component {
  state = { hasError: false };

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error, info) {
    console.error('Unhandled UI error:', error, info);
  }

  render() {
    if (!this.state.hasError) return this.props.children;
    return (
      <main className="mx-auto flex min-h-screen max-w-md flex-col items-center justify-center px-4 text-center">
        <p className="font-mono text-5xl font-bold">
          <span className="marker px-2">Oops</span>
        </p>
        <h1 className="mt-6 font-display text-2xl font-bold">Something went wrong</h1>
        <p className="mt-2 text-muted">An unexpected error occurred while showing this page. Reloading usually fixes it.</p>
        <div className="mt-6 flex gap-3">
          <button
            type="button"
            onClick={() => window.location.reload()}
            className="cursor-pointer rounded-xl bg-ink px-4 py-2.5 text-sm font-semibold text-paper"
          >
            Reload
          </button>
          <a href="/" className="rounded-xl border border-line px-4 py-2.5 text-sm font-semibold">
            Go home
          </a>
        </div>
      </main>
    );
  }
}
