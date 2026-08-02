import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import type { Session } from '@supabase/supabase-js';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import { AppRoutes } from '../App';
import { AuthContext, type AuthContextType } from '../components/auth/auth-context';
import { StrategyRecommendationCard } from '../components/strategy/StrategyRecommendationCard';
import Today from '../pages/Today';

const session = { user: { email: 'person@example.com' }, access_token: 'test-token' } as unknown as Session;

function renderWithContext(ui: React.ReactNode, { path = '/', authenticated = true }: { path?: string; authenticated?: boolean } = {}) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  const auth: AuthContextType = { session: authenticated ? session : null, user: authenticated ? session.user : null, isLoading: false, signOut: vi.fn(async () => undefined) };
  return render(<QueryClientProvider client={client}><AuthContext.Provider value={auth}><MemoryRouter initialEntries={[path]}>{ui}</MemoryRouter></AuthContext.Provider></QueryClientProvider>);
}

describe('routing and shell', () => {
  it('redirects a logged-out protected route without rendering private state', async () => {
    renderWithContext(<AppRoutes />, { path: '/today', authenticated: false });
    expect(await screen.findByRole('heading', { name: /welcome back/i })).toBeInTheDocument();
    expect(screen.queryByText(/realistic day, at a glance/i)).not.toBeInTheDocument();
  });

  it('renders the public demo without authentication', () => {
    renderWithContext(<AppRoutes />, { path: '/demo', authenticated: false });
    expect(screen.getByRole('heading', { name: /a busy day, made credible/i })).toBeInTheDocument();
    expect(screen.getByText(/does not authenticate/i)).toBeInTheDocument();
  });

  it('shows only Today, Inbox, and Plan in primary navigation', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => new Response(JSON.stringify([]), { status: 200 })));
    renderWithContext(<Today />, { path: '/today' });
    const navigation = screen.getByRole('navigation', { name: /primary/i });
    expect(navigation).toHaveTextContent('Today');
    expect(navigation).toHaveTextContent('Inbox');
    expect(navigation).toHaveTextContent('Plan');
    expect(navigation).not.toHaveTextContent('Reflection');
  });
});

describe('Today', () => {
  it('renders one next action and a strategy recommendation', async () => {
    const commitments = [{ id: '1', user_id: 'u', title: 'Finish authentication fix', description: 'Run the regression suite', type: 'hard_deadline', status: 'active', estimated_minutes: 60, actual_minutes: 0, importance: 5, flexibility: 1, progress_percent: 0, risk_level: 'critical', risk_score: 90, confidence_score: 0.9 }];
    vi.stubGlobal('fetch', vi.fn(async () => new Response(JSON.stringify(commitments), { status: 200, headers: { 'Content-Type': 'application/json' } })));
    renderWithContext(<Today />, { path: '/today' });
    expect(await screen.findByRole('heading', { name: 'Finish authentication fix' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /do now, then protect/i })).toBeInTheDocument();
    expect(screen.getAllByRole('button', { name: /start focus/i })).toHaveLength(1);
  });

  it('renders a retryable public error instead of a raw payload', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => new Response(JSON.stringify({ error: { code: 'persistence_error', message: 'Your plan is temporarily unavailable.' } }), { status: 503, headers: { 'Content-Type': 'application/json' } })));
    renderWithContext(<Today />, { path: '/today' });
    expect(await screen.findByRole('alert')).toHaveTextContent('Your plan is temporarily unavailable.');
    expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument();
    expect(screen.queryByText('persistence_error')).not.toBeInTheDocument();
  });
});

it('explains that strategy guidance does not change data', () => {
  render(<StrategyRecommendationCard recommendation={{ title: 'Batch the quick tasks', why: 'Three similar emails would interrupt focus.', evidence: ['3 email tasks'], action: 'Review them together at 4 PM.', tradeoff: 'Replies wait until the batch.', automaticChange: false }} />);
  expect(screen.getByText(/no automatic changes/i)).toBeInTheDocument();
});

it('validates the documented invalid signup values', async () => {
  const user = userEvent.setup();
  renderWithContext(<AppRoutes />, { path: '/signup', authenticated: false });
  await user.type(screen.getByPlaceholderText('you@example.com'), 'dhruv');
  await user.type(screen.getByPlaceholderText('At least 8 characters'), 'Chronos123!');
  await user.type(screen.getByPlaceholderText('Repeat your password'), 'Chronos123!');
  await user.click(screen.getByRole('button', { name: /sign up/i }));
  expect(await screen.findByText(/valid email address/i)).toBeInTheDocument();
});
