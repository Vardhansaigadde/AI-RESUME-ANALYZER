import { createContext, useContext } from 'react';

/** { user, ready, enabled, openSignIn(reason?), signOut(), deleteAccount() } — see AuthProvider. */
export const AuthContext = createContext({
  user: null,
  ready: true,
  enabled: false,
  openSignIn: () => {},
  signOut: async () => {},
  deleteAccount: async () => {},
});

export const useAuth = () => useContext(AuthContext);

/** First name for greetings. */
export function firstName(user) {
  const name = user?.user_metadata?.full_name || user?.user_metadata?.name || '';
  const first = name.trim().split(/\s+/)[0] || (user?.email || '').split('@')[0].replace(/[\d._-]+$/, '');
  // "vardhansai" or "VARDHANSAI" → "Vardhansai"
  return first ? first.charAt(0).toUpperCase() + first.slice(1).toLowerCase() : '';
}
