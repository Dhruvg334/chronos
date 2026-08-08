import type { HTMLAttributes, ReactNode } from 'react';
import { AlertCircle, Inbox as InboxIcon, LoaderCircle } from 'lucide-react';

export function PageHeader({ eyebrow, title, description, action }: { eyebrow?: string; title: string; description?: string; action?: ReactNode }) {
  return (
    <header className="mb-8 flex flex-col gap-5 border-b border-line pb-6 sm:flex-row sm:items-end sm:justify-between">
      <div className="min-w-0">
        {eyebrow && <p className="eyebrow mb-2">{eyebrow}</p>}
        <h1 className="max-w-3xl text-3xl font-semibold leading-tight tracking-[-0.035em] text-balance sm:text-[2.55rem]">{title}</h1>
        {description && <p className="mt-2 max-w-2xl text-sm leading-6 text-muted sm:text-base">{description}</p>}
      </div>
      {action && <div className="shrink-0">{action}</div>}
    </header>
  );
}

export function Surface({ className = '', ...props }: HTMLAttributes<HTMLDivElement>) { return <div className={`surface ${className}`} {...props} />; }

export function LoadingState({ label = 'Loading' }: { label?: string }) {
  return <div className="flex min-h-44 items-center justify-center gap-3 rounded-2xl border border-line bg-white text-sm text-muted"><LoaderCircle className="h-5 w-5 animate-spin text-accent" />{label}</div>;
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return <div role="alert" className="flex min-h-44 flex-col items-center justify-center rounded-2xl border border-danger/20 bg-danger-soft/50 p-6 text-center"><AlertCircle className="mb-3 h-6 w-6 text-danger" /><h2 className="font-semibold">Something needs attention</h2><p className="mt-1 max-w-lg text-sm text-muted">{message}</p>{onRetry && <button className="button-secondary mt-4" onClick={onRetry}>Try again</button>}</div>;
}

export function EmptyState({ title, message, action }: { title: string; message: string; action?: ReactNode }) {
  return <div className="flex min-h-44 flex-col items-center justify-center rounded-2xl border border-dashed border-[#D7D7D0] bg-white/55 p-7 text-center"><InboxIcon className="mb-3 h-5 w-5 text-faint" /><h2 className="font-semibold">{title}</h2><p className="mt-1 max-w-lg text-sm leading-6 text-muted">{message}</p>{action && <div className="mt-4">{action}</div>}</div>;
}
