import { useQuery } from '@tanstack/react-query';
import { ArrowRight, CheckCircle2, Clock3 } from 'lucide-react';
import { Link } from 'react-router-dom';
import AppShell from '../components/layout/AppShell';
import { StrategyRecommendationCard, type StrategyRecommendationView } from '../components/strategy/StrategyRecommendationCard';
import { EmptyState, ErrorState, LoadingState, PageHeader, Surface } from '../components/ui/primitives';
import { apiFetch, apiUrl, getApiErrorMessage } from '../lib/api';
import type { SavedCommitment } from '../types/api';

async function loadCommitments(): Promise<SavedCommitment[]> {
  const response = await apiFetch(apiUrl('/api/v1/commitments'));
  if (!response.ok) throw new Error(await getApiErrorMessage(response, 'Your plan could not be loaded.'));
  return response.json();
}

function selectNext(items: SavedCommitment[]) {
  const weights: Record<string, number> = { rescue_required: 5, critical: 4, at_risk: 3, watch: 2, stable: 1 };
  return [...items].filter(item => item.status !== 'completed').sort((a, b) => (weights[b.risk_level] ?? 0) - (weights[a.risk_level] ?? 0) || new Date(a.deadline_at ?? '2999-01-01').getTime() - new Date(b.deadline_at ?? '2999-01-01').getTime())[0];
}

function guidance(item?: SavedCommitment): StrategyRecommendationView | null {
  if (!item) return null;
  const urgent = ['rescue_required', 'critical'].includes(item.risk_level);
  if (urgent) return { title: 'Do now, then protect the remaining work', why: `${item.title} has the highest current time risk, so adding new work would make the plan less credible.`, evidence: [item.risk_level.replace('_', ' '), `${Math.max(item.estimated_minutes - item.actual_minutes, 0)} minutes remaining`], action: 'Start the next concrete step and reserve a realistic follow-up block.', tradeoff: 'Lower-priority work may need explicit deferral.', automaticChange: false };
  if (item.estimated_minutes - item.actual_minutes >= 45) return { title: 'Use a protected focus interval', why: 'The remaining work is long enough to benefit from a bounded period without switching.', evidence: [`${item.estimated_minutes - item.actual_minutes} minutes remaining`, 'no urgent recovery signal'], action: 'Choose a 45-minute interval, with pause, finish, stop, and stuck options.', tradeoff: 'The interval may split the task at an artificial boundary.', automaticChange: false };
  return null;
}

export default function Today() {
  const query = useQuery({ queryKey: ['commitments'], queryFn: loadCommitments });
  const items = query.data ?? [];
  const next = selectNext(items);
  const recommendation = guidance(next);

  return <AppShell><PageHeader eyebrow="Today" title="A realistic day, at a glance" description="See what matters, choose the next action, and adjust only when reality requires it." action={<Link className="button-secondary" to="/inbox">Capture something</Link>} />
    {query.isPending ? <LoadingState label="Loading today’s plan" /> : query.isError ? <ErrorState message={query.error instanceof Error ? query.error.message : 'Your plan could not be loaded.'} onRetry={() => query.refetch()} /> : items.length === 0 ? <EmptyState title="Nothing is competing for your attention" message="Capture the commitments on your mind, then return here for a realistic next action." action={<Link className="button-primary" to="/inbox">Open Inbox</Link>} /> : <div className="space-y-5">
      <Surface className="p-5 sm:p-6"><div className="flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between"><div><div className="flex items-center gap-2 text-sm font-medium text-success"><CheckCircle2 className="h-4 w-4" />{items.filter(item => ['critical','rescue_required'].includes(item.risk_level)).length ? 'Plan needs one decision' : 'Plan is workable'}</div><p className="mt-3 text-sm text-muted">Next meaningful action</p><h2 className="mt-1 text-2xl font-semibold">{next?.title}</h2><p className="mt-2 text-sm text-muted">{next?.description || 'Define the smallest visible step that moves this commitment forward.'}</p></div><button className="button-primary shrink-0">Start focus <ArrowRight className="ml-2 h-4 w-4" /></button></div></Surface>
      <div className="grid gap-5 lg:grid-cols-[1.25fr_0.75fr]"><Surface className="p-5 sm:p-6"><div className="mb-5 flex items-center justify-between"><h2 className="text-lg font-semibold">Ordered plan</h2><Link className="text-sm font-medium text-accent-strong hover:underline" to="/plan">Open Plan</Link></div><ol className="space-y-1">{items.slice(0, 4).map((item, index) => <li key={item.id} className="flex items-center gap-4 rounded-xl px-3 py-3 hover:bg-surface-subtle"><span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-accent-soft text-xs font-semibold text-accent-strong">{index + 1}</span><div className="min-w-0 flex-1"><p className="truncate font-medium">{item.title}</p><p className="mt-0.5 flex items-center gap-1.5 text-xs text-muted"><Clock3 className="h-3.5 w-3.5" />{Math.max(item.estimated_minutes - item.actual_minutes, 0)} minutes remaining</p></div><span className="text-xs capitalize text-muted">{item.risk_level.replace('_', ' ')}</span></li>)}</ol></Surface>
      <Surface className="p-5 sm:p-6"><p className="text-xs font-semibold uppercase tracking-[0.14em] text-muted">Attention</p><p className="mt-3 text-3xl font-semibold">{items.filter(item => ['critical','rescue_required','at_risk'].includes(item.risk_level)).length}</p><p className="mt-1 text-sm text-muted">commitments may need a decision or a smaller scope.</p></Surface></div>
      {recommendation && <StrategyRecommendationCard recommendation={recommendation} />}
    </div>}
  </AppShell>;
}
