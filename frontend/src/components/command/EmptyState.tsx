import { LayoutDashboard, ArrowRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface EmptyStateProps {
  onLoadDemo: () => Promise<void>;
}

export function EmptyState({ onLoadDemo }: EmptyStateProps) {
  const navigate = useNavigate();

  return (
    <div className="flex flex-col items-center justify-center py-20 px-4 text-center border border-slate-800 border-dashed rounded-xl bg-slate-900/50">
      <div className="w-16 h-16 bg-slate-800 rounded-2xl flex items-center justify-center mb-6 shadow-inner">
        <LayoutDashboard className="w-8 h-8 text-slate-400" />
      </div>
      <h2 className="text-2xl font-bold text-white mb-3">No commitments yet</h2>
      <p className="text-slate-400 max-w-md mx-auto mb-8 leading-relaxed">
        ChronOS needs something to manage. You can either paste a messy brain dump into the Inbox, or load the Judge Demo to see it in action instantly.
      </p>
      
      <div className="flex flex-col sm:flex-row gap-4">
        <button
          onClick={() => navigate('/inbox')}
          className="flex items-center justify-center gap-2 px-6 py-3 font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-500 transition-colors"
        >
          Go to Inbox
          <ArrowRight className="w-4 h-4" />
        </button>
        <button
          onClick={() => {
            const confirmed = window.confirm('Load the Judge Demo scenario? This will replace existing demo-tagged records, but it will not delete your real commitments.');
            if (confirmed) void onLoadDemo();
          }}
          className="px-6 py-3 font-semibold text-slate-300 bg-slate-800 rounded-lg hover:bg-slate-700 hover:text-white transition-colors"
        >
          Load Judge Demo
        </button>
      </div>
    </div>
  );
}
