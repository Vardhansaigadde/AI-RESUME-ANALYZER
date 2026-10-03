import { motion } from 'framer-motion';
import { ArrowDown, ArrowUp, Briefcase } from 'lucide-react';
import { useCountUp } from '../../hooks/useCountUp';
import { scoreTone } from '../../lib/resume';
import { formatRole } from '../../utils/format';

function Delta({ value }) {
  if (value == null || Math.abs(value) < 0.5) return null;
  const up = value > 0;
  const Icon = up ? ArrowUp : ArrowDown;
  return (
    <motion.span
      initial={{ scale: 0, rotate: -20 }}
      animate={{ scale: 1, rotate: 0 }}
      transition={{ type: 'spring', stiffness: 500, damping: 14, delay: 0.6 }}
      className={`inline-flex items-center gap-0.5 rounded-full px-2 py-0.5 font-mono text-xs font-bold ${up ? 'bg-ok-soft text-ok' : 'bg-pen-soft text-pen'}`}
      title="Change since your original upload"
    >
      <Icon className="size-3" aria-hidden />
      {Math.abs(value).toFixed(0)}
    </motion.span>
  );
}

/** Circular match-score dial that fills and counts up. */
function MatchDial({ score, delta }) {
  const shown = useCountUp(score, 1300);
  const tone = scoreTone(score);
  const r = 44;
  const circumference = 2 * Math.PI * r;
  return (
    <div className="card flex items-center gap-5 p-5">
      <div className="relative size-28 shrink-0">
        <svg viewBox="0 0 100 100" className="size-full -rotate-90" aria-hidden>
          <circle cx="50" cy="50" r={r} fill="none" stroke="var(--color-sunken)" strokeWidth="9" />
          <motion.circle
            cx="50"
            cy="50"
            r={r}
            fill="none"
            stroke={tone.stroke}
            strokeWidth="9"
            strokeLinecap="round"
            strokeDasharray={circumference}
            initial={{ strokeDashoffset: circumference }}
            animate={{ strokeDashoffset: circumference * (1 - score / 100) }}
            transition={{ duration: 1.3, ease: [0.16, 1, 0.3, 1] }}
          />
        </svg>
        <div className="absolute inset-0 grid place-items-center">
          <span id="match-score-value" className="font-mono text-3xl font-bold">
            {shown.toFixed(0)}
            <span className="text-base text-muted">%</span>
          </span>
        </div>
      </div>
      <div>
        <p className="text-xs font-semibold tracking-wide text-muted uppercase">Job match</p>
        <p className={`mt-1 font-display text-xl font-semibold ${tone.text}`}>
          {score >= 75 ? 'Strong fit' : score >= 50 ? 'Partial fit' : 'Weak fit'}
        </p>
        <div className="mt-2">
          <Delta value={delta} />
        </div>
      </div>
    </div>
  );
}

/** ATS score shown as a rubber stamp that thumps onto the page. */
function AtsStamp({ ats, delta }) {
  const shown = useCountUp(ats.score, 1100);
  const tone = scoreTone(ats.score);
  return (
    <div className="card flex items-center gap-5 p-5">
      <motion.div
        initial={{ scale: 2.2, rotate: -24, opacity: 0 }}
        animate={{ scale: 1, rotate: -8, opacity: 1 }}
        transition={{ type: 'spring', stiffness: 380, damping: 15, delay: 0.25 }}
        className={`grid size-28 shrink-0 place-items-center rounded-full border-[3px] border-dashed ${tone.text}`}
        style={{ borderColor: 'currentColor' }}
      >
        <div className="text-center leading-none">
          <div className="font-mono text-3xl font-bold">{shown.toFixed(0)}</div>
          <div className="mt-1 text-[10px] font-bold tracking-[0.2em]">ATS</div>
        </div>
      </motion.div>
      <div>
        <p className="text-xs font-semibold tracking-wide text-muted uppercase">ATS check</p>
        <p className={`mt-1 font-display text-xl font-semibold ${tone.text}`}>{ats.verdict}</p>
        <div className="mt-2">
          <Delta value={delta} />
        </div>
      </div>
    </div>
  );
}

function TopRole({ roles, confidence }) {
  const top = roles?.[0];
  return (
    <div className="card flex items-center gap-5 p-5">
      <motion.span
        initial={{ y: -12, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ type: 'spring', stiffness: 300, damping: 16, delay: 0.4 }}
        className="grid size-16 shrink-0 place-items-center rounded-2xl bg-accent-soft text-accent"
      >
        <Briefcase className="size-7" aria-hidden />
      </motion.span>
      <div className="min-w-0">
        <p className="text-xs font-semibold tracking-wide text-muted uppercase">Closest job category</p>
        <p className="mt-1 truncate font-display text-xl font-semibold">{top ? formatRole(top.role) : '—'}</p>
        <p className="mt-1 text-xs text-muted">{confidence === 'low' ? 'Not a clear match, see the Match tab' : `${top?.match_percent.toFixed(0)}% likely`}</p>
      </div>
    </div>
  );
}

export default function SummaryCards({ result, original }) {
  const delta = (key) => (original && original !== result ? key(result) - key(original) : null);
  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
      <MatchDial score={result.match_score} delta={delta((r) => r.match_score)} />
      {result.ats && <AtsStamp ats={result.ats} delta={delta((r) => r.ats?.score ?? 0)} />}
      <TopRole roles={result.suggested_roles} confidence={result.confidence} />
    </div>
  );
}
