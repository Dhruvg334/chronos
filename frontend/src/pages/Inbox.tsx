import { useMutation } from '@tanstack/react-query';
import { ArrowRight, RotateCcw } from 'lucide-react';
import { useState } from 'react';
import AppShell from '../components/layout/AppShell';
import { ExtractionReview } from '../components/intake/ExtractionReview';
import { ExternalProposals } from '../components/intake/ExternalProposals';
import { PageHeader, Surface } from '../components/ui/primitives';
import { apiFetch, apiUrl, getApiErrorMessage } from '../lib/api';
import type { IntakeResponse } from '../types/api';

const example = 'Finish the authentication regression fix before tomorrow afternoon, review the deployment notes, prepare slides for Monday, attend a team call at 4 PM, and submit my database assignment by Tuesday morning.';

async function extract(text: string): Promise<IntakeResponse> { const response = await apiFetch(apiUrl('/api/v1/ai/intake'), { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ text }) }); if (!response.ok) throw new Error(await getApiErrorMessage(response, 'ChronOS could not review this capture.')); return response.json(); }

export default function Inbox() {
  const [text, setText] = useState('');
  const [data, setData] = useState<IntakeResponse | null>(null);
  const [saved, setSaved] = useState(false);
  const mutation = useMutation({ mutationFn: extract, onSuccess: result => setData(result) });
  if (data) return <AppShell><PageHeader eyebrow="Inbox" title="Review only what needs judgment" description="Confirm uncertain details and approve only the drafts you want to save." /><ExtractionReview agentRunId={data.agent_run_id} initialDrafts={data.drafts} onComplete={() => { setData(null); setText(''); setSaved(true); }} /></AppShell>;
  return <AppShell><PageHeader eyebrow="Inbox" title="Capture what’s on your mind" description="Start with plain language. ChronOS prepares reviewable drafts and keeps uncertainty visible." /><ExternalProposals />
    <Surface className="mx-auto max-w-3xl p-5 sm:p-7"><label className="label" htmlFor="capture">Commitments, tasks, meetings, or loose ends</label><textarea id="capture" className="field min-h-44 resize-y text-base leading-7" value={text} onChange={event => setText(event.target.value)} placeholder="For example: I need to finish the auth fix before tomorrow afternoon…" />
      <div className="mt-3 flex flex-col gap-3 text-sm sm:flex-row sm:items-center sm:justify-between"><button className="text-left font-medium text-accent-strong hover:underline" onClick={() => setText(example)}>Use an example</button><button className="button-primary" disabled={!text.trim() || mutation.isPending} onClick={() => mutation.mutate(text)}>{mutation.isPending ? 'Reviewing…' : 'Review capture'}<ArrowRight className="ml-2 h-4 w-4" /></button></div>
      {mutation.isError && <div role="alert" className="mt-4 flex items-start justify-between gap-4 rounded-xl border border-danger/30 bg-danger-soft p-4 text-sm text-danger"><span>{mutation.error instanceof Error ? mutation.error.message : 'ChronOS could not review this capture.'}</span><button className="inline-flex shrink-0 items-center gap-1 font-semibold" onClick={() => mutation.mutate(text)}><RotateCcw className="h-3.5 w-3.5" />Retry</button></div>}
      {saved && <p role="status" className="mt-4 rounded-xl bg-success-soft p-4 text-sm text-success">Approved commitments were saved. Open Today to review the next action.</p>}
    </Surface>
  </AppShell>;
}
