import { useState, useEffect } from 'react';
import { Loader2, Calendar, CheckCircle2, AlertCircle } from "lucide-react";
import { apiFetch as fetch } from "../../lib/api";
import type { GoogleConnectionStatus } from "../../types/api";

export function CalendarConnection() {
  const [status, setStatus] = useState<GoogleConnectionStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  const fetchStatus = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await fetch(`${API_URL}/api/v1/google/connection`, {
        headers: { 'Authorization': `Bearer dev-mock-token` } // Hardcoded for hackathon MVP or ideally from a provider
      });
      if (!res.ok) throw new Error('Failed to fetch connection status');
      const data = await res.json();
      setStatus(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    
    // Check if we just redirected back with a success/error query param
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('calendar_connected') === 'true') {
        // Clear the param from URL
        window.history.replaceState({}, document.title, window.location.pathname);
    } else if (urlParams.get('calendar_error')) {
        setError("Failed to connect Google Calendar.");
        window.history.replaceState({}, document.title, window.location.pathname);
    }
  }, []);

  const handleConnect = async () => {
    try {
      const res = await fetch(`${API_URL}/api/v1/google/auth/url`, {
        headers: { 'Authorization': `Bearer dev-mock-token` }
      });
      if (!res.ok) throw new Error('Failed to get auth URL');
      const data = await res.json();
      window.location.href = data.auth_url;
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleSync = async () => {
    try {
      setSyncing(true);
      setError(null);
      const res = await fetch(`${API_URL}/api/v1/calendar/sync`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer dev-mock-token` }
      });
      if (!res.ok) throw new Error('Failed to sync calendar');
      await fetchStatus();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setSyncing(false);
    }
  };

  const handleDisconnect = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API_URL}/api/v1/google/disconnect`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer dev-mock-token` }
      });
      if (!res.ok) throw new Error('Failed to disconnect calendar');
      await fetchStatus();
    } catch (err: any) {
      setError(err.message);
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="mb-6 bg-white border border-[#E5E0D8] rounded-xl shadow-sm">
        <div className="flex items-center justify-center py-6">
          <Loader2 className="h-6 w-6 animate-spin text-[#7A7771]" />
        </div>
      </div>
    );
  }

  return (
    <div className="mb-6 bg-white border border-[#E5E0D8] rounded-xl shadow-sm">
      <div className="pb-3 border-b border-[#E5E0D8] p-4">
        <h3 className="text-lg font-bold text-[#2C2B29] flex items-center gap-2">
          <Calendar className="h-5 w-5" />
          Google Calendar
        </h3>
      </div>
      <div className="p-4 pt-4">
        {error && (
          <div className="mb-4 p-3 bg-[#FFF5F5] border border-[#993333] rounded-md flex items-start gap-2 text-[#993333] text-sm">
            <AlertCircle className="h-4 w-4 mt-0.5 shrink-0" />
            <p>{error}</p>
          </div>
        )}

        {status?.connected ? (
          <div className="space-y-4">
            <div className="flex items-center gap-2 text-[#3D663D] text-sm font-medium">
              <CheckCircle2 className="h-4 w-4" />
              Connected
            </div>
            {status.email && (
              <p className="text-xs text-[#7A7771]">Account: {status.email}</p>
            )}
            {status.last_synced_at && (
              <p className="text-xs text-[#7A7771]">
                Last synced: {new Date(status.last_synced_at).toLocaleString()}
              </p>
            )}
            <div className="flex gap-2">
              <button 
                onClick={handleSync} 
                disabled={syncing}
                className="px-3 py-1.5 border border-[#D1CCC2] text-[#4A4844] text-sm font-semibold rounded hover:bg-[#FAF9F6] transition-colors flex items-center gap-1 disabled:opacity-50"
              >
                {syncing && <Loader2 className="h-4 w-4 animate-spin" />}
                Sync Now
              </button>
              <button 
                onClick={handleDisconnect} 
                disabled={syncing}
                className="px-3 py-1.5 bg-transparent border border-[#993333] text-[#993333] text-sm font-semibold rounded hover:bg-[#FFF5F5] transition-colors disabled:opacity-50"
              >
                Disconnect
              </button>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <p className="text-sm text-[#7A7771]">
              Connect your Google Calendar to view real-time availability and improve focus suggestions.
            </p>
            <button 
              onClick={handleConnect} 
              className="w-full px-4 py-2 bg-[#2C2B29] text-white text-sm font-semibold rounded-lg hover:bg-black transition-colors"
            >
              Connect Google Calendar
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
