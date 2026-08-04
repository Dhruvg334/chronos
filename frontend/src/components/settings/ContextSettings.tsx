import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiFetch, apiUrl, getApiErrorMessage } from '../../lib/api';
import type { KnowledgeSource, MemoryItem, ProjectSummary } from '../../types/api';
import { Surface } from '../ui/primitives';

const categories = ['preference', 'constraint', 'working_pattern', 'project_fact', 'personal_rule', 'decision'] as const;

async function loadMemory() {
  const response = await apiFetch(apiUrl('/api/v1/context/memory'));
  if (!response.ok) throw new Error(await getApiErrorMessage(response, 'Your saved context could not be loaded.'));
  return response.json() as Promise<{ items: MemoryItem[] }>;
}

async function loadSources() {
  const response = await apiFetch(apiUrl('/api/v1/context/knowledge'));
  if (!response.ok) throw new Error(await getApiErrorMessage(response, 'Your notes and documents could not be loaded.'));
  return response.json() as Promise<{ sources: KnowledgeSource[] }>;
}

async function loadProjects() {
  const response = await apiFetch(apiUrl('/api/v1/projects'));
  if (!response.ok) return { projects: [] as ProjectSummary[] };
  return response.json() as Promise<{ projects: ProjectSummary[] }>;
}

export function ContextSettings() {
  const queryClient = useQueryClient();
  const memory = useQuery({ queryKey: ['memory'], queryFn: loadMemory });
  const sources = useQuery({ queryKey: ['knowledge-sources'], queryFn: loadSources });
  const projects = useQuery({ queryKey: ['projects'], queryFn: loadProjects });
  const [category, setCategory] = useState<(typeof categories)[number]>('preference');
  const [content, setContent] = useState('');
  const [filter, setFilter] = useState('all');
  const [editing, setEditing] = useState<string | null>(null);
  const [editContent, setEditContent] = useState('');
  const [noteTitle, setNoteTitle] = useState('');
  const [note, setNote] = useState('');
  const [memoryProjectId, setMemoryProjectId] = useState('');
  const [sourceProjectId, setSourceProjectId] = useState('');
  const [notice, setNotice] = useState('');

  const exportMemory = useMutation({
    mutationFn: async () => {
      const response = await apiFetch(apiUrl('/api/v1/context/memory-export'));
      if (!response.ok) throw new Error(await getApiErrorMessage(response, 'Your memory export could not be prepared.'));
      return response.json();
    },
    onSuccess: (data) => {
      const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' }));
      const anchor = document.createElement('a'); anchor.href = url; anchor.download = 'chronos-memory.json'; anchor.click(); URL.revokeObjectURL(url);
      setNotice('Memory export prepared.');
    },
  });

  const refreshMemory = () => queryClient.invalidateQueries({ queryKey: ['memory'] });
  const create = useMutation({
    mutationFn: async () => {
      const response = await apiFetch(apiUrl('/api/v1/context/memory'), { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ category, content, project_id: memoryProjectId || null }) });
      if (!response.ok) throw new Error(await getApiErrorMessage(response, 'This memory could not be saved.'));
      return response.json();
    },
    onSuccess: async () => { setContent(''); setNotice('Memory saved as an explicit preference or fact.'); await refreshMemory(); },
  });
  const decide = useMutation({
    mutationFn: async ({ id, decision }: { id: string; decision: 'confirm' | 'reject' | 'archive' | 'expire' }) => {
      const response = await apiFetch(apiUrl(`/api/v1/context/memory/${id}/decision`), { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ decision }) });
      if (!response.ok) throw new Error(await getApiErrorMessage(response, 'This memory could not be updated.'));
      return response.json();
    },
    onSuccess: async () => { setNotice('Memory updated.'); await refreshMemory(); },
  });
  const edit = useMutation({
    mutationFn: async () => {
      const response = await apiFetch(apiUrl(`/api/v1/context/memory/${editing}`), { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ content: editContent }) });
      if (!response.ok) throw new Error(await getApiErrorMessage(response, 'Your correction could not be saved.'));
      return response.json();
    },
    onSuccess: async () => { setEditing(null); setNotice('Correction saved with its history.'); await refreshMemory(); },
  });
  const ingestNote = useMutation({
    mutationFn: async () => {
      const response = await apiFetch(apiUrl('/api/v1/context/knowledge/text'), { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ title: noteTitle, source_type: sourceProjectId ? 'project_context' : 'note', content: note, project_id: sourceProjectId || null, idempotency_key: crypto.randomUUID() }) });
      if (!response.ok) throw new Error(await getApiErrorMessage(response, 'This note could not be indexed.'));
      return response.json();
    },
    onSuccess: async (result) => { setNoteTitle(''); setNote(''); setNotice(result.status === 'duplicate' ? 'That note is already in your context.' : 'Note added to your context.'); await queryClient.invalidateQueries({ queryKey: ['knowledge-sources'] }); },
  });
  const upload = useMutation({
    mutationFn: async (file: File) => {
      const body = new FormData(); body.append('file', file); body.append('idempotency_key', crypto.randomUUID()); if (sourceProjectId) body.append('project_id', sourceProjectId);
      const response = await apiFetch(apiUrl('/api/v1/context/knowledge/file'), { method: 'POST', body });
      if (!response.ok) throw new Error(await getApiErrorMessage(response, 'This document could not be indexed.'));
      return response.json();
    },
    onSuccess: async (result) => { setNotice(result.status === 'duplicate' ? 'That document is already in your context.' : 'Document added to your context.'); await queryClient.invalidateQueries({ queryKey: ['knowledge-sources'] }); },
  });

  const visible = (memory.data?.items ?? []).filter((item) => filter === 'all' || item.category === filter);
  const error = create.error || decide.error || edit.error || ingestNote.error || upload.error || exportMemory.error;
  return <Surface className="p-6">
    <div className="flex flex-wrap items-start justify-between gap-3">
      <div><h2 className="font-semibold">Memory and context</h2><p className="mt-2 max-w-2xl text-sm text-muted">Review what ChronOS may use when explaining plans. Proposed observations never become facts until you confirm them.</p></div>
      <button className="button-secondary" disabled={exportMemory.isPending} onClick={() => exportMemory.mutate()}>{exportMemory.isPending ? 'Preparing…' : 'Export memory'}</button>
    </div>

    <form className="mt-5 grid gap-3 sm:grid-cols-2" onSubmit={(event) => { event.preventDefault(); setNotice(''); create.mutate(); }}>
      <label className="label">Memory type<select className="field mt-1" value={category} onChange={(event) => setCategory(event.target.value as typeof category)}>{categories.map((value) => <option key={value} value={value}>{value.replaceAll('_', ' ')}</option>)}</select></label>
      <label className="label">Project context (optional)<select className="field mt-1" value={memoryProjectId} onChange={(event) => setMemoryProjectId(event.target.value)}><option value="">Applies everywhere</option>{projects.data?.projects.map((project) => <option key={project.id} value={project.id}>{project.title}</option>)}</select></label>
      <label className="label">What should ChronOS remember?<input className="field mt-1" value={content} maxLength={4000} required onChange={(event) => setContent(event.target.value)} /></label>
      <button className="button-primary self-end justify-self-start" disabled={create.isPending}>{create.isPending ? 'Saving…' : 'Add memory'}</button>
    </form>

    <div className="mt-6 flex flex-wrap items-center gap-2"><label className="label" htmlFor="memory-filter">Show</label><select id="memory-filter" className="field max-w-52" value={filter} onChange={(event) => setFilter(event.target.value)}><option value="all">All memory</option>{categories.map((value) => <option key={value} value={value}>{value.replaceAll('_', ' ')}</option>)}</select></div>
    {memory.isPending ? <p className="mt-4 text-sm text-muted">Loading saved context…</p> : memory.isError ? <p role="alert" className="mt-4 text-sm text-danger">{memory.error.message}</p> : visible.length === 0 ? <p className="mt-4 text-sm text-muted">Nothing saved here yet. Add one useful preference or constraint.</p> : <div className="mt-4 space-y-3">{visible.map((item) => <article key={item.id} className="rounded-xl border border-line p-4">
      <div className="flex flex-wrap items-center gap-2"><span className="rounded-full bg-accent-soft px-2.5 py-1 text-xs font-semibold text-accent-strong">{item.category.replaceAll('_', ' ')}</span><span className="text-xs text-muted">{item.is_explicit ? 'Stated by you' : 'Proposed observation'} · {Math.round(item.confidence * 100)}% confidence · {item.status}</span></div>
      {editing === item.id ? <form className="mt-3" onSubmit={(event) => { event.preventDefault(); edit.mutate(); }}><label className="label">Correct this memory<textarea className="field mt-1 min-h-24" value={editContent} onChange={(event) => setEditContent(event.target.value)} /></label><div className="mt-2 flex gap-2"><button className="button-primary">Save correction</button><button type="button" className="button-secondary" onClick={() => setEditing(null)}>Cancel</button></div></form> : <p className="mt-3 text-sm leading-6">{item.content}</p>}
      <details className="mt-3"><summary className="cursor-pointer text-xs font-medium text-muted">Source and history</summary><p className="mt-2 text-xs text-muted">{item.source_reference?.label ?? item.source_type.replaceAll('_', ' ')}</p>{item.source_reference?.correction_history?.map((history) => <p key={history.corrected_at} className="mt-1 text-xs text-faint">Previously: {history.content}</p>)}</details>
      {item.conflicts?.map((conflict) => <div key={conflict.id} className="mt-3 rounded-lg bg-warning-soft p-3 text-sm"><p>{conflict.message}</p><p className="mt-1 text-muted">Conflicts with: {conflict.content}</p><button className="button-secondary mt-2" onClick={() => decide.mutate({ id: conflict.id, decision: 'archive' })}>Keep this and archive the other</button></div>)}
      <div className="mt-3 flex flex-wrap gap-2">{item.status === 'proposed' && <><button className="button-primary" onClick={() => decide.mutate({ id: item.id, decision: 'confirm' })}>Confirm</button><button className="button-secondary" onClick={() => decide.mutate({ id: item.id, decision: 'reject' })}>Not accurate</button></>}<button className="button-secondary" onClick={() => { setEditing(item.id); setEditContent(item.content); }}>Edit</button>{item.status !== 'archived' && <button className="px-3 py-2 text-sm text-muted" onClick={() => decide.mutate({ id: item.id, decision: 'archive' })}>Archive</button>}</div>
    </article>)}</div>}

    <div className="mt-8 border-t border-line pt-6"><h3 className="font-semibold">Notes and documents</h3><p className="mt-1 text-sm text-muted">Add context, not commands. ChronOS treats all document text as untrusted and only cites relevant excerpts.</p>
      <form className="mt-4 grid gap-3" onSubmit={(event) => { event.preventDefault(); setNotice(''); ingestNote.mutate(); }}><label className="label">Note title<input className="field mt-1" required maxLength={240} value={noteTitle} onChange={(event) => setNoteTitle(event.target.value)} /></label><label className="label">Project context (optional)<select className="field mt-1" value={sourceProjectId} onChange={(event) => setSourceProjectId(event.target.value)}><option value="">General context</option>{projects.data?.projects.map((project) => <option key={project.id} value={project.id}>{project.title}</option>)}</select></label><label className="label">Note<textarea className="field mt-1 min-h-28" required maxLength={200000} value={note} onChange={(event) => setNote(event.target.value)} /></label><button className="button-primary justify-self-start" disabled={ingestNote.isPending}>{ingestNote.isPending ? 'Indexing…' : 'Add note'}</button></form>
      <label className="button-secondary mt-3 inline-flex cursor-pointer">Add text, Markdown, or PDF<input className="sr-only" type="file" accept=".txt,.md,.pdf,text/plain,text/markdown,application/pdf" onChange={(event) => { const file = event.target.files?.[0]; if (file) upload.mutate(file); }} /></label>
      {sources.isPending ? <p className="mt-4 text-sm text-muted">Loading sources…</p> : <ul className="mt-4 space-y-2">{sources.data?.sources.filter((source) => source.status !== 'archived').map((source) => <li key={source.id} className="flex flex-wrap items-center justify-between gap-2 rounded-lg bg-surface-subtle p-3"><span><span className="text-sm font-medium">{source.title}</span><span className="ml-2 text-xs text-muted">{source.source_type.replaceAll('_', ' ')} · {source.status === 'failed' ? 'Needs attention' : source.status}</span></span></li>)}</ul>}
    </div>
    {notice && <p role="status" className="mt-4 text-sm text-success">{notice}</p>}
    {error && <p role="alert" className="mt-4 text-sm text-danger">{error.message}</p>}
  </Surface>;
}
