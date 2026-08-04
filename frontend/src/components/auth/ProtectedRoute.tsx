import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from './auth-context';
import { Loader2 } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { loadOnboarding } from '../../lib/onboarding';

export function ProtectedRoute() {
  const { session, isLoading } = useAuth();
  const location = useLocation();
  const onboarding = useQuery({ queryKey: ['onboarding'], queryFn: loadOnboarding, enabled: !!session });

  if (isLoading || (!!session && onboarding.isPending)) {
    return (
      <div className="flex h-screen w-full items-center justify-center bg-canvas">
        <Loader2 className="w-8 h-8 animate-spin text-accent-strong" />
      </div>
    );
  }

  if (!session) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  if (onboarding.data && !['completed', 'skipped'].includes(onboarding.data.onboarding_status) && location.pathname !== '/onboarding') {
    return <Navigate to="/onboarding" replace />;
  }

  return <Outlet />;
}
