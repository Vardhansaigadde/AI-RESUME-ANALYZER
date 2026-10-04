import { motion } from 'framer-motion';
import { ArrowDown, ArrowUp } from 'lucide-react';
import { useCountUp } from '../../hooks/useCountUp';
import { scoreTone } from '../../lib/resume';
import { resumeStrength } from '../../lib/strength';

function Delta({ value }) {
  if (value == null || Math.abs(value) < 0.5) return null;
  const up = value > 0;
  const Icon = up ? ArrowUp : ArrowDown;
  return (
    <motion.span
      initial={{ scale: 0, rotate: -20 }}
      animate={{ scale: 1, rotate: 0 }}
      transition={{ type: 'spring', stiffness: 500, damping: 14, delay: 0.6 }}
      className={`inline-flex items-center gap-0.5 rounded-full px-1.5 py-0.5 font-mono text-[11px] font-bold ${
        up ? 'bg-ok-soft text-ok' : 'bg-pen-soft text-pen'
      }`}
      title="Change since your original upload"
    >
      <Icon className="size-3" aria-hidden />
      {Math.abs(value).toFixed(0)}
    </motion.span>
  );
}

/** Shared layout: visual on the left, label / verdict / change on the right. */
function ScoreCard({ visual, label, verdict, tone, delta }) {
  return (
    <div className="card flex flex-col items-center gap-2 p-3 text-center md:flex-row md:gap-4 md:p-5 md:text-left">
      {visual}
      <div className="min-w-0">
        <p className="text-[10px] font-semibold tracking-wide text-muted uppercase md:text-xs">{label}</p>
        <p className={`mt-0.5 font-display text-sm leading-tight font-semibold md:truncate md:text-lg ${tone.text}`}>{verdict}</p>
        <div className="mt-1 hidden h-5 md:block">
          <Delta value={delta} />
        </div>
      </div>
    </div>
  );
}

/** Circular progress dial that fills and counts up. */
function Dial({ value, tone, suffix = '%', id }) {
  const shown = useCountUp(value, 1200);
  const r = 42;
  const circumference = 2 * Math.PI * r;
  return (
    <div className="relative size-16 shrink-0 md:size-20">
      <svg viewBox="0 0 100 100" className="size-full -rotate-90" aria-hidden>
        <circle cx="50" cy="50" r={r} fill="none" stroke="var(--color-sunken)" strokeWidth="10" />
        <motion.circle
          cx="50"
          cy="50"
          r={r}
          fill="none"
          stroke={tone.stroke}
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: circumference * (1 - value / 100) }}
          transition={{ duration: 1.2, ease: [0.16, 1, 0.3, 1] }}
        />
      </svg>
      <span id={id} className="absolute inset-0 grid place-items-center font-mono text-lg font-bold md:text-xl">
        {shown.toFixed(0)}
        <span className="sr-only">{suffix}</span>
      </span>
    </div>
  );
}

/** ATS score as a rubber stamp that thumps onto the page. */
function Stamp({ value, tone }) {
  const shown = useCountUp(value, 1000);
  return (
    <motion.div
      initial={{ scale: 2.2, rotate: -24, opacity: 0 }}
      animate={{ scale: 1, rotate: -8, opacity: 1 }}
      transition={{ type: 'spring', stiffness: 380, damping: 15, delay: 0.25 }}
      className={`grid size-16 shrink-0 place-items-center rounded-full border-[3px] border-dashed md:size-20 ${tone.text}`}
      style={{ borderColor: 'currentColor' }}
    >
      <div className="text-center leading-none">
        <div className="font-mono text-lg font-bold md:text-xl">{shown.toFixed(0)}</div>
        <div className="mt-0.5 text-[9px] font-bold tracking-[0.2em]">ATS</div>
      </div>
    </motion.div>
  );
}

/** Letter grade tile. */
function GradeTile({ grade, tone }) {
  return (
    <motion.span
      initial={{ scale: 0, rotate: -25 }}
      animate={{ scale: 1, rotate: -6 }}
      transition={{ type: 'spring', stiffness: 380, damping: 13, delay: 0.4 }}
      className={`grid size-16 shrink-0 place-items-center rounded-2xl font-display text-4xl font-bold md:size-20 md:text-5xl ${tone.bg} ${tone.text}`}
    >
      {grade}
    </motion.span>
  );
}

export default function SummaryCards({ result, original, draft }) {
  const sameMode = original && original.mode === result.mode;
  const delta = (pick) => (original && original !== result && sameMode ? pick(result) - pick(original) : null);
  const strength = resumeStrength(draft || result.resume, { studentMode: result.student_mode });
  const strengthTone = scoreTone(strength.score);

  const cards = [];
  if (result.mode === 'resume_only') {
    const coverage = Math.round((result.role_gap?.coverage || 0) * 100);
    // Coverage of a role's core skills: 70%+ ready, 40%+ getting there
    const tone = scoreTone(coverage >= 70 ? 75 : coverage >= 40 ? 50 : 0);
    cards.push(
      <ScoreCard
        key="strength"
        label="Resume strength"
        verdict={`${strength.score}/100`}
        tone={strengthTone}
        visual={<GradeTile grade={strength.grade} tone={strengthTone} />}
      />,
    );
    if (result.ats) {
      const atsTone = scoreTone(result.ats.score);
      cards.push(
        <ScoreCard key="ats" label="ATS check" verdict={result.ats.verdict} tone={atsTone} delta={delta((r) => r.ats?.score ?? 0)} visual={<Stamp value={result.ats.score} tone={atsTone} />} />,
      );
    }
    if (result.role_gap) {
      cards.push(
        <ScoreCard
          key="role"
          label={result.role_gap.role}
          verdict={coverage >= 70 ? 'Ready' : coverage >= 40 ? 'Getting there' : 'Skills to build'}
          tone={tone}
          visual={<Dial value={coverage} tone={tone} />}
        />,
      );
    }
  } else {
    const matchTone = scoreTone(result.match_score);
    cards.push(
      <ScoreCard
        key="match"
        label="Job match"
        verdict={result.match_score >= 75 ? 'Strong fit' : result.match_score >= 50 ? 'Partial fit' : 'Weak fit'}
        tone={matchTone}
        delta={delta((r) => r.match_score)}
        visual={<Dial id="match-score-value" value={result.match_score} tone={matchTone} />}
      />,
    );
    if (result.ats) {
      const atsTone = scoreTone(result.ats.score);
      cards.push(
        <ScoreCard key="ats" label="ATS check" verdict={result.ats.verdict} tone={atsTone} delta={delta((r) => r.ats?.score ?? 0)} visual={<Stamp value={result.ats.score} tone={atsTone} />} />,
      );
    }
    cards.push(
      <ScoreCard
        key="strength"
        label="Resume strength"
        verdict={`Grade ${strength.grade}`}
        tone={strengthTone}
        visual={<GradeTile grade={strength.grade} tone={strengthTone} />}
      />,
    );
  }

  return <div className="grid grid-cols-3 gap-2 md:gap-4">{cards}</div>;
}
