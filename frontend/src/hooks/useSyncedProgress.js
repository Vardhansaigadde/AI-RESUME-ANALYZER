import { useEffect, useRef, useState } from 'react';
import { useAuth } from '../lib/authContext';
import { loadProgress, saveProgress } from '../lib/cloud';
import { KEYS, readStorage, writeStorage } from '../lib/storage';

/** Combine two { skill: [ticks] } maps: a box ticked on either device stays ticked. */
function merge(a = {}, b = {}) {
  const out = { ...a };
  for (const [skill, ticks] of Object.entries(b)) {
    const mine = out[skill] || [];
    const len = Math.max(mine.length, ticks.length);
    out[skill] = Array.from({ length: len }, (_, i) => Boolean(mine[i] || ticks[i]));
  }
  return out;
}

/**
 * Roadmap checklist ticks and weekly pace. Always kept in this browser; when signed
 * in, merged with the account's copy and saved back to it.
 */
export function useSyncedProgress() {
  const { user } = useAuth();
  const [progress, setProgress] = useState(() => readStorage(KEYS.progress, {}));
  const [pace, setPace] = useState(() => readStorage(KEYS.pace, 8));
  const synced = useRef(null); // id of the user whose account copy has been merged

  useEffect(() => writeStorage(KEYS.progress, progress), [progress]);
  useEffect(() => writeStorage(KEYS.pace, pace), [pace]);

  // After sign-in, fetch the account's copy and merge it in
  useEffect(() => {
    if (!user) {
      synced.current = null;
      return undefined;
    }
    let live = true;
    loadProgress()
      .then((row) => {
        if (!live) return;
        synced.current = user.id;
        if (row?.hours_per_week) setPace(row.hours_per_week);
        setProgress((local) => merge(local, row?.progress)); // new object: triggers the save below
      })
      .catch(() => {
        // Offline or not set up yet: keep working from this browser
      });
    return () => {
      live = false;
    };
  }, [user]);

  // Save changes to the account (debounced)
  useEffect(() => {
    if (!user || synced.current !== user.id) return undefined;
    const id = setTimeout(() => saveProgress(progress, pace).catch(() => {}), 1000);
    return () => clearTimeout(id);
  }, [user, progress, pace]);

  return { progress, setProgress, pace, setPace };
}
