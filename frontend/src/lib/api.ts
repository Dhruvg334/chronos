import { supabase } from './supabase';

const rawApiUrl = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

export const API_BASE_URL = rawApiUrl.replace(/\/$/, '');

export function apiUrl(path: string): string {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return `${API_BASE_URL}${normalizedPath}`;
}

export async function apiFetch(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  const { data: { session } } = await supabase.auth.getSession();
  const headers = new Headers(init?.headers);

  if (session?.access_token) {
    headers.set('Authorization', `Bearer ${session.access_token}`);
  }

  return fetch(input, {
    ...init,
    headers,
  });
}

export async function getApiErrorMessage(response: Response, fallback: string): Promise<string> {
  try {
    const data = await response.json();
    if (typeof data?.detail === 'string') return data.detail;
    if (typeof data?.message === 'string') return data.message;
    if (typeof data?.error === 'string') return data.error;
  } catch {
    // Some responses are not JSON. Use the caller's user-facing fallback.
  }

  return fallback;
}
