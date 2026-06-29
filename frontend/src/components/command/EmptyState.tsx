import { LayoutDashboard, ArrowRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface EmptyStateProps {
  onLoadDemo: () => Promise<void>;
}

export function EmptyState({ onLoadDemo }: EmptyStateProps) {
  const navigate = useNavigate();

  return (
    <div className="flex flex-col items-center justify-center py-20 px-4 text-center border border-warm-border border-dashed rounded-2xl bg-white shadow-sm max-w-3xl mx-auto mt-8">
      <div className="w-16 h-16 bg-warm-ivory border border-warm-border rounded-2xl flex items-center justify-center mb-6 shadow-sm">
        <LayoutDashboard className="w-8 h-8 text-text-muted" />
      </div>
      <h2 className="text-2xl font-bold text-text-primary mb-3">No commitments yet</h2>
      <p className="text-text-secondary max-w-md mx-auto mb-8 leading-relaxed">
        ChronOS needs something to manage. You can either paste a messy brain dump into the Inbox, or load the Judge Demo to see how ChronOS rescues a slipping deadline.
      </p>
      
      <div className="flex flex-col sm:flex-row gap-4">
        <button
          onClick={() => navigate('/inbox')}
          className="flex items-center justify-center gap-2 px-6 py-2.5 font-semibold text-white bg-text-primary rounded-lg hover:bg-black transition-colors shadow-sm"
        >
          Go to Inbox
          <ArrowRight className="w-4 h-4" />
        </button>
        <button
          onClick={onLoadDemo}
          className="px-6 py-2.5 font-semibold text-text-secondary bg-white border border-warm-border rounded-lg hover:bg-warm-ivory transition-colors shadow-sm"
        >
          Load Judge Demo
        </button>
      </div>
    </div>
  );
}
