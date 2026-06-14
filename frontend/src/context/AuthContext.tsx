import { createContext, useContext, useMemo, useState, type ReactNode } from 'react';
import { login as apiLogin, logout as apiLogout } from '../api/client';
import type { User } from '../api/types';

interface AuthContextValue {
  user: User | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  isAdmin: boolean;
}

const AuthContext = createContext<AuthContextValue | null>(null);

function loadUser(): User | null {
  const raw = localStorage.getItem('user');
  if (!raw) return null;
  try {
    return JSON.parse(raw) as User;
  } catch {
    return null;
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(loadUser);

  const value = useMemo<AuthContextValue>(() => ({
    user,
    isAdmin: Boolean(user?.is_portal_admin),
    async login(email, password) {
      const data = await apiLogin(email, password);
      setUser(data.user);
    },
    async logout() {
      await apiLogout();
      setUser(null);
    },
  }), [user]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
