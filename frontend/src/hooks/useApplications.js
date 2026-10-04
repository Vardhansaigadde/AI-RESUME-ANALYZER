import { useCallback, useEffect, useMemo, useState } from 'react';
import { useAuth } from '../lib/authContext';
import { deleteApplication, listApplications, saveApplication, updateApplication } from '../lib/cloud';

/** The signed-in user's tracked applications, with save / update / remove. Empty when signed out. */
export function useApplications() {
  const { user } = useAuth();
  const [state, setState] = useState({ userId: null, items: [], error: null });

  useEffect(() => {
    if (!user) return undefined;
    let live = true;
    listApplications()
      .then((items) => live && setState({ userId: user.id, items, error: null }))
      .catch((err) => live && setState({ userId: user.id, items: [], error: err.message }));
    return () => {
      live = false;
    };
  }, [user]);

  const current = user && state.userId === user.id;
  const items = useMemo(() => (current ? state.items : []), [current, state.items]);
  const setItems = (fn) => setState((s) => ({ ...s, items: fn(s.items) }));

  const save = useCallback(async (job) => {
    const row = await saveApplication(job);
    setItems((list) => [row, ...list.filter((x) => x.id !== row.id)]);
    return row;
  }, []);

  const update = useCallback(async (id, patch) => {
    // Optimistic: show the change at once, roll back if the save fails
    let previous;
    setItems((list) =>
      list.map((x) => {
        if (x.id !== id) return x;
        previous = x;
        return { ...x, ...patch };
      }),
    );
    try {
      const row = await updateApplication(id, patch);
      setItems((list) => list.map((x) => (x.id === id ? row : x)));
    } catch (err) {
      if (previous) setItems((list) => list.map((x) => (x.id === id ? previous : x)));
      throw err;
    }
  }, []);

  const remove = useCallback(async (id) => {
    await deleteApplication(id);
    setItems((list) => list.filter((x) => x.id !== id));
  }, []);

  const savedUrls = useMemo(() => new Set(items.map((x) => x.url)), [items]);
  return {
    items,
    loading: Boolean(user) && !current,
    error: current ? state.error : null,
    save,
    update,
    remove,
    savedUrls,
  };
}
