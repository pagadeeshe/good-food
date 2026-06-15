import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import { fetchCurrentUser, login as apiLogin, logout as apiLogout } from '../api/client';
import type { User } from '../api/types';
import { LoadingState } from '../components/PageHeader';

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  isAdmin: boolean;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCurrentUser()
      .then(setUser)
      .finally(() => setLoading(false));
  }, []);

  const value = useMemo<AuthContextValue>(() => ({
    user,
    loading,
    isAdmin: Boolean(user?.is_portal_admin),
    async login(email, password) {
      const data = await apiLogin(email, password);
      setUser(data.user);
    },
    async logout() {
      await apiLogout();
      setUser(null);
    },
  }), [user, loading]);

  if (loading) {
    return <LoadingState label="Loading…" />;
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
