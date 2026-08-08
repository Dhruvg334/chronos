import { useEffect, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { ArrowLeft, ArrowRight, CalendarDays, Check, Clock3, Gauge, Sparkles } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { apiFetch, apiUrl, getApiErrorMessage } from '../lib/api';
import type { PlanningProfile } from '../types/api';
import { ErrorState, LoadingState } from '../components/ui/primitives';
import { loadOnboarding } from '../lib/onboarding';

const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
const TIMEZONES = ['UTC', 'Asia/Kolkata', 'Asia/Singapore', 'Europe/London', 'America/New_York', 'America/Los_Angeles', 'Australia/Sydney'];

const steps = [
  { icon: CalendarDays, label: 'Your week', detail: 'Where planning is allowed' },
  { icon: Clock3, label: 'Your window', detail: 'When work can actually fit' },
  { icon: Gauge, label: 'Your defaults', detail: 'Comfortable planning limits' },
];

export default function Onboarding() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const query = useQuery({ queryKey: ['onboarding'], queryFn: loadOnboarding });
  const [form, setForm] = useState<PlanningProfile | null>(null);
  const [step, setStep] = useState(1);

  useEffect(() => {
    if (query.data) {
      setForm(query.data);
      setStep(query.data.onboarding_status === 'in_progress' ? query.data.onboarding_step : 1);
    }
  }, [query.data]);

  const save = useMutation({
    mutationFn: async ({ nextStep, complete }: { nextStep: number; complete: boolean }) => {
      const response = await apiFetch(apiUrl('/api/v1/settings/onboarding'), {
        method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ ...form, onboarding_step: nextStep, complete }),
      });
      if (!response.ok) throw new Error(await getApiErrorMessage(response, 'Setup could not be saved.'));
      return response.json() as Promise<PlanningProfile>;
    },
    onSuccess: async (data, variables) => {
      setForm(data);
      await queryClient.invalidateQueries({ queryKey: ['onboarding'] });
      if (variables.complete) navigate('/today', { replace: true });
      else setStep(variables.nextStep);
    },
  });

  const skip = useMutation({
    mutationFn: async () => {
      const response = await apiFetch(apiUrl('/api/v1/settings/onboarding/skip'), { method: 'POST' });
      if (!response.ok) throw new Error(await getApiErrorMessage(response, 'Setup could not be skipped.'));
      return response.json();
    },
    onSuccess: async () => { await queryClient.invalidateQueries({ queryKey: ['onboarding'] }); navigate('/today', { replace: true }); },
  });

  if (query.isPending || !form) return <main className="min-h-screen bg-canvas p-6"><LoadingState label="Loading setup" /></main>;
  if (query.isError) return <main className="min-h-screen bg-canvas p-6"><ErrorState message={query.error.message} onRetry={() => query.refetch()} /></main>;

  const toggleDay = (day: number) => setForm(current => current ? { ...current, available_weekdays: current.available_weekdays.includes(day) ? current.available_weekdays.filter(item => item !== day) : [...current.available_weekdays, day].sort() } : current);
  const set = <K extends keyof PlanningProfile>(key: K, value: PlanningProfile[K]) => setForm(current => current ? { ...current, [key]: value } : current);
  const invalidWindow = form.working_end_time <= form.working_start_time || (!!form.protected_interval_start !== !!form.protected_interval_end);

  return (
    <main className="min-h-screen bg-canvas px-4 py-5 sm:px-6 sm:py-7">
      <div className="mx-auto grid min-h-[calc(100vh-2.5rem)] max-w-6xl overflow-hidden rounded-[28px] border border-line bg-white lg:grid-cols-[330px_1fr]">
        <aside className="relative border-b border-line bg-[#F2F1ED] p-6 lg:border-b-0 lg:border-r lg:p-8">
          <div className="flex items-center justify-between lg:block">
            <span className="brand-wordmark">Chron<span className="brand-os">OS</span></span>
            <button className="button-ghost lg:hidden" disabled={skip.isPending} onClick={() => skip.mutate()}>Skip</button>
          </div>
          <div className="mt-8 hidden lg:block">
            <p className="eyebrow">Three quiet decisions</p>
            <h1 className="mt-3 text-3xl font-semibold leading-tight tracking-[-0.035em]">Tell ChronOS where planning should stop.</h1>
            <p className="mt-3 text-sm leading-6 text-muted">These are boundaries, not productivity targets. You can change every value later.</p>
          </div>
          <ol className="mt-6 grid grid-cols-3 gap-2 lg:mt-10 lg:grid-cols-1 lg:gap-1">
            {steps.map(({ icon: Icon, label, detail }, index) => {
              const current = index + 1 === step;
              const complete = index + 1 < step;
              return (
                <li key={label} className={`flex items-center gap-3 rounded-xl px-3 py-3 transition ${current ? 'bg-white text-ink' : 'text-muted'}`}>
                  <span className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg ${current ? 'bg-accent-soft text-accent-strong' : complete ? 'bg-success-soft text-success' : 'bg-white/60 text-faint'}`}>
                    {complete ? <Check className="h-4 w-4" /> : <Icon className="h-4 w-4" />}
                  </span>
                  <div className="hidden min-w-0 lg:block"><p className="text-sm font-semibold">{label}</p><p className="mt-0.5 text-xs text-muted">{detail}</p></div>
                </li>
              );
            })}
          </ol>
          <button className="button-ghost mt-auto hidden lg:inline-flex lg:absolute lg:bottom-10" disabled={skip.isPending} onClick={() => skip.mutate()}>Skip for now</button>
        </aside>

        <section className="flex items-center justify-center p-5 sm:p-8 lg:p-12">
          <div className="w-full max-w-2xl motion-enter" key={step}>
            <div className="mb-8 flex items-center justify-between">
              <div><p className="eyebrow">Setup · {step} of 3</p><div className="mt-2 flex gap-1.5" aria-label={`Step ${step} of 3`}>{[1,2,3].map(item => <span key={item} className={`h-1.5 w-12 rounded-full ${item <= step ? 'bg-accent' : 'bg-line'}`} />)}</div></div>
              <Sparkles className="h-5 w-5 text-faint" aria-hidden="true" />
            </div>

            {step === 1 && <section>
              <h2 className="text-3xl font-semibold tracking-[-0.035em]">Start with your week</h2>
              <p className="mt-2 text-sm leading-6 text-muted">Choose when ChronOS may place work and how much guidance you want.</p>
              <div className="mt-7 grid gap-4 sm:grid-cols-2">
                <label className="label">Timezone<select className="field mt-1" value={form.timezone} onChange={event => set('timezone', event.target.value)}>{TIMEZONES.map(zone => <option key={zone}>{zone}</option>)}</select></label>
                <label className="label">Planning style<select className="field mt-1" value={form.planning_style} onChange={event => set('planning_style', event.target.value as PlanningProfile['planning_style'])}><option value="guided">Guided — more context</option><option value="balanced">Balanced</option><option value="minimal">Minimal — fewer prompts</option></select></label>
              </div>
              <fieldset className="mt-6"><legend className="label">Available weekdays</legend><div className="grid grid-cols-4 gap-2 sm:grid-cols-7">{DAYS.map((day, index) => {
                const active = form.available_weekdays.includes(index);
                return <label key={day} className={`flex min-h-12 cursor-pointer items-center justify-center rounded-xl border px-2 text-sm font-medium transition ${active ? 'border-accent/30 bg-accent-soft text-accent-strong' : 'border-line bg-white text-muted hover:bg-surface-subtle'}`}><input className="sr-only" type="checkbox" checked={active} onChange={() => toggleDay(index)} />{day.slice(0, 3)}</label>;
              })}</div></fieldset>
            </section>}

            {step === 2 && <section>
              <h2 className="text-3xl font-semibold tracking-[-0.035em]">Protect your working window</h2>
              <p className="mt-2 text-sm leading-6 text-muted">Define the hours ChronOS can use. Lunch or another protected interval is optional.</p>
              <div className="mt-7 grid gap-4 sm:grid-cols-2"><TimeField label="Work starts" value={form.working_start_time} onChange={value => set('working_start_time', value)} /><TimeField label="Work ends" value={form.working_end_time} onChange={value => set('working_end_time', value)} /><TimeField label="Protected interval starts" value={form.protected_interval_start ?? ''} optional onChange={value => set('protected_interval_start', value || null)} /><TimeField label="Protected interval ends" value={form.protected_interval_end ?? ''} optional onChange={value => set('protected_interval_end', value || null)} /></div>
              {invalidWindow && <p role="alert" className="mt-4 rounded-xl bg-danger-soft px-3 py-2.5 text-sm text-danger">Use a valid work window and provide both protected interval times.</p>}
            </section>}

            {step === 3 && <section>
              <h2 className="text-3xl font-semibold tracking-[-0.035em]">Choose comfortable defaults</h2>
              <p className="mt-2 text-sm leading-6 text-muted">These values shape recommendations. They are not goals to maximize.</p>
              <div className="mt-7 grid gap-4 sm:grid-cols-2"><NumberField label="Daily focus limit" value={form.daily_focus_limit_minutes} min={15} max={1440} onChange={value => set('daily_focus_limit_minutes', value)} /><NumberField label="Default focus duration" value={form.default_focus_duration_minutes} min={5} max={180} onChange={value => set('default_focus_duration_minutes', value)} /><NumberField label="Transition buffer" value={form.minimum_transition_buffer_minutes} min={0} max={120} onChange={value => set('minimum_transition_buffer_minutes', value)} /><NumberField label="Quick-task threshold" value={form.quick_task_threshold_minutes} min={1} max={60} onChange={value => set('quick_task_threshold_minutes', value)} /></div>
            </section>}

            {(save.isError || skip.isError) && <p role="alert" className="mt-5 rounded-xl bg-danger-soft px-3 py-2.5 text-sm text-danger">{(save.error || skip.error)?.message}</p>}

            <div className="mt-9 flex items-center justify-between border-t border-line pt-5">
              <button type="button" className="button-ghost" disabled={step === 1 || save.isPending} onClick={() => setStep(value => value - 1)}><ArrowLeft className="mr-1.5 h-4 w-4" />Back</button>
              <button className="button-primary" disabled={save.isPending || form.available_weekdays.length === 0 || invalidWindow} onClick={() => save.mutate({ nextStep: Math.min(3, step + 1), complete: step === 3 })}>{save.isPending ? 'Saving…' : step === 3 ? 'Finish setup' : 'Save and continue'}{!save.isPending && step < 3 ? <ArrowRight className="ml-2 h-4 w-4" /> : null}</button>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}

function TimeField({ label, value, optional, onChange }: { label: string; value: string; optional?: boolean; onChange: (value: string) => void }) { return <label className="label">{label}{optional && <span className="font-normal text-faint"> (optional)</span>}<input aria-label={label} type="time" required={!optional} className="field mt-1" value={value.slice(0, 5)} onChange={event => onChange(event.target.value)} /></label>; }
function NumberField({ label, value, min, max, onChange }: { label: string; value: number; min: number; max: number; onChange: (value: number) => void }) { return <label className="label">{label}<span className="font-normal text-faint"> (minutes)</span><input aria-label={label} type="number" required min={min} max={max} className="field mt-1" value={value} onChange={event => onChange(Number(event.target.value))} /></label>; }
