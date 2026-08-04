import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { Lightbulb, ShieldCheck } from 'lucide-react';
import { apiFetch, apiUrl, getApiErrorMessage } from '../../lib/api';
import type { StrategyRecommendation } from '../../types/api';

type FeedbackAction = 'useful' | 'not_useful' | 'used' | 'dismissed';

export function StrategyRecommendationCard({ recommendation }: { recommendation: StrategyRecommendation }) {
  const [dismissed, setDismissed] = useState(false);
  const [notice, setNotice] = useState('');
  const feedback = useMutation({
    mutationFn: async (userAction: FeedbackAction) => {
      const response = await apiFetch(apiUrl('/api/v1/recommendations/feedback'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          recommendation_type: 'strategy',
          recommendation_key: recommendation.strategy,
          context_summary: {
            surface: 'today',
            strategy: recommendation.strategy,
            confidence: recommendation.confidence,
          },
          user_action: userAction,
        }),
      });
      if (!response.ok) {
        throw new Error(await getApiErrorMessage(response, 'Feedback could not be saved.'));
      }
      return userAction;
    },
    onSuccess: (action) => {
      if (action === 'dismissed') setDismissed(true);
      else setNotice(action === 'used' ? 'Marked as used.' : 'Thanks — feedback saved.');
    },
  });

  if (dismissed) {
    return <section className="surface-subtle p-4">
      <p className="text-sm text-muted">Guidance dismissed.</p>
      <button className="button-secondary mt-3" onClick={() => setDismissed(false)}>Show it again</button>
    </section>;
  }

  return <section aria-labelledby="strategy-heading" className="surface-subtle p-5">
    <div className="flex items-start gap-3">
      <div className="rounded-lg bg-accent-soft p-2 text-accent-strong"><Lightbulb className="h-4 w-4" /></div>
      <div className="min-w-0 flex-1">
        <p className="text-xs font-semibold uppercase tracking-[0.14em] text-accent-strong">Planning guidance · {recommendation.confidence} confidence</p>
        <h2 id="strategy-heading" className="mt-1 text-lg font-semibold">{recommendation.title}</h2>
      </div>
    </div>
    <p className="mt-4 text-sm leading-6 text-muted">{recommendation.why}</p>
    <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2">
      <div><dt className="font-medium text-ink">Evidence</dt><dd className="mt-1 text-muted">{recommendation.evidence.join(' · ')}</dd></div>
      <div><dt className="font-medium text-ink">Trade-off</dt><dd className="mt-1 text-muted">{recommendation.tradeoff}</dd></div>
    </dl>
    <div className="mt-4 flex flex-col gap-3 border-t border-line pt-4 sm:flex-row sm:items-center sm:justify-between">
      <p className="font-medium">{recommendation.action}</p>
      <span className="inline-flex shrink-0 items-center gap-1.5 text-xs text-muted"><ShieldCheck className="h-4 w-4" />No automatic changes</span>
    </div>
    <div className="mt-4 flex flex-wrap items-center gap-2" aria-label="Recommendation feedback">
      <button className="button-secondary" disabled={feedback.isPending} onClick={() => feedback.mutate('useful')}>Useful</button>
      <button className="button-secondary" disabled={feedback.isPending} onClick={() => feedback.mutate('not_useful')}>Not useful</button>
      <button className="button-secondary" disabled={feedback.isPending} onClick={() => feedback.mutate('used')}>I used this</button>
      <button className="px-3 py-2 text-sm font-medium text-muted hover:text-ink" disabled={feedback.isPending} onClick={() => feedback.mutate('dismissed')}>Dismiss</button>
    </div>
    {notice && <p role="status" className="mt-3 text-sm text-success">{notice}</p>}
    {feedback.isError && <p role="alert" className="mt-3 text-sm text-danger">{feedback.error.message}</p>}
  </section>;
}
