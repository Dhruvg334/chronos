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
        className="text-[#7A7771] hover:text-[#B57C45] transition-colors focus:outline-none focus:ring-2 focus:ring-[#B57C45] rounded-full p-0.5"
        aria-label="More information"
      >
        <Info className="w-4 h-4" />
      </button>
      {isTooltipVisible && (
        <div 
          className="absolute z-50 w-64 p-3 mt-2 text-xs font-medium leading-relaxed text-[#2C2B29] bg-white border border-[#E5E0D8] rounded-xl shadow-lg shadow-black/5 top-full left-1/2 -translate-x-1/2 md:translate-x-0 md:left-0 pointer-events-none"
        >
          {content}
        </div>
      )}
    </div>
  );
}
