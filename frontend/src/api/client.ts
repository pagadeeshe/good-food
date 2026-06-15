import type { AuthResponse, User } from './types';

const API_BASE = import.meta.env.VITE_API_URL?.replace(/\/$/, '') ?? '';

type RequestOptions = RequestInit & { auth?: boolean };

class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function refreshAccessToken(): Promise<boolean> {
  const res = await fetch(`${API_BASE}/api/auth/token/refresh/`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({}),
  });
  return res.ok;
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> | undefined),
  };

  let response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
    credentials: 'include',
  });

  if (response.status === 401 && options.auth !== false) {
    const refreshed = await refreshAccessToken();
    if (refreshed) {
      response = await fetch(`${API_BASE}${path}`, {
        ...options,
        headers,
        credentials: 'include',
      });
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

export async function fetchCurrentUser(): Promise<User | null> {
  try {
    return await apiRequest<User>('/api/auth/profile/');
  } catch {
    return null;
  }
}

export async function login(email: string, password: string): Promise<AuthResponse> {
  const data = await apiRequest<AuthResponse>('/api/auth/login/', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
    auth: false,
  });
  return data;
}

export async function logout() {
  try {
    await apiRequest('/api/auth/logout/', {
      method: 'POST',
      body: JSON.stringify({}),
      auth: false,
    });
  } catch {
    // Clear client state even if logout request fails.
  }
}
