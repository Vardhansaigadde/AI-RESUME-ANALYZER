import { motion } from 'framer-motion';

/** Accessible on/off switch with a springy knob. */
export default function Switch({ checked, onChange, label, description, disabled = false }) {
  return (
    <label className={`flex items-start gap-3 ${disabled ? 'cursor-not-allowed opacity-50' : 'cursor-pointer'}`}>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        disabled={disabled}
        onClick={() => onChange(!checked)}
        className={`relative mt-0.5 inline-flex h-6 w-11 shrink-0 cursor-pointer items-center rounded-full border transition-colors ${
          checked ? 'border-accent bg-accent' : 'border-line bg-sunken'
        }`}
      >
        <motion.span
          layout
          transition={{ type: 'spring', stiffness: 600, damping: 30 }}
          className={`size-4.5 rounded-full bg-white shadow ${checked ? 'ml-[22px]' : 'ml-[3px]'}`}
        />
      </button>
      <span>
        <span className="block text-sm font-semibold">{label}</span>
        {description && <span className="block text-xs text-muted">{description}</span>}
      </span>
    </label>
  );
}
