import { useEffect, useMemo, useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { CirclePause, CirclePlay, Flag, HelpCircle, Square } from 'lucide-react';
import { apiFetch, apiUrl, getApiErrorMessage } from '../../lib/api';
import type { ActiveFocusSession } from '../../types/api';
import { Surface } from '../ui/primitives';

type NextAction = { commitment_id: string; title: string } | null;

async function mutateFocus(path: string, body?: unknown) {
  const response = await apiFetch(apiUrl(path), { method: 'POST', headers: body ? { 'Content-Type': 'application/json' } : undefined, body: body ? JSON.stringify(body) : undefined });
  if (!response.ok) throw new Error(await getApiErrorMessage(response, 'The focus session could not be updated.'));
  return response.json();
}

function formatClock(seconds: number) {
  const safe = Math.max(0, seconds);
  return `${String(Math.floor(safe / 60)).padStart(2, '0')}:${String(safe % 60).padStart(2, '0')}`;
}

export default function FocusPanel({ session, nextAction }: { session: ActiveFocusSession | null; nextAction: NextAction }) {
  const queryClient = useQueryClient();
  const [duration, setDuration] = useState(25);
  const [tick, setTick] = useState(0);
  const [stuckOptions, setStuckOptions] = useState<string[]>([]);
  const [showReflection, setShowReflection] = useState(false);
  const [showStop, setShowStop] = useState(false);
  const [notice, setNotice] = useState('');

  useEffect(() => {
    if (!session || session.status === 'paused') return;
    const timer = window.setInterval(() => setTick(value => value + 1), 1000);
    return () => window.clearInterval(timer);
  }, [session]);

  const remaining = useMemo(() => session ? Math.max(0, session.remaining_seconds - (session.status === 'active' ? tick : 0)) : 0, [session, tick]);
  const refresh = async () => { await Promise.all([queryClient.invalidateQueries({ queryKey: ['today'] }), queryClient.invalidateQueries({ queryKey: ['plan'] })]); };
  const mutation = useMutation({
    mutationFn: ({ path, body }: { path: string; body?: unknown }) => mutateFocus(path, body),
    onSuccess: async () => { setTick(0); setStuckOptions([]); await refresh(); },
  });

  if (!session) return <Surface className="p-5 sm:p-6">
    <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between"><div><p className="text-xs font-semibold uppercase tracking-[0.14em] text-accent-strong">Focus</p><h2 className="mt-1 text-lg font-semibold">Protect the next useful interval</h2><p className="mt-1 text-sm text-muted">Start with {nextAction?.title ?? 'your selected commitment'} and adjust honestly when reality changes.</p></div><div className="flex items-end gap-2"><label className="text-sm text-muted">Minutes<select aria-label="Focus duration" className="field mt-1 w-24" value={duration} onChange={event => setDuration(Number(event.target.value))}><option>25</option><option>45</option><option>60</option></select></label><button className="button-primary" disabled={!nextAction || mutation.isPending} onClick={() => nextAction && mutation.mutate({ path: '/api/v1/focus-blocks/start', body: { commitment_id: nextAction.commitment_id, duration_minutes: duration } })}>Start focus</button></div></div>
    {mutation.isError && <p role="alert" className="mt-4 text-sm text-danger">{mutation.error.message}</p>}{notice && <p role="status" className="mt-4 text-sm text-success">{notice}</p>}
  </Surface>;

  if (showReflection) return <Surface className="p-5 sm:p-6"><p className="text-xs font-semibold uppercase tracking-[0.14em] text-accent-strong">Reflection</p><h2 className="mt-1 text-xl font-semibold">Close the focus loop</h2><p className="mt-1 text-sm text-muted">Record what happened so Today can refresh with better evidence.</p><form className="mt-5 grid gap-4 sm:grid-cols-2" onSubmit={event => { event.preventDefault(); const data = new FormData(event.currentTarget); mutation.mutate({ path: `/api/v1/focus-blocks/${session.id}/complete`, body: { actual_minutes: Number(data.get('actual_minutes')), completion_status: data.get('completion_status'), energy_level: Number(data.get('energy_level')), progress_percent: Number(data.get('progress_percent')), blocker_reason: data.get('blocker_reason') || null } }, { onSuccess: () => { setShowReflection(false); setNotice('Reflection saved. Today has been refreshed.'); } }); }}>
    <label className="label">Actual minutes<input name="actual_minutes" type="number" min="0" max="720" defaultValue="20" className="field mt-1" /></label><label className="label">Completion<select name="completion_status" defaultValue="partial" className="field mt-1"><option value="partial">Partial</option><option value="completed">Completed</option></select></label><label className="label">Energy (1–5)<input name="energy_level" type="number" min="1" max="5" defaultValue="3" className="field mt-1" /></label><label className="label">Progress<input name="progress_percent" type="number" min="0" max="100" defaultValue="40" className="field mt-1" /></label><label className="label sm:col-span-2">Blocker, if any<input name="blocker_reason" className="field mt-1" /></label><div className="flex gap-2 sm:col-span-2"><button type="button" className="button-secondary" onClick={() => setShowReflection(false)}>Keep focusing</button><button className="button-primary" disabled={mutation.isPending}>Save reflection</button></div>{mutation.isError && <p role="alert" className="text-sm text-danger sm:col-span-2">{mutation.error.message}</p>}
  </form></Surface>;

  return <Surface className="p-5 sm:p-6"><div className="flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between"><div><p className="text-xs font-semibold uppercase tracking-[0.14em] text-accent-strong">{session.status === 'paused' ? 'Focus paused' : 'Focus in progress'}</p><h2 className="mt-1 text-xl font-semibold">{session.title}</h2><p className="mt-2 text-sm text-muted">Planned for {session.planned_minutes} minutes</p></div><p aria-label={`${remaining} seconds remaining`} className="font-mono text-4xl font-semibold tabular-nums">{formatClock(remaining)}</p></div>
    <div className="mt-5 flex flex-wrap gap-2">{session.status === 'active' ? <button className="button-secondary" disabled={mutation.isPending} onClick={() => mutation.mutate({ path: `/api/v1/focus-blocks/${session.id}/pause` })}><CirclePause className="mr-2 h-4 w-4" />Pause</button> : <button className="button-primary" disabled={mutation.isPending} onClick={() => mutation.mutate({ path: `/api/v1/focus-blocks/${session.id}/resume` })}><CirclePlay className="mr-2 h-4 w-4" />Resume</button>}<button className="button-secondary" disabled={mutation.isPending} onClick={() => mutation.mutate({ path: `/api/v1/focus-blocks/${session.id}/stuck` }, { onSuccess: data => setStuckOptions(data.options) })}><HelpCircle className="mr-2 h-4 w-4" />I’m stuck</button><button className="button-secondary" onClick={() => setShowReflection(true)}><Flag className="mr-2 h-4 w-4" />Finish</button><button className="button-secondary" onClick={() => setShowStop(true)}><Square className="mr-2 h-4 w-4" />Stop</button></div>
    {stuckOptions.length > 0 && <div className="mt-5 rounded-xl bg-surface-subtle p-4"><h3 className="font-medium">Choose the smallest useful adjustment</h3><ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-muted">{stuckOptions.map(option => <li key={option}>{option}</li>)}</ul></div>}
    {showStop && <form className="mt-5 flex flex-col gap-3 rounded-xl border border-line p-4 sm:flex-row sm:items-end" onSubmit={event => { event.preventDefault(); const reason = String(new FormData(event.currentTarget).get('reason') || ''); mutation.mutate({ path: `/api/v1/focus-blocks/${session.id}/skip`, body: { reason } }, { onSuccess: () => { setShowStop(false); setNotice('Focus stopped. Add a reflection when you are ready.'); } }); }}><label className="label flex-1">Why are you stopping?<input required minLength={2} name="reason" className="field mt-1" /></label><button className="button-primary" disabled={mutation.isPending}>Stop session</button></form>}
    {mutation.isError && <p role="alert" className="mt-4 text-sm text-danger">{mutation.error.message}</p>}{notice && <p role="status" className="mt-4 text-sm text-success">{notice}</p>}
  </Surface>;
}
