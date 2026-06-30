import { useEffect, useState } from 'react';
import { AlertCircle, Calendar, CheckCircle2, Loader2 } from 'lucide-react';
import { apiFetch, apiUrl, getApiErrorMessage } from '../../lib/api';
import type { GoogleConnectionStatus } from '../../types/api';

export function CalendarConnection() {
  const [status, setStatus] = useState<GoogleConnectionStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchStatus = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await apiFetch(apiUrl('/api/v1/google/connection'));
      if (!res.ok) {
        throw new Error(await getApiErrorMessage(res, 'Could not load Google Calendar connection.'));
      }
      setStatus(await res.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not load Google Calendar connection.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();

    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('calendar_connected') === 'true') {
      window.history.replaceState({}, document.title, window.location.pathname);
      fetchStatus();
    } else if (urlParams.get('calendar_error')) {
      setError('Google Calendar could not be connected. Please try again.');
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  }, []);

  const handleConnect = async () => {
    try {
      setError(null);
      const res = await apiFetch(apiUrl('/api/v1/google/auth/url'));
      if (!res.ok) {
        throw new Error(await getApiErrorMessage(res, 'Could not start Google Calendar connection.'));
      }
      const data = await res.json();
      if (!data?.auth_url) throw new Error('Google Calendar connection URL was missing.');
      window.location.href = data.auth_url;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not start Google Calendar connection.');
    }
  };

  const handleSync = async () => {
    try {
      setSyncing(true);
      setError(null);
      const res = await apiFetch(apiUrl('/api/v1/calendar/sync'), { method: 'POST' });
      if (!res.ok) {
        throw new Error(await getApiErrorMessage(res, 'Could not sync Google Calendar.'));
      }
      await fetchStatus();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not sync Google Calendar.');
    } finally {
      setSyncing(false);
    }
  };

  const handleDisconnect = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await apiFetch(apiUrl('/api/v1/google/disconnect'), { method: 'POST' });
      if (!res.ok) {
        throw new Error(await getApiErrorMessage(res, 'Could not disconnect Google Calendar.'));
      }
      await fetchStatus();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not disconnect Google Calendar.');
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="mb-6 rounded-xl border border-warm-border bg-white shadow-sm">
        <div className="flex items-center justify-center py-6">
          <Loader2 className="h-6 w-6 animate-spin text-text-muted" />
        </div>
      </div>
    );
  }

  return (
    <div className="mb-6 rounded-xl border border-warm-border bg-white shadow-sm">
      <div className="border-b border-warm-border p-4 pb-3">
        <h3 className="flex items-center gap-2 text-lg font-bold text-text-primary">
          <Calendar className="h-5 w-5" />
          Google Calendar
        </h3>
      </div>
      <div className="p-4 pt-4">
        {error && (
          <div className="mb-4 flex items-start gap-2 rounded-md border border-risk-atrisk bg-red-50 p-3 text-sm text-risk-atrisk">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
            <p>{error}</p>
          </div>
        )}

        {status?.connected ? (
          <div className="space-y-4">
            <div className="flex items-center gap-2 text-sm font-medium text-risk-stable">
              <CheckCircle2 className="h-4 w-4" />
              Connected
            </div>
            {status.email && <p className="text-xs text-text-muted">Account: {status.email}</p>}
            {status.last_synced_at && (
              <p className="text-xs text-text-muted">
                Last synced: {new Date(status.last_synced_at).toLocaleString()}
              </p>
            )}
            <div className="flex gap-2">
              <button
                onClick={handleSync}
                disabled={syncing}
                className="flex items-center gap-1 rounded border border-warm-border px-3 py-1.5 text-sm font-semibold text-text-secondary transition-colors hover:bg-warm-ivory disabled:opacity-50"
              >
                {syncing && <Loader2 className="h-4 w-4 animate-spin" />}
                Sync now
              </button>
              <button
                onClick={handleDisconnect}
                disabled={syncing}
                className="rounded border border-risk-atrisk bg-transparent px-3 py-1.5 text-sm font-semibold text-risk-atrisk transition-colors hover:bg-red-50 disabled:opacity-50"
              >
                Disconnect
              </button>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <p className="text-sm text-text-muted">
              Connect Google Calendar to let ChronOS read availability and improve focus suggestions.
            </p>
            <button
              onClick={handleConnect}
              className="w-full rounded-lg bg-text-primary px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-black"
            >
              Connect Google Calendar
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
