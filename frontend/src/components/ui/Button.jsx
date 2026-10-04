import { motion } from 'framer-motion';
import { LoaderCircle } from 'lucide-react';

const VARIANTS = {
  primary:
    'bg-ink text-paper hover:bg-ink/90 shadow-[0_3px_0_0_var(--color-accent)] hover:shadow-[0_5px_0_0_var(--color-accent)]',
  accent: 'bg-accent text-white hover:brightness-110 shadow-[0_3px_0_0_var(--color-ink)]',
  secondary: 'bg-card text-ink border border-line hover:border-ink/40',
  ghost: 'text-muted hover:text-ink hover:bg-sunken',
  danger: 'text-pen hover:bg-pen-soft',
};

const SIZES = {
  sm: 'h-8 px-3 text-xs gap-1.5 rounded-lg',
  md: 'h-10 px-4 text-sm gap-2 rounded-xl',
  lg: 'h-13 px-7 text-base gap-2.5 rounded-2xl',
};

/** Button with a springy press, an optional leading icon and a loading state. */
export default function Button({
  variant = 'primary',
  size = 'md',
  icon: Icon,
  loading = false,
  disabled = false,
  className = '',
  children,
  ...props
}) {
  const inactive = disabled || loading;
  return (
    <motion.button
      type="button"
      whileHover={inactive ? undefined : { y: -1 }}
      whileTap={inactive ? undefined : { y: 1, scale: 0.98 }}
      transition={{ type: 'spring', stiffness: 500, damping: 30 }}
      disabled={inactive}
      className={`inline-flex shrink-0 cursor-pointer items-center justify-center font-semibold transition-[background,box-shadow,color,border-color] disabled:cursor-not-allowed disabled:opacity-45 disabled:shadow-none ${VARIANTS[variant]} ${SIZES[size]} ${className}`}
      {...props}
    >
      {loading ? <LoaderCircle className="size-4 animate-spin" aria-hidden /> : Icon && <Icon className="size-4" aria-hidden />}
      {children}
    </motion.button>
  );
}
