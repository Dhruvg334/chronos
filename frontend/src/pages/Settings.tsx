import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import AppShell from "../components/layout/AppShell";
import {
  ErrorState,
  LoadingState,
  PageHeader,
  Surface,
} from "../components/ui/primitives";
import { apiFetch, apiUrl, getApiErrorMessage } from "../lib/api";
import type { IntegrationStatus, PlanningProfile } from "../types/api";
import { PreferenceSettings } from "../components/settings/PreferenceSettings";

const DAYS = [
  "Monday",
  "Tuesday",
  "Wednesday",
  "Thursday",
  "Friday",
  "Saturday",
  "Sunday",
];
const TIMEZONES = [
  "UTC",
  "Asia/Kolkata",
  "Asia/Singapore",
  "Europe/London",
  "America/New_York",
  "America/Los_Angeles",
  "Australia/Sydney",
];

async function loadProfile(): Promise<PlanningProfile> {
  const response = await apiFetch(apiUrl("/api/v1/settings/planning-profile"));
  if (!response.ok)
    throw new Error(
      await getApiErrorMessage(
        response,
        "Your availability could not be loaded.",
      ),
    );
  return response.json();
}

async function loadIntegrations(): Promise<IntegrationStatus[]> {
  const response = await apiFetch(apiUrl("/api/v1/settings/integrations"));
  if (!response.ok)
    throw new Error(
      await getApiErrorMessage(response, "Integration status is unavailable."),
    );
  return response.json();
}

function timeValue(value: string | null) {
  return value?.slice(0, 5) ?? "";
}

export default function Settings() {
  const queryClient = useQueryClient();
  const profileQuery = useQuery({
    queryKey: ["planning-profile"],
    queryFn: loadProfile,
  });
  const integrations = useQuery({
    queryKey: ["integration-status"],
    queryFn: loadIntegrations,
  });
  const [form, setForm] = useState<PlanningProfile | null>(null);
  const [notice, setNotice] = useState("");
  useEffect(() => {
    if (profileQuery.data) setForm(profileQuery.data);
  }, [profileQuery.data]);

  const save = useMutation({
    mutationFn: async (profile: PlanningProfile) => {
      const response = await apiFetch(
        apiUrl("/api/v1/settings/planning-profile"),
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(profile),
        },
      );
      if (!response.ok)
        throw new Error(
          await getApiErrorMessage(
            response,
            "Your availability could not be saved.",
          ),
        );
      return response.json() as Promise<PlanningProfile>;
    },
    onSuccess: async (data) => {
      setForm(data);
      setNotice("Availability saved.");
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["planning-profile"] }),
        queryClient.invalidateQueries({ queryKey: ["plan"] }),
        queryClient.invalidateQueries({ queryKey: ["today"] }),
      ]);
    },
  });
  const reset = useMutation({
    mutationFn: async () => {
      const response = await apiFetch(
        apiUrl("/api/v1/settings/planning-profile/reset"),
        { method: "POST" },
      );
      if (!response.ok)
        throw new Error(
          await getApiErrorMessage(response, "Defaults could not be restored."),
        );
      return response.json() as Promise<PlanningProfile>;
    },
    onSuccess: async (data) => {
      setForm(data);
      setNotice("Defaults restored.");
      await queryClient.invalidateQueries();
    },
  });
  const connectCalendar = useMutation({
    mutationFn: async () => {
      const response = await apiFetch(apiUrl("/api/v1/google/auth/url"));
      if (!response.ok) throw new Error(await getApiErrorMessage(response, "Google Calendar connection is unavailable."));
      return response.json() as Promise<{ auth_url: string }>;
    },
    onSuccess: ({ auth_url }) => window.location.assign(auth_url),
  });
  const disconnectCalendar = useMutation({
    mutationFn: async () => {
      const response = await apiFetch(apiUrl("/api/v1/google/disconnect"), { method: "POST" });
      if (!response.ok) throw new Error(await getApiErrorMessage(response, "Google Calendar could not be disconnected."));
    },
    onSuccess: async () => {
      setNotice("Google Calendar disconnected.");
      await Promise.all([queryClient.invalidateQueries({ queryKey: ["integration-status"] }), queryClient.invalidateQueries({ queryKey: ["plan"] }), queryClient.invalidateQueries({ queryKey: ["today"] })]);
    },
  });

  const setNumber = (key: keyof PlanningProfile, value: string) =>
    setForm((current) =>
      current ? { ...current, [key]: Number(value) } : current,
    );
  const setText = (key: keyof PlanningProfile, value: string | null) =>
    setForm((current) => (current ? { ...current, [key]: value } : current));
  const toggleDay = (day: number) =>
    setForm((current) =>
      current
        ? {
            ...current,
            available_weekdays: current.available_weekdays.includes(day)
              ? current.available_weekdays.filter((value) => value !== day)
              : [...current.available_weekdays, day].sort(),
          }
        : current,
    );

  return (
    <AppShell>
      <PageHeader
        eyebrow="Settings"
        title="Personal availability"
        description="Define when work can fit. ChronOS uses these boundaries for Today, Plan, and focus recommendations."
      />
      <div className="mx-auto max-w-4xl space-y-5">
        <Surface className="p-6">
          <h2 className="font-semibold">Calendar planning</h2>
          {integrations.isPending ? (
            <p className="mt-2 text-sm text-muted">Checking connection…</p>
          ) : (
            integrations.data?.map((item) => (
              <div key={item.provider} className="mt-3">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="rounded-full bg-accent-soft px-3 py-1 text-xs font-semibold text-accent-strong">
                    {item.state.replaceAll("_", " ")}
                  </span>
                  <span className="text-xs text-muted">Read-only</span>
                </div>
                <p className="mt-2 text-sm text-muted">{item.message}</p>
                {item.last_successful_sync && (
                  <p className="mt-1 text-xs text-faint">
                    Last successful sync{" "}
                    {new Date(item.last_successful_sync).toLocaleString()}
                  </p>
                )}
                {item.retry_available && (
                  <button
                    className="button-secondary mt-3"
                    onClick={() => integrations.refetch()}
                  >
                    Retry status
                  </button>
                )}
                {item.state === "disconnected" && (
                  <button className="button-primary mt-3" disabled={connectCalendar.isPending} onClick={() => connectCalendar.mutate()}>{connectCalendar.isPending ? "Opening…" : "Connect read-only calendar"}</button>
                )}
                {item.state === "connected" && (
                  <button className="button-secondary mt-3" disabled={disconnectCalendar.isPending} onClick={() => disconnectCalendar.mutate()}>{disconnectCalendar.isPending ? "Disconnecting…" : "Disconnect calendar"}</button>
                )}
                {(connectCalendar.isError || disconnectCalendar.isError) && <p role="alert" className="mt-2 text-sm text-danger">{(connectCalendar.error || disconnectCalendar.error)?.message}</p>}
              </div>
            ))
          )}
        </Surface>
        {profileQuery.isError ? (
          <ErrorState
            message={profileQuery.error.message}
            onRetry={() => profileQuery.refetch()}
          />
        ) : profileQuery.isPending || !form ? (
          <LoadingState label="Loading availability" />
        ) : (
          <form
            onSubmit={(event) => {
              event.preventDefault();
              setNotice("");
              save.mutate(form);
            }}
            className="space-y-5"
          >
            <Surface className="p-6">
              <h2 className="font-semibold">Available days and hours</h2>
              <div className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-4 lg:grid-cols-7">
                {DAYS.map((label, day) => (
                  <label
                    key={label}
                    className="flex items-center gap-2 rounded-lg border border-line p-3 text-sm"
                  >
                    <input
                      type="checkbox"
                      checked={form.available_weekdays.includes(day)}
                      onChange={() => toggleDay(day)}
                    />
                    {label.slice(0, 3)}
                  </label>
                ))}
              </div>
              {form.available_weekdays.length === 0 && (
                <p role="alert" className="mt-2 text-sm text-danger">
                  Choose at least one available day.
                </p>
              )}
              <div className="mt-5 grid gap-4 sm:grid-cols-3">
                <label className="label">
                  Timezone
                  <select
                    aria-label="Timezone"
                    className="field mt-1"
                    value={form.timezone}
                    onChange={(event) =>
                      setText("timezone", event.target.value)
                    }
                  >
                    {TIMEZONES.map((zone) => (
                      <option key={zone}>{zone}</option>
                    ))}
                  </select>
                </label>
                <label className="label">
                  Work start
                  <input
                    aria-label="Work start"
                    type="time"
                    required
                    className="field mt-1"
                    value={timeValue(form.working_start_time)}
                    onChange={(event) =>
                      setText("working_start_time", event.target.value)
                    }
                  />
                </label>
                <label className="label">
                  Work end
                  <input
                    aria-label="Work end"
                    type="time"
                    required
                    className="field mt-1"
                    value={timeValue(form.working_end_time)}
                    onChange={(event) =>
                      setText("working_end_time", event.target.value)
                    }
                  />
                </label>
              </div>
            </Surface>
            <Surface className="p-6">
              <h2 className="font-semibold">Capacity boundaries</h2>
              <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                <NumberField
                  label="Daily focus-minute limit"
                  value={form.daily_focus_limit_minutes}
                  min={15}
                  max={1440}
                  onChange={(value) =>
                    setNumber("daily_focus_limit_minutes", value)
                  }
                />
                <NumberField
                  label="Default focus duration"
                  value={form.default_focus_duration_minutes}
                  min={5}
                  max={180}
                  onChange={(value) =>
                    setNumber("default_focus_duration_minutes", value)
                  }
                />
                <NumberField
                  label="Transition buffer"
                  value={form.minimum_transition_buffer_minutes}
                  min={0}
                  max={120}
                  onChange={(value) =>
                    setNumber("minimum_transition_buffer_minutes", value)
                  }
                />
                <NumberField
                  label="Daily unscheduled buffer"
                  value={form.minimum_daily_unscheduled_buffer_minutes}
                  min={0}
                  max={720}
                  onChange={(value) =>
                    setNumber("minimum_daily_unscheduled_buffer_minutes", value)
                  }
                />
                <NumberField
                  label="Quick-task threshold"
                  value={form.quick_task_threshold_minutes}
                  min={1}
                  max={60}
                  onChange={(value) =>
                    setNumber("quick_task_threshold_minutes", value)
                  }
                />
              </div>
              <fieldset className="mt-5">
                <legend className="label">
                  Optional lunch or protected interval
                </legend>
                <div className="mt-2 grid gap-4 sm:grid-cols-2">
                  <label className="label">
                    Protected start
                    <input
                      aria-label="Protected start"
                      type="time"
                      className="field mt-1"
                      value={timeValue(form.protected_interval_start)}
                      onChange={(event) =>
                        setText(
                          "protected_interval_start",
                          event.target.value || null,
                        )
                      }
                    />
                  </label>
                  <label className="label">
                    Protected end
                    <input
                      aria-label="Protected end"
                      type="time"
                      className="field mt-1"
                      value={timeValue(form.protected_interval_end)}
                      onChange={(event) =>
                        setText(
                          "protected_interval_end",
                          event.target.value || null,
                        )
                      }
                    />
                  </label>
                </div>
              </fieldset>
            </Surface>
            {(save.isError || reset.isError) && (
              <p role="alert" className="text-sm text-danger">
                {(save.error || reset.error)?.message}
              </p>
            )}
            {notice && (
              <p role="status" className="text-sm text-success">
                {notice}
              </p>
            )}
            <div className="flex flex-wrap gap-3">
              <button
                className="button-primary"
                disabled={
                  save.isPending || form.available_weekdays.length === 0
                }
              >
                {save.isPending ? "Saving…" : "Save availability"}
              </button>
              <button
                type="button"
                className="button-secondary"
                disabled={reset.isPending}
                onClick={() => reset.mutate()}
              >
                {reset.isPending ? "Resetting…" : "Reset to defaults"}
              </button>
            </div>
          </form>
        )}
        <Surface className="p-6">
          <h2 className="font-semibold">Automation policy</h2>
          <p className="mt-2 text-sm leading-6 text-muted">
            Recommendation-first is active. Internal and external writes require
            approval; no external write automation is enabled.
          </p>
        </Surface>
        <PreferenceSettings />
      </div>
    </AppShell>
  );
}

function NumberField({
  label,
  value,
  min,
  max,
  onChange,
}: {
  label: string;
  value: number;
  min: number;
  max: number;
  onChange: (value: string) => void;
}) {
  return (
    <label className="label">
      {label}
      <span className="ml-1 font-normal text-muted"> (minutes)</span>
      <input
        aria-label={label}
        type="number"
        required
        min={min}
        max={max}
        className="field mt-1"
        value={value}
        onChange={(event) => onChange(event.target.value)}
      />
    </label>
  );
}
