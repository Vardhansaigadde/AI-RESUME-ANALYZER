// Shared Framer Motion presets.

/** Fade-and-rise used by staggered cards. */
export const reveal = {
  hidden: { opacity: 0, y: 14 },
  show: { opacity: 1, y: 0, transition: { type: 'spring', stiffness: 260, damping: 24 } },
};
