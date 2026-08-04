import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { AlertTriangle, CheckCircle2, Clock3 } from 'lucide-react';
import { Link } from 'react-router-dom';
import FocusPanel from '../components/focus/FocusPanel';
import AppShell from '../components/layout/AppShell';
import { WhyThisPlan } from '../components/planning/WhyThisPlan';
import { RecoveryDialog } from '../components/recovery/RecoveryDialog';
import { StrategyRecommendationCard } from '../components/strategy/StrategyRecommendationCard';
import { EmptyState, ErrorState, LoadingState, PageHeader, Surface } from '../components/ui/primitives';
import { apiFetch, apiUrl, getApiErrorMessage } from '../lib/api';
import type { TodayResponse } from '../types/api';

async function loadToday(): Promise<TodayResponse> { const response = await apiFetch(apiUrl('/api/v1/today')); if (!response.ok) throw new Error(await getApiErrorMessage(response, 'Your day could not be loaded.')); return response.json(); }

export default function Today() {
  const query = useQuery({ queryKey: ['today'], queryFn: loadToday, refetchInterval: data => data.state.data?.active_focus_session?.status === 'active' ? 30_000 : false });
  const [showRecovery, setShowRecovery] = useState(false); const data = query.data;
  return <AppShell><PageHeader eyebrow="Today" title="A realistic day, at a glance" description="See what matters, choose the next action, and adjust only when reality requires it." action={<Link className="button-secondary" to="/inbox">Capture something</Link>} />
    {query.isPending ? <LoadingState label="Loading today’s plan" /> : query.isError ? <ErrorState message={query.error instanceof Error ? query.error.message : 'Your day could not be loaded.'} onRetry={() => query.refetch()} /> : !data || data.status === 'empty' ? <EmptyState title="Your day is ready for a first decision" message="Capture one commitment or make a small plan. ChronOS will keep the surface quiet until there is something useful to show." action={<Link className="button-primary" to="/inbox">Capture the first item</Link>} /> : <div className="space-y-5">
      <Surface className="p-5 sm:p-6"><div className="flex items-start gap-3"><div className={`rounded-full p-2 ${data.status === 'attention' ? 'bg-danger-soft text-danger' : 'bg-success-soft text-success'}`}>{data.status === 'attention' ? <AlertTriangle className="h-4 w-4" /> : <CheckCircle2 className="h-4 w-4" />}</div><div className="min-w-0"><p className="font-medium">{data.status_message}</p><p className="mt-3 text-sm text-muted">Next meaningful action</p><h2 className="mt-1 text-2xl font-semibold">{data.next_action?.title}</h2>{(data.next_action?.project || data.next_action?.outcome) && <p className="mt-1 text-sm font-medium text-accent-strong">{data.next_action.project?.title}{data.next_action.project && data.next_action.outcome ? ' · ' : ''}{data.next_action.outcome?.title}</p>}<p className="mt-2 text-sm text-muted">{data.next_action?.detail}</p></div></div></Surface>
      <FocusPanel session={data.active_focus_session} nextAction={data.next_action} durationOptions={data.focus_duration_options} />
      <Surface className="p-5 sm:p-6"><div className="mb-4 flex flex-wrap items-center justify-between gap-3"><h2 className="text-lg font-semibold">Today’s plan</h2><div className="flex items-center gap-3"><span className="rounded-full bg-surface-subtle px-3 py-1 text-xs text-muted">{data.attention_count + data.pending_approval_count} need attention</span><Link className="text-sm font-medium text-accent-strong hover:underline" to="/plan">Open Plan</Link></div></div>{data.ordered_plan.length ? <ol className="space-y-1">{data.ordered_plan.map((item, index) => <li key={item.id} className="flex items-center gap-4 rounded-xl px-3 py-3"><span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-accent-soft text-xs font-semibold text-accent-strong">{index + 1}</span><div className="min-w-0 flex-1"><p className="truncate font-medium">{item.title}</p><p className="mt-0.5 flex items-center gap-1.5 text-xs capitalize text-muted"><Clock3 className="h-3.5 w-3.5" />{item.status.replaceAll('_', ' ')}</p></div></li>)}</ol> : <div><p className="text-sm text-muted">Nothing is planned for today yet.</p><Link className="button-primary mt-3" to="/plan">Make a small plan</Link></div>}</Surface>
      {data.strategy_recommendation && <StrategyRecommendationCard recommendation={data.strategy_recommendation} />}
      {data.explanation && <details className="surface p-5"><summary className="cursor-pointer font-medium">Why this plan?</summary><div className="mt-4"><WhyThisPlan explanation={data.explanation} /></div></details>}
      {!!data.routines_due?.length && <Surface className="p-5 sm:p-6"><div className="flex items-center justify-between"><div><p className="text-xs font-semibold uppercase tracking-[0.14em] text-muted">Due today</p><h2 className="mt-1 text-lg font-semibold">Routines</h2></div><Link className="text-sm font-medium text-accent-strong" to="/plan">Manage in Plan</Link></div><ul className="mt-3 space-y-2">{data.routines_due.map(routine => <li key={routine.id} className="rounded-lg bg-surface-subtle p-3"><span className="font-medium">{routine.title}</span><span className="ml-2 text-sm text-muted">{routine.preferred_time || 'Flexible'} · {routine.duration_minutes} min</span></li>)}</ul></Surface>}
      {data.recovery && <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-line bg-surface-subtle p-4"><div><p className="font-medium">The plan may need a calm adjustment</p><p className="mt-1 text-sm text-muted">{data.recovery.what_changed}</p></div><button className="button-secondary" onClick={() => setShowRecovery(true)}>Review recovery</button></div>}
      {showRecovery && data.recovery && <RecoveryDialog recovery={data.recovery} onClose={() => setShowRecovery(false)} />}
    </div>}
  </AppShell>;
}
