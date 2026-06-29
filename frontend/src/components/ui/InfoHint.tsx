import { Info } from 'lucide-react';
import { useState } from 'react';

interface InfoHintProps {
  content: string;
  align?: 'start' | 'end';
}

export function InfoHint({ content, align = 'start' }: InfoHintProps) {
  const [isTooltipVisible, setTooltipVisible] = useState(false);

  return (
    <span
      className="relative inline-flex items-center ml-1 align-middle"
      onMouseEnter={() => setTooltipVisible(true)}
      onMouseLeave={() => setTooltipVisible(false)}
      onFocus={() => setTooltipVisible(true)}
      onBlur={() => setTooltipVisible(false)}
    >
      <button
        type="button"
        title={content}
        className="rounded-full p-0.5 text-text-muted transition-colors hover:text-accent-amber focus:outline-none focus:ring-2 focus:ring-accent-amber/40"
        aria-label={content}
      >
        <Info className="h-4 w-4" />
      </button>
      {isTooltipVisible && (
        <span
          className={`absolute top-full z-[100] mt-2 w-64 max-w-[min(16rem,calc(100vw-2rem))] rounded-xl border border-warm-border bg-white p-3 text-left text-xs font-medium leading-relaxed text-text-primary shadow-lg shadow-black/5 ${align === 'end' ? 'right-0' : 'left-0'}`}
        >
          {content}
        </span>
      )}
    </span>
  );
}
