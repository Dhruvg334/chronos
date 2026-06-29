import { Info } from 'lucide-react';
import { useState } from 'react';

interface InfoHintProps {
  content: string;
}

export function InfoHint({ content }: InfoHintProps) {
  const [isTooltipVisible, setTooltipVisible] = useState(false);

  return (
    <div 
      className="relative inline-flex items-center ml-1"
      onMouseEnter={() => setTooltipVisible(true)}
      onMouseLeave={() => setTooltipVisible(false)}
      onFocus={() => setTooltipVisible(true)}
      onBlur={() => setTooltipVisible(false)}
    >
      <button 
        type="button" 
        className="text-text-muted hover:text-accent-amber transition-colors focus:outline-none focus:ring-2 focus:ring-accent-amber rounded-full p-0.5"
        aria-label="More information"
      >
        <Info className="w-4 h-4" />
      </button>
      {isTooltipVisible && (
        <div 
          className="absolute z-50 w-64 p-3 mt-2 text-xs font-medium leading-relaxed text-text-primary bg-white border border-warm-border rounded-xl shadow-lg shadow-black/5 top-full left-1/2 -translate-x-1/2 md:translate-x-0 md:left-0 pointer-events-none"
        >
          {content}
        </div>
      )}
    </div>
  );
}
