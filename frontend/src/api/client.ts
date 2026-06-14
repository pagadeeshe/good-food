import type { AuthResponse } from './types';

const API_BASE = import.meta.env.VITE_API_URL?.replace(/\/$/, '') ?? '';

type RequestOptions = RequestInit & { auth?: boolean };

class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

function getTokens() {
  const access = localStorage.getItem('access_token');
  const refresh = localStorage.getItem('refresh_token');
  return { access, refresh };
}

export function setTokens(access: string, refresh: string) {
  localStorage.setItem('access_token', access);
  localStorage.setItem('refresh_token', refresh);
}

export function clearTokens() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user');
}

async function refreshAccessToken(): Promise<string | null> {
  const { refresh } = getTokens();
  if (!refresh) return null;

  const res = await fetch(`${API_BASE}/api/auth/token/refresh/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh }),
  });

  if (!res.ok) return null;
  const data = await res.json();
  localStorage.setItem('access_token', data.access);
  return data.access as string;
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> | undefined),
  };

  if (options.auth !== false) {
    const { access } = getTokens();
    if (access) headers.Authorization = `Bearer ${access}`;
  }

  let response = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (response.status === 401 && options.auth !== false) {
    const newAccess = await refreshAccessToken();
    if (newAccess) {
      headers.Authorization = `Bearer ${newAccess}`;
      response = await fetch(`${API_BASE}${path}`, { ...options, headers });
    }
  }

  if (!response.ok) {
    let message = 'Request failed';
    try {
      const err = await response.json();
      message = err.error || err.detail || JSON.stringify(err);
    } catch {
      message = response.statusText;
    }
    throw new ApiError(message, response.status);
  }

  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export async function login(email: string, password: string): Promise<AuthResponse> {
  const data = await apiRequest<AuthResponse>('/api/auth/login/', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
    auth: false,
  });
  setTokens(data.access, data.refresh);
  localStorage.setItem('user', JSON.stringify(data.user));
  return data;
}

export async function logout() {
  const { refresh } = getTokens();
  try {
    if (refresh) {
      await apiRequest('/api/auth/logout/', {
        method: 'POST',
        body: JSON.stringify({ refresh_token: refresh }),
      });
    }
  } finally {
    clearTokens();
  }
}
