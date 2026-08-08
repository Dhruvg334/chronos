import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { AlertTriangle, ArrowUpRight, CheckCircle2, Clock3 } from 'lucide-react';
import { Link } from 'react-router-dom';
import FocusPanel from '../components/focus/FocusPanel';
import AppShell from '../components/layout/AppShell';
import { WhyThisPlan } from '../components/planning/WhyThisPlan';
import { RecoveryDialog } from '../components/recovery/RecoveryDialog';
import { StrategyRecommendationCard } from '../components/strategy/StrategyRecommendationCard';
import { EmptyState, ErrorState, LoadingState, PageHeader, Surface } from '../components/ui/primitives';
import { apiFetch, apiUrl, getApiErrorMessage } from '../lib/api';
import type { TodayResponse } from '../types/api';

async function loadToday(): Promise<TodayResponse> {
  const response = await apiFetch(apiUrl('/api/v1/today'));
  if (!response.ok) throw new Error(await getApiErrorMessage(response, 'Your day could not be loaded.'));
  return response.json();
}

export default function Today() {
  const query = useQuery({ queryKey: ['today'], queryFn: loadToday, refetchInterval: data => data.state.data?.active_focus_session?.status === 'active' ? 30_000 : false });
  const [showRecovery, setShowRecovery] = useState(false);
  const data = query.data;

  return (
    <AppShell>
      <PageHeader eyebrow="Today" title="A realistic day, at a glance" description="See what matters, choose the next action, and adjust only when reality requires it." action={<Link className="button-secondary" to="/inbox">Capture something</Link>} />

      {query.isPending ? <LoadingState label="Loading today’s plan" /> :
       query.isError ? <ErrorState message={query.error instanceof Error ? query.error.message : 'Your day could not be loaded.'} onRetry={() => query.refetch()} /> :
       !data || data.status === 'empty' ? <EmptyState title="Your day is ready for a first decision" message="Capture one commitment or make a small plan. ChronOS will keep the surface quiet until there is something useful to show." action={<Link className="button-primary" to="/inbox">Capture the first item</Link>} /> :
       <div className="space-y-7">
         <section className="grid gap-5 border-b border-line pb-7 lg:grid-cols-[1fr_auto] lg:items-end">
           <div className="min-w-0">
             <div className="flex items-center gap-2 text-sm font-medium">
               <span className={`inline-flex h-7 w-7 items-center justify-center rounded-full ${data.status === 'attention' ? 'bg-danger-soft text-danger' : 'bg-success-soft text-success'}`}>{data.status === 'attention' ? <AlertTriangle className="h-3.5 w-3.5" /> : <CheckCircle2 className="h-3.5 w-3.5" />}</span>
               <span className="text-muted">{data.status_message}</span>
             </div>
             <p className="mt-6 text-xs font-semibold uppercase tracking-[0.15em] text-faint">Next meaningful action</p>
             <h2 className="mt-2 max-w-3xl text-3xl font-semibold leading-tight tracking-[-0.035em] sm:text-4xl">{data.next_action?.title}</h2>
             {(data.next_action?.project || data.next_action?.outcome) && <p className="mt-2 text-sm font-medium text-accent-strong">{data.next_action.project?.title}{data.next_action.project && data.next_action.outcome ? ' · ' : ''}{data.next_action.outcome?.title}</p>}
             {data.next_action?.detail && <p className="mt-3 max-w-2xl text-sm leading-6 text-muted">{data.next_action.detail}</p>}
           </div>
           <Link to="/plan" className="button-ghost justify-self-start lg:justify-self-end">Open Plan<ArrowUpRight className="ml-1.5 h-4 w-4" /></Link>
         </section>

         <FocusPanel session={data.active_focus_session} nextAction={data.next_action} durationOptions={data.focus_duration_options} />

         <section>
           <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
             <div><p className="eyebrow">Execution</p><h2 className="mt-1 text-xl font-semibold tracking-[-0.025em]">Today’s plan</h2></div>
             {(data.attention_count + data.pending_approval_count) > 0 && <span className="rounded-full bg-surface-subtle px-3 py-1 text-xs font-medium text-muted">{data.attention_count + data.pending_approval_count} need attention</span>}
           </div>
           {data.ordered_plan.length ? (
             <ol className="divide-y divide-line border-y border-line">
               {data.ordered_plan.map((item, index) => (
                 <li key={item.id} className="grid grid-cols-[34px_1fr_auto] items-center gap-3 py-3.5">
                   <span className="text-xs font-semibold tabular-nums text-faint">{String(index + 1).padStart(2, '0')}</span>
                   <div className="min-w-0"><p className="truncate text-sm font-medium sm:text-base">{item.title}</p></div>
                   <p className="flex items-center gap-1.5 text-xs capitalize text-muted"><Clock3 className="h-3.5 w-3.5" />{item.status.replaceAll('_', ' ')}</p>
                 </li>
               ))}
             </ol>
           ) : <div className="rounded-2xl border border-dashed border-line bg-white/50 p-5"><p className="text-sm text-muted">Nothing is planned for today yet.</p><Link className="button-primary mt-3" to="/plan">Make a small plan</Link></div>}
         </section>

         <div className="grid gap-5 lg:grid-cols-2">
           {data.strategy_recommendation && <StrategyRecommendationCard recommendation={data.strategy_recommendation} />}
           {data.explanation && <details className="rounded-2xl border border-line bg-white p-5"><summary className="cursor-pointer font-medium">Why this plan?</summary><div className="mt-4"><WhyThisPlan explanation={data.explanation} /></div></details>}
         </div>

         {!!data.routines_due?.length && <Surface className="p-5 sm:p-6"><div className="flex items-center justify-between"><div><p className="eyebrow">Due today</p><h2 className="mt-1 text-lg font-semibold">Routines</h2></div><Link className="text-sm font-medium text-accent-strong" to="/plan">Manage in Plan</Link></div><ul className="mt-4 divide-y divide-line">{data.routines_due.map(routine => <li key={routine.id} className="flex items-center justify-between gap-4 py-3 first:pt-0 last:pb-0"><span className="font-medium">{routine.title}</span><span className="text-sm text-muted">{routine.preferred_time || 'Flexible'} · {routine.duration_minutes} min</span></li>)}</ul></Surface>}

         {data.recovery && <div className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-accent/15 bg-accent-soft/45 p-5"><div><p className="font-semibold">The plan may need a calm adjustment</p><p className="mt-1 text-sm text-muted">{data.recovery.what_changed}</p></div><button className="button-secondary" onClick={() => setShowRecovery(true)}>Review recovery</button></div>}
         {showRecovery && data.recovery && <RecoveryDialog recovery={data.recovery} onClose={() => setShowRecovery(false)} />}
       </div>}
    </AppShell>
  );
}
