import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CalendarDays, Clock3, Plus, X } from "lucide-react";
import AppShell from "../components/layout/AppShell";
import {
  ErrorState,
  LoadingState,
  PageHeader,
  Surface,
} from "../components/ui/primitives";
import { apiFetch, apiUrl, getApiErrorMessage } from "../lib/api";
import { WhyThisPlan } from "../components/planning/WhyThisPlan";
import { RoutinesPanel } from "../components/planning/RoutinesPanel";
import { Link } from "react-router-dom";
import type { AdaptivePlanResponse, PlanItem, PlanResponse } from "../types/api";

function localDateValue(date: Date) {
  const offset = date.getTimezoneOffset() * 60_000;
  return new Date(date.getTime() - offset).toISOString().slice(0, 10);
}
function localDateTimeValue(date: Date) {
  const offset = date.getTimezoneOffset() * 60_000;
  return new Date(date.getTime() - offset).toISOString().slice(0, 16);
}
function dayRange(value: string) {
  const start = new Date(`${value}T00:00:00`);
  const end = new Date(start);
  end.setDate(end.getDate() + 1);
  return { start, end };
}
function calendarCapacityLabel(state: string) {
  if (state === "live") return "Live calendar plus profile";
  if (state === "cached") return "Cached calendar plus profile";
  if (state === "stale") return "Stale calendar cache plus profile";
  if (state === "unavailable") return "Calendar unavailable; using cached events or profile";
  return "Profile-only planning";
}
async function loadPlan(date: string): Promise<PlanResponse> {
  const { start, end } = dayRange(date);
  const response = await apiFetch(
    apiUrl(
      `/api/v1/plan?start_at=${encodeURIComponent(start.toISOString())}&end_at=${encodeURIComponent(end.toISOString())}`,
    ),
  );
  if (!response.ok)
    throw new Error(
      await getApiErrorMessage(response, "The plan could not be loaded."),
    );
  return response.json();
}

function TimelineItem({ item, timezone }: { item: PlanItem; timezone?: string }) {
  return (
    <article className="relative mb-4 rounded-xl border border-line bg-surface-subtle p-4 before:absolute before:-left-[31px] before:top-5 before:h-2 before:w-2 before:rounded-full before:bg-accent">
      <p className="text-xs capitalize text-muted">
        {item.start_at
          ? new Date(item.start_at).toLocaleTimeString([], {
              hour: "2-digit",
              minute: "2-digit",
              timeZone: timezone,
            })
          : "Unscheduled"}{" "}
        · {item.kind.replace("_", " ")}
      </p>
      <h3 className="mt-1 font-medium">{item.title}</h3>
      {item.end_at && (
        <p className="mt-1 text-xs text-muted">
          Until{" "}
          {new Date(item.end_at).toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
            timeZone: timezone,
          })}
        </p>
      )}
    </article>
  );
}

export default function Plan() {
  const queryClient = useQueryClient();
  const [date, setDate] = useState(localDateValue(new Date()));
  const [showForm, setShowForm] = useState(false);
  const [notice, setNotice] = useState("");
  const query = useQuery({
    queryKey: ["plan", date],
    queryFn: () => loadPlan(date),
  });
  const defaultStart = useMemo(() => {
    const { start } = dayRange(date);
    start.setHours(10, 0, 0, 0);
    return localDateTimeValue(start);
  }, [date]);
  const createBlock = useMutation({
    mutationFn: async (payload: unknown) => {
      const response = await apiFetch(apiUrl("/api/v1/plan/blocks"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!response.ok)
        throw new Error(
          await getApiErrorMessage(
            response,
            "The plan block could not be created.",
          ),
        );
      return response.json();
    },
    onSuccess: async () => {
      setNotice("Plan block created.");
      setShowForm(false);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["plan"] }),
        queryClient.invalidateQueries({ queryKey: ["today"] }),
      ]);
    },
  });
  const adaptive = useMutation({
    mutationFn: async (): Promise<AdaptivePlanResponse> => {
      const { start, end } = dayRange(date);
      const response = await apiFetch(apiUrl("/api/v1/plan/adaptive"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ start_at: start.toISOString(), end_at: end.toISOString() }),
      });
      if (!response.ok) throw new Error(await getApiErrorMessage(response, "An adaptive plan could not be prepared."));
      return response.json();
    },
  });
  const approveAdaptive = useMutation({
    mutationFn: async (proposalId: string) => {
      const response = await apiFetch(apiUrl(`/api/v1/plan/adaptive/${proposalId}/approve`), { method: "POST" });
      if (!response.ok) throw new Error(await getApiErrorMessage(response, "The proposed plan could not be approved."));
      return response.json();
    },
    onSuccess: async () => {
      setNotice("Adaptive plan approved.");
      adaptive.reset();
      await Promise.all([queryClient.invalidateQueries({ queryKey: ["plan"] }), queryClient.invalidateQueries({ queryKey: ["today"] })]);
    },
  });
  const retryCalendar = useMutation({
    mutationFn: async () => {
      const response = await apiFetch(apiUrl("/api/v1/calendar/sync"), { method: "POST" });
      if (!response.ok) throw new Error(await getApiErrorMessage(response, "Calendar sync is unavailable."));
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["plan"] }),
  });

  return (
    <AppShell>
      <PageHeader
        eyebrow="Plan"
        title="Make the work fit the time"
        description="Calendar events, focus blocks, unscheduled commitments, capacity, and buffers in one view."
        action={
          <div className="flex flex-wrap gap-2"><Link className="button-secondary" to="/week">Plan the week</Link><Link className="button-secondary" to="/projects">Projects</Link><button
            className="button-secondary"
            disabled={adaptive.isPending || !query.data?.unscheduled_commitments.length}
            onClick={() => adaptive.mutate()}
          >
            {adaptive.isPending ? "Diagnosing…" : "Suggest adaptive plan"}
          </button><button
            className="button-secondary"
            onClick={() => {
              setShowForm(true);
              setNotice("");
            }}
          >
            <Plus className="mr-2 h-4 w-4" />
            Add plan block
          </button></div>
        }
      />
      <div className="mb-5 flex flex-wrap items-end gap-3">
        <label className="label">
          Plan date
          <input
            aria-label="Plan date"
            type="date"
            className="field mt-1 w-auto"
            value={date}
            onChange={(event) => setDate(event.target.value)}
          />
        </label>
        {notice && (
          <p role="status" className="pb-2 text-sm text-success">
            {notice}
          </p>
        )}
      </div>
      {showForm && (
        <Surface className="mb-5 p-5">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">Add a plan block</h2>
            <button
              className="icon-button"
              aria-label="Close plan block form"
              onClick={() => setShowForm(false)}
            >
              <X className="h-4 w-4" />
            </button>
          </div>
          <form
            className="mt-4 grid gap-4 md:grid-cols-4"
            onSubmit={(event) => {
              event.preventDefault();
              const values = new FormData(event.currentTarget);
              createBlock.mutate({
                commitment_id: values.get("commitment_id"),
                start_at: new Date(
                  String(values.get("start_at")),
                ).toISOString(),
                duration_minutes: Number(values.get("duration_minutes")),
              });
            }}
          >
            <label className="label md:col-span-2">
              Commitment
              <select
                required
                name="commitment_id"
                className="field mt-1"
                defaultValue=""
              >
                <option value="" disabled>
                  Select a commitment
                </option>
                {query.data?.unscheduled_commitments.map((item) => (
                  <option key={item.id} value={item.commitment_id ?? item.id}>
                    {item.title}
                  </option>
                ))}
              </select>
            </label>
            <label className="label">
              Start time
              <input
                required
                name="start_at"
                type="datetime-local"
                className="field mt-1"
                defaultValue={defaultStart}
              />
            </label>
            <label className="label">
              Duration
              <select
                name="duration_minutes"
                className="field mt-1"
                defaultValue="60"
              >
                <option value="25">25 minutes</option>
                <option value="45">45 minutes</option>
                <option value="60">60 minutes</option>
                <option value="90">90 minutes</option>
              </select>
            </label>
            <div className="md:col-span-4">
              <button
                className="button-primary"
                disabled={
                  createBlock.isPending ||
                  !query.data?.unscheduled_commitments.length
                }
              >
                {createBlock.isPending ? "Checking…" : "Create block"}
              </button>
            </div>
            {createBlock.isError && (
              <p role="alert" className="text-sm text-danger md:col-span-4">
                {createBlock.error.message}
              </p>
            )}
          </form>
        </Surface>
      )}
      {adaptive.isError && <p role="alert" className="mb-5 text-sm text-danger">{adaptive.error.message}</p>}
      {approveAdaptive.isError && <p role="alert" className="mb-5 text-sm text-danger">{approveAdaptive.error.message}</p>}
      {adaptive.data && (
        <div className="mb-5 space-y-4">
          <WhyThisPlan explanation={adaptive.data.explanation} />
          <Surface className="p-5">
            <h2 className="font-semibold">{adaptive.data.recommended_plan.label}</h2>
            <p className="mt-2 text-sm text-muted">{adaptive.data.recommended_plan.summary}</p>
            <ul className="mt-3 space-y-2 text-sm">
              {adaptive.data.recommended_plan.blocks.map((block) => <li key={`${block.commitment_id}-${block.start_at}`} className="rounded-lg bg-surface-subtle p-3">{new Date(block.start_at).toLocaleString([], { timeZone: query.data?.timezone })} · {block.duration_minutes} min · {block.rationale}</li>)}
            </ul>
            <button className="button-primary mt-4" disabled={approveAdaptive.isPending} onClick={() => approveAdaptive.mutate(adaptive.data!.proposal_id)}>{approveAdaptive.isPending ? "Approving…" : "Approve this plan"}</button>
          </Surface>
        </div>
      )}
      {query.isPending ? (
        <LoadingState label="Loading the plan" />
      ) : query.isError ? (
        <ErrorState
          message={
            query.error instanceof Error
              ? query.error.message
              : "The plan could not be loaded."
          }
          onRetry={() => query.refetch()}
        />
      ) : (
        query.data && (
          <div className="grid gap-5 lg:grid-cols-[1fr_300px]">
            <Surface className="overflow-hidden">
              <div className="flex items-center justify-between border-b border-line p-5">
                <div>
                  <h2 className="font-semibold">
                    {new Date(`${date}T12:00:00`).toLocaleDateString([], {
                      weekday: "long",
                      month: "long",
                      day: "numeric",
                    })}
                  </h2>
                  <p className="mt-1 text-sm text-muted">
                    Calendar reality and protected work
                  </p>
                </div>
                <CalendarDays className="h-5 w-5 text-accent" />
              </div>
              <div className="p-5">
                <div className="relative ml-14 border-l border-line pl-6">
                  {query.data.ordered_timeline.length ? (
                    query.data.ordered_timeline.map((item) => (
                      <TimelineItem
                        key={`${item.kind}-${item.id}`}
                        item={item}
                        timezone={query.data.timezone}
                      />
                    ))
                  ) : (
                    <div className="py-12 text-center">
                      <Clock3 className="mx-auto h-6 w-6 text-faint" />
                      <h3 className="mt-3 font-medium">The day is open</h3>
                      <p className="mt-1 text-sm text-muted">
                        Add a realistic block and keep room for transitions.
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </Surface>
            <div className="space-y-5">
              <Surface className="p-5">
                <p className="text-xs font-semibold uppercase tracking-[0.14em] text-muted">
                  Remaining capacity
                </p>
                <p className="mt-3 text-2xl font-semibold">
                  {query.data.capacity.remaining_minutes} min
                </p>
                {query.data.capacity.over_capacity_minutes > 0 && (
                  <p
                    role="alert"
                    className="mt-2 text-sm font-medium text-danger"
                  >
                    Over capacity by {query.data.capacity.over_capacity_minutes}{" "}
                    minutes.
                  </p>
                )}
                <dl className="mt-3 space-y-1 text-sm text-muted">
                  <div className="flex justify-between">
                    <dt>Available focus</dt>
                    <dd>{query.data.capacity.total_available_minutes} min</dd>
                  </div>
                  <div className="flex justify-between">
                    <dt>Calendar</dt>
                    <dd>{query.data.capacity.busy_minutes} min</dd>
                  </div>
                  <div className="flex justify-between">
                    <dt>Plan blocks</dt>
                    <dd>{query.data.capacity.scheduled_minutes} min</dd>
                  </div>
                  <div className="flex justify-between">
                    <dt>Buffers</dt>
                    <dd>{query.data.capacity.buffer_minutes} min</dd>
                  </div>
                </dl>
                <p className="mt-3 rounded-lg bg-accent-soft p-3 text-xs text-accent-strong">
                  {calendarCapacityLabel(query.data.capacity.calendar_state)} · {query.data.capacity.confidence} confidence
                  {query.data.capacity.last_successful_sync && <> · synced {new Date(query.data.capacity.last_successful_sync).toLocaleString()}</>}
                </p>
                {query.data.capacity.retry_available && (
                  <button className="button-secondary mt-3" disabled={retryCalendar.isPending} onClick={() => retryCalendar.mutate()}>{retryCalendar.isPending ? "Retrying…" : "Retry calendar"}</button>
                )}
                {retryCalendar.isError && <p role="alert" className="mt-2 text-xs text-danger">{retryCalendar.error.message}</p>}
              </Surface>
              <Surface className="p-5">
                <h2 className="font-semibold">Unscheduled work</h2>
                {query.data.unscheduled_commitments.length ? (
                  <ul className="mt-3 space-y-2 text-sm">
                    {query.data.unscheduled_commitments.map((item) => (
                      <li
                        key={item.id}
                        className="rounded-lg bg-surface-subtle p-3"
                      >
                        {item.title}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="mt-2 text-sm text-muted">
                    Every active commitment in this view has a block.
                  </p>
                )}
              </Surface>
              {query.data.explanation && <WhyThisPlan explanation={query.data.explanation} />}
              <Surface className="p-5">
                <h2 className="font-semibold">Buffer guidance</h2>
                <p className="mt-2 text-sm text-muted">
                  {query.data.buffer_guidance}
                </p>
              </Surface>
            </div>
          </div>
        )
      )}
      <div className="mt-5"><RoutinesPanel /></div>
    </AppShell>
  );
}
