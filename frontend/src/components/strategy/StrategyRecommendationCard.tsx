import { Lightbulb, ShieldCheck } from 'lucide-react';
import type { StrategyRecommendation } from '../../types/api';

export function StrategyRecommendationCard({ recommendation }: { recommendation: StrategyRecommendation }) {
  return <section aria-labelledby="strategy-heading" className="surface-subtle p-5">
    <div className="flex items-start gap-3"><div className="rounded-lg bg-accent-soft p-2 text-accent-strong"><Lightbulb className="h-4 w-4" /></div><div className="min-w-0 flex-1"><p className="text-xs font-semibold uppercase tracking-[0.14em] text-accent-strong">Planning guidance · {recommendation.confidence} confidence</p><h2 id="strategy-heading" className="mt-1 text-lg font-semibold">{recommendation.title}</h2></div></div>
    <p className="mt-4 text-sm leading-6 text-muted">{recommendation.why}</p>
    <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2"><div><dt className="font-medium text-ink">Evidence</dt><dd className="mt-1 text-muted">{recommendation.evidence.join(' · ')}</dd></div><div><dt className="font-medium text-ink">Trade-off</dt><dd className="mt-1 text-muted">{recommendation.tradeoff}</dd></div></dl>
    <div className="mt-4 flex flex-col gap-3 border-t border-line pt-4 sm:flex-row sm:items-center sm:justify-between"><p className="font-medium">{recommendation.action}</p><span className="inline-flex shrink-0 items-center gap-1.5 text-xs text-muted"><ShieldCheck className="h-4 w-4" />No automatic changes</span></div>
  </section>;
}
