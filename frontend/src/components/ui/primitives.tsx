import type { HTMLAttributes, ReactNode } from 'react';
import { AlertCircle, Inbox as InboxIcon, LoaderCircle } from 'lucide-react';

export function PageHeader({ eyebrow, title, description, action }: { eyebrow?: string; title: string; description?: string; action?: ReactNode }) {
  return <header className="mb-7 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between"><div>{eyebrow && <p className="mb-2 text-xs font-semibold uppercase tracking-[0.16em] text-accent-strong">{eyebrow}</p>}<h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">{title}</h1>{description && <p className="mt-2 max-w-2xl text-muted">{description}</p>}</div>{action}</header>;
}

export function Surface({ className = '', ...props }: HTMLAttributes<HTMLDivElement>) { return <div className={`surface ${className}`} {...props} />; }

export function LoadingState({ label = 'Loading' }: { label?: string }) { return <div className="surface flex min-h-48 items-center justify-center gap-3 text-sm text-muted"><LoaderCircle className="h-5 w-5 animate-spin text-accent" />{label}</div>; }

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) { return <div role="alert" className="surface flex min-h-48 flex-col items-center justify-center p-6 text-center"><AlertCircle className="mb-3 h-6 w-6 text-danger" /><h2 className="font-semibold">Something needs attention</h2><p className="mt-1 max-w-lg text-sm text-muted">{message}</p>{onRetry && <button className="button-secondary mt-4" onClick={onRetry}>Try again</button>}</div>; }

export function EmptyState({ title, message, action }: { title: string; message: string; action?: ReactNode }) { return <div className="surface flex min-h-48 flex-col items-center justify-center p-6 text-center"><InboxIcon className="mb-3 h-6 w-6 text-faint" /><h2 className="font-semibold">{title}</h2><p className="mt-1 max-w-lg text-sm text-muted">{message}</p>{action && <div className="mt-4">{action}</div>}</div>; }
