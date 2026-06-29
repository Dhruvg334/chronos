import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Loader2, Calendar, CheckCircle2, AlertCircle } from "lucide-react";
import { GoogleConnectionStatus } from "@/types/api";
import { fetchAuthSession } from "@/lib/api"; // Wait, how do I make authenticated calls? We use fetch with headers.
// Actually, let's just use standard fetch since the frontend doesn't have an axios instance exposed in api.ts

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
      <Card className="mb-6">
        <CardContent className="flex items-center justify-center py-6">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="mb-6">
      <CardHeader className="pb-3 border-b">
        <CardTitle className="text-lg flex items-center gap-2">
          <Calendar className="h-5 w-5" />
          Google Calendar
        </CardTitle>
      </CardHeader>
      <CardContent className="pt-4">
        {error && (
          <div className="mb-4 p-3 bg-red-500/10 border border-red-500/20 rounded-md flex items-start gap-2 text-red-400 text-sm">
            <AlertCircle className="h-4 w-4 mt-0.5 shrink-0" />
            <p>{error}</p>
          </div>
        )}

        {status?.connected ? (
          <div className="space-y-4">
            <div className="flex items-center gap-2 text-green-500 text-sm font-medium">
              <CheckCircle2 className="h-4 w-4" />
              Connected
            </div>
            {status.email && (
              <p className="text-xs text-muted-foreground">Account: {status.email}</p>
            )}
            {status.last_synced_at && (
              <p className="text-xs text-muted-foreground">
                Last synced: {new Date(status.last_synced_at).toLocaleString()}
              </p>
            )}
            <div className="flex gap-2">
              <Button size="sm" variant="outline" onClick={handleSync} disabled={syncing}>
                {syncing && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Sync Now
              </Button>
              <Button size="sm" variant="destructive" onClick={handleDisconnect} disabled={syncing}>
                Disconnect
              </Button>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <p className="text-sm text-muted-foreground">
              Connect your Google Calendar to view real-time availability and improve focus suggestions.
            </p>
            <Button onClick={handleConnect} className="w-full">
              Connect Google Calendar
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
