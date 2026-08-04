import { useEffect, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { apiFetch, apiUrl, getApiErrorMessage } from '../lib/api';
import type { PlanningProfile } from '../types/api';
import { ErrorState, LoadingState, Surface } from '../components/ui/primitives';
import { loadOnboarding } from '../lib/onboarding';

const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
const TIMEZONES = ['UTC', 'Asia/Kolkata', 'Asia/Singapore', 'Europe/London', 'America/New_York', 'America/Los_Angeles', 'Australia/Sydney'];

export default function Onboarding() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const query = useQuery({ queryKey: ['onboarding'], queryFn: loadOnboarding });
  const [form, setForm] = useState<PlanningProfile | null>(null);
  const [step, setStep] = useState(1);
  useEffect(() => { if (query.data) { setForm(query.data); setStep(query.data.onboarding_status === 'in_progress' ? query.data.onboarding_step : 1); } }, [query.data]);

  const save = useMutation({
    mutationFn: async ({ nextStep, complete }: { nextStep: number; complete: boolean }) => {
      const response = await apiFetch(apiUrl('/api/v1/settings/onboarding'), { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ ...form, onboarding_step: nextStep, complete }) });
      if (!response.ok) throw new Error(await getApiErrorMessage(response, 'Setup could not be saved.'));
      return response.json() as Promise<PlanningProfile>;
    },
    onSuccess: async (data, variables) => { setForm(data); await queryClient.invalidateQueries({ queryKey: ['onboarding'] }); if (variables.complete) navigate('/today', { replace: true }); else setStep(variables.nextStep); },
  });
  const skip = useMutation({ mutationFn: async () => { const response = await apiFetch(apiUrl('/api/v1/settings/onboarding/skip'), { method: 'POST' }); if (!response.ok) throw new Error(await getApiErrorMessage(response, 'Setup could not be skipped.')); return response.json(); }, onSuccess: async () => { await queryClient.invalidateQueries({ queryKey: ['onboarding'] }); navigate('/today', { replace: true }); } });

  if (query.isPending || !form) return <LoadingState label="Loading setup" />;
  if (query.isError) return <ErrorState message={query.error.message} onRetry={() => query.refetch()} />;
  const toggleDay = (day: number) => setForm(current => current ? { ...current, available_weekdays: current.available_weekdays.includes(day) ? current.available_weekdays.filter(item => item !== day) : [...current.available_weekdays, day].sort() } : current);
  const set = <K extends keyof PlanningProfile>(key: K, value: PlanningProfile[K]) => setForm(current => current ? { ...current, [key]: value } : current);
  const invalidWindow = form.working_end_time <= form.working_start_time || (!!form.protected_interval_start !== !!form.protected_interval_end);

  return <main className="min-h-screen bg-canvas px-4 py-8 sm:py-14"><div className="mx-auto max-w-2xl"><div className="mb-6 flex items-center justify-between"><span className="text-xl font-semibold">Chron<span className="text-accent">OS</span></span><button className="button-secondary" disabled={skip.isPending} onClick={() => skip.mutate()}>Skip for now</button></div>
    <Surface className="p-5 sm:p-8"><div aria-label={`Step ${step} of 3`} className="mb-7"><div className="flex justify-between text-sm"><span className="font-medium">Set up your planning boundaries</span><span className="text-muted">{step} of 3</span></div><div className="mt-3 h-2 overflow-hidden rounded-full bg-surface-subtle"><div className="h-full bg-accent motion-reduce:transition-none" style={{ width: `${step / 3 * 100}%` }} /></div></div>
      {step === 1 && <section><h1 className="text-2xl font-semibold">Start with your week</h1><p className="mt-2 text-sm text-muted">Choose when ChronOS may suggest work. You can change this later.</p><div className="mt-5 grid gap-4 sm:grid-cols-2"><label className="label">Timezone<select className="field mt-1" value={form.timezone} onChange={event => set('timezone', event.target.value)}>{TIMEZONES.map(zone => <option key={zone}>{zone}</option>)}</select></label><label className="label">Planning style<select className="field mt-1" value={form.planning_style} onChange={event => set('planning_style', event.target.value as PlanningProfile['planning_style'])}><option value="guided">Guided — more context</option><option value="balanced">Balanced</option><option value="minimal">Minimal — fewer prompts</option></select></label></div><fieldset className="mt-5"><legend className="label">Available weekdays</legend><div className="grid grid-cols-2 gap-2 sm:grid-cols-4">{DAYS.map((day, index) => <label key={day} className="flex min-h-11 items-center gap-2 rounded-xl border border-line p-3 text-sm"><input type="checkbox" checked={form.available_weekdays.includes(index)} onChange={() => toggleDay(index)} />{day.slice(0, 3)}</label>)}</div></fieldset></section>}
      {step === 2 && <section><h1 className="text-2xl font-semibold">Protect your working window</h1><p className="mt-2 text-sm text-muted">Lunch is optional. No calendar connection is required.</p><div className="mt-5 grid gap-4 sm:grid-cols-2"><TimeField label="Work starts" value={form.working_start_time} onChange={value => set('working_start_time', value)} /><TimeField label="Work ends" value={form.working_end_time} onChange={value => set('working_end_time', value)} /><TimeField label="Protected interval starts" value={form.protected_interval_start ?? ''} optional onChange={value => set('protected_interval_start', value || null)} /><TimeField label="Protected interval ends" value={form.protected_interval_end ?? ''} optional onChange={value => set('protected_interval_end', value || null)} /></div>{invalidWindow && <p role="alert" className="mt-3 text-sm text-danger">Use a valid work window and provide both protected interval times.</p>}</section>}
      {step === 3 && <section><h1 className="text-2xl font-semibold">Choose comfortable defaults</h1><p className="mt-2 text-sm text-muted">These guide capacity and focus; they are not performance targets.</p><div className="mt-5 grid gap-4 sm:grid-cols-2"><NumberField label="Daily focus limit" value={form.daily_focus_limit_minutes} min={15} max={1440} onChange={value => set('daily_focus_limit_minutes', value)} /><NumberField label="Default focus duration" value={form.default_focus_duration_minutes} min={5} max={180} onChange={value => set('default_focus_duration_minutes', value)} /><NumberField label="Transition buffer" value={form.minimum_transition_buffer_minutes} min={0} max={120} onChange={value => set('minimum_transition_buffer_minutes', value)} /><NumberField label="Quick-task threshold" value={form.quick_task_threshold_minutes} min={1} max={60} onChange={value => set('quick_task_threshold_minutes', value)} /></div></section>}
      {(save.isError || skip.isError) && <p role="alert" className="mt-5 text-sm text-danger">{(save.error || skip.error)?.message}</p>}
      <div className="mt-8 flex flex-wrap justify-between gap-3"><button type="button" className="button-secondary" disabled={step === 1 || save.isPending} onClick={() => setStep(value => value - 1)}>Back</button><button className="button-primary" disabled={save.isPending || form.available_weekdays.length === 0 || invalidWindow} onClick={() => save.mutate({ nextStep: Math.min(3, step + 1), complete: step === 3 })}>{save.isPending ? 'Saving…' : step === 3 ? 'Finish setup' : 'Save and continue'}</button></div>
    </Surface></div></main>;
}

function TimeField({ label, value, optional, onChange }: { label: string; value: string; optional?: boolean; onChange: (value: string) => void }) { return <label className="label">{label}{optional && <span className="font-normal"> (optional)</span>}<input aria-label={label} type="time" required={!optional} className="field mt-1" value={value.slice(0, 5)} onChange={event => onChange(event.target.value)} /></label>; }
function NumberField({ label, value, min, max, onChange }: { label: string; value: number; min: number; max: number; onChange: (value: number) => void }) { return <label className="label">{label}<span className="font-normal"> (minutes)</span><input aria-label={label} type="number" required min={min} max={max} className="field mt-1" value={value} onChange={event => onChange(Number(event.target.value))} /></label>; }
