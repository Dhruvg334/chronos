import { LayoutDashboard, ArrowRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface EmptyStateProps {
  onLoadDemo: () => Promise<void>;
}

export function EmptyState({ onLoadDemo }: EmptyStateProps) {
  const navigate = useNavigate();

  return (
    <div className="flex flex-col items-center justify-center py-20 px-4 text-center border border-[#E5E0D8] border-dashed rounded-2xl bg-white shadow-sm max-w-3xl mx-auto mt-8">
      <div className="w-16 h-16 bg-[#FAF9F6] border border-[#E5E0D8] rounded-2xl flex items-center justify-center mb-6 shadow-sm">
        <LayoutDashboard className="w-8 h-8 text-[#7A7771]" />
      </div>
      <h2 className="text-2xl font-bold text-[#2C2B29] mb-3">No commitments yet</h2>
      <p className="text-[#5C5A56] max-w-md mx-auto mb-8 leading-relaxed">
        ChronOS needs something to manage. You can either paste a messy brain dump into the Inbox, or load the Judge Demo to see how ChronOS rescues a slipping deadline.
      </p>
      
      <div className="flex flex-col sm:flex-row gap-4">
        <button
          onClick={() => navigate('/inbox')}
          className="flex items-center justify-center gap-2 px-6 py-2.5 font-semibold text-white bg-[#2C2B29] rounded-lg hover:bg-black transition-colors shadow-sm"
        >
          Go to Inbox
          <ArrowRight className="w-4 h-4" />
        </button>
        <button
          onClick={onLoadDemo}
          className="px-6 py-2.5 font-semibold text-[#5C5A56] bg-white border border-[#E5E0D8] rounded-lg hover:bg-[#FAF9F6] transition-colors shadow-sm"
        >
          Load Judge Demo
        </button>
      </div>
    </div>
  );
}
