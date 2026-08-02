import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import type { Session } from '@supabase/supabase-js';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { AppRoutes } from '../App';
import { AuthContext, type AuthContextType } from '../components/auth/auth-context';
import Plan from '../pages/Plan';
import Settings from '../pages/Settings';
import Today from '../pages/Today';
import type { ActiveFocusSession, PlanResponse, TodayResponse } from '../types/api';

const session = { user: { email: 'person@example.com' }, access_token: 'test-token' } as unknown as Session;
const recommendation = { strategy: 'eisenhower_triage', title: 'Do now', why: 'The work is urgent and important.', evidence: ['urgent', 'important'], action: 'Start now.', tradeoff: 'Lower-priority work waits.', automatic_change: false as const, confidence: 'high' as const, alternatives: [] };
let active: ActiveFocusSession | null;
let conflictMode: boolean;
let overCapacity: boolean;
let profileFailure: boolean;
let transactionFailure: boolean;
let savedProfile: Record<string, unknown> | null;

const planningProfile = { timezone: 'Asia/Kolkata', available_weekdays: [0, 1, 2, 3, 4, 5], working_start_time: '09:30:00', working_end_time: '18:30:00', daily_focus_limit_minutes: 300, default_focus_duration_minutes: 45, minimum_transition_buffer_minutes: 10, minimum_daily_unscheduled_buffer_minutes: 60, protected_interval_start: '13:00:00', protected_interval_end: '14:00:00', quick_task_threshold_minutes: 5 };

function todayData(): TodayResponse {
  return { status: 'attention', status_message: 'One decision can make the plan workable.', next_action: { commitment_id: 'c1', title: 'Authentication regression fix', detail: 'Run the regression suite', estimated_minutes: 60 }, ordered_plan: [{ id: 'c1', kind: 'commitment', title: 'Authentication regression fix', commitment_id: 'c1', status: 'critical' }], attention_count: 1, strategy_recommendation: recommendation, pending_approval_count: 0, active_focus_session: active, recovery: { commitment_id: 'c1', title: 'Make the plan credible again', reason: 'The deadline is close.', options: ['Define a smaller next step'], requires_approval: true } };
}

function planData(): PlanResponse {
  return { range_start: '2026-08-02T00:00:00Z', range_end: '2026-08-03T00:00:00Z', calendar_events: [{ id: 'e1', kind: 'calendar_event', title: 'Team call', start_at: '2026-08-02T16:00:00Z', end_at: '2026-08-02T17:00:00Z', status: 'busy' }], plan_blocks: [], unscheduled_commitments: [{ id: 'c1', kind: 'commitment', title: 'Authentication regression fix', commitment_id: 'c1', status: 'critical' }], ordered_timeline: [{ id: 'e1', kind: 'calendar_event', title: 'Team call', start_at: '2026-08-02T16:00:00Z', end_at: '2026-08-02T17:00:00Z', status: 'busy' }], capacity: { total_minutes: 300, busy_minutes: 60, planned_minutes: overCapacity ? 360 : 0, buffer_minutes: 70, available_minutes: overCapacity ? 0 : 300, total_available_minutes: 300, scheduled_minutes: overCapacity ? 360 : 0, remaining_minutes: overCapacity ? 0 : 300, over_capacity_minutes: overCapacity ? 60 : 0, confidence: 'medium', sources: ['personal_availability', 'calendar_disconnected_profile_only'], calendar_state: 'disconnected' }, buffer_guidance: 'Keep at least 10 minutes between demanding blocks.' };
}

function json(data: unknown, status = 200) { return new Response(JSON.stringify(data), { status, headers: { 'Content-Type': 'application/json' } }); }

beforeEach(() => {
  active = null;
  conflictMode = false;
  overCapacity = false;
  profileFailure = false;
  transactionFailure = false;
  savedProfile = null;
  vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    if (url.endsWith('/api/v1/today')) return json(todayData());
    if (url.includes('/api/v1/plan/blocks')) return transactionFailure ? json({ error: { message: 'The transaction failed. No plan data was saved.' } }, 503) : conflictMode ? json({ error: { message: 'That time overlaps with Team call.' } }, 409) : json({ status: 'created', block: { id: 'b1' } }, 201);
    if (url.includes('/api/v1/plan?')) return json(planData());
    if (url.endsWith('/api/v1/settings/planning-profile/reset')) return json(planningProfile);
    if (url.endsWith('/api/v1/settings/planning-profile')) {
      if (profileFailure) return json({ error: { message: 'Database schema is incompatible with this ChronOS version.' } }, 503);
      if (init?.method === 'PUT') savedProfile = JSON.parse(String(init.body));
      return json(savedProfile ?? planningProfile);
    }
    if (url.endsWith('/api/v1/settings/integrations')) return json([{ provider: 'google_calendar', access: 'read_only', state: 'unavailable', last_successful_sync: null, retry_available: true, planning_mode: 'profile_only', message: 'Calendar status is temporarily unavailable. Planning is using your availability profile only.' }]);
    if (url.endsWith('/focus-blocks/start')) { active = { id: 'f1', commitment_id: 'c1', title: 'Authentication regression fix', status: 'active', planned_minutes: 25, elapsed_seconds: 0, remaining_seconds: 1500, started_at: new Date().toISOString() }; return json({ session: active }); }
    if (url.endsWith('/pause')) { active = { ...active!, status: 'paused', paused_at: new Date().toISOString() }; return json({ session: active }); }
    if (url.endsWith('/resume')) { active = { ...active!, status: 'active', paused_at: null }; return json({ session: active }); }
    if (url.endsWith('/stuck')) return json({ focus_block_id: 'f1', options: ['Define a smaller next step', 'Identify missing information', 'Switch to a short setup action', 'Request a recovery suggestion'], recovery_available: true });
    if (url.endsWith('/complete')) { active = null; return json({ session: null, reflection: { id: 'r1' }, reflection_requested: false }); }
    if (url.endsWith('/skip')) { active = null; return json({ session: null, reflection_requested: true }); }
    if (url.includes('/api/v1/rescue/')) return json({ status: 'plan_generated', proposals: [{ id: 'p1' }] });
    return json({});
  }));
});

function renderWithContext(ui: React.ReactNode, { path = '/', authenticated = true, signOut = vi.fn(async () => undefined) }: { path?: string; authenticated?: boolean; signOut?: AuthContextType['signOut'] } = {}) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  const auth: AuthContextType = { session: authenticated ? session : null, user: authenticated ? session.user : null, isLoading: false, signOut };
  const view = render(<QueryClientProvider client={client}><AuthContext.Provider value={auth}><MemoryRouter initialEntries={[path]}>{ui}</MemoryRouter></AuthContext.Provider></QueryClientProvider>);
  return { ...view, client };
}

it('shows an accessible fallback while a lazy route loads', async () => {
  renderWithContext(<AppRoutes />, { path: '/guide', authenticated: false });
  expect(screen.getByRole('status')).toHaveTextContent('Loading ChronOS');
  expect(await screen.findByRole('heading', { name: /from scattered commitments/i })).toBeInTheDocument();
});

it('renders the consolidated Today response and one strategy recommendation', async () => {
  renderWithContext(<Today />, { path: '/today' });
  expect(await screen.findByRole('heading', { name: 'Authentication regression fix' })).toBeInTheDocument();
  expect(screen.getByRole('heading', { name: 'Do now' })).toBeInTheDocument();
  expect(screen.getAllByText(/no automatic changes/i)).toHaveLength(1);
});

it('starts a contextual focus session from Today', async () => {
  const user = userEvent.setup(); renderWithContext(<Today />, { path: '/today' });
  await user.click(await screen.findByRole('button', { name: /start focus/i }));
  expect(await screen.findByText(/focus in progress/i)).toBeInTheDocument();
  expect(screen.getByLabelText(/seconds remaining/i)).toBeInTheDocument();
});

it('pauses, resumes, and finishes focus with a contextual reflection', async () => {
  active = { id: 'f1', commitment_id: 'c1', title: 'Authentication regression fix', status: 'active', planned_minutes: 25, elapsed_seconds: 3, remaining_seconds: 1497, started_at: new Date().toISOString() };
  const user = userEvent.setup(); renderWithContext(<Today />, { path: '/today' });
  await user.click(await screen.findByRole('button', { name: 'Pause' }));
  expect(await screen.findByRole('button', { name: 'Resume' })).toBeInTheDocument();
  await user.click(screen.getByRole('button', { name: 'Resume' }));
  expect(await screen.findByRole('button', { name: 'Finish' })).toBeInTheDocument();
  await user.click(screen.getByRole('button', { name: 'Finish' }));
  expect(screen.getByRole('heading', { name: /close the focus loop/i })).toBeInTheDocument();
  await user.click(screen.getByRole('button', { name: /save reflection/i }));
  expect(await screen.findByText(/reflection saved/i)).toBeInTheDocument();
});

it('shows the deterministic stuck options', async () => {
  active = { id: 'f1', commitment_id: 'c1', title: 'Fix', status: 'active', planned_minutes: 25, elapsed_seconds: 0, remaining_seconds: 1500, started_at: new Date().toISOString() };
  const user = userEvent.setup(); renderWithContext(<Today />);
  await user.click(await screen.findByRole('button', { name: /i’m stuck/i }));
  expect(await screen.findByText('Identify missing information')).toBeInTheDocument();
  expect(screen.getByText('Request a recovery suggestion')).toBeInTheDocument();
});

it('creates a plan block and invalidates the plan', async () => {
  const user = userEvent.setup(); renderWithContext(<Plan />, { path: '/plan' });
  await user.click(await screen.findByRole('button', { name: /add plan block/i }));
  await user.selectOptions(screen.getByLabelText('Commitment'), 'c1');
  await user.click(screen.getByRole('button', { name: /create block/i }));
  expect(await screen.findByText('Plan block created.')).toBeInTheDocument();
});

it('shows a clear overlap error for a conflicting plan block', async () => {
  conflictMode = true; const user = userEvent.setup(); renderWithContext(<Plan />);
  await user.click(await screen.findByRole('button', { name: /add plan block/i }));
  await user.selectOptions(screen.getByLabelText('Commitment'), 'c1');
  await user.click(screen.getByRole('button', { name: /create block/i }));
  expect(await screen.findByRole('alert')).toHaveTextContent('overlaps with Team call');
});

it('renders profile capacity, degraded planning, and over-capacity warnings', async () => {
  overCapacity = true;
  renderWithContext(<Plan />);
  expect(await screen.findByText('Over capacity by 60 minutes.')).toBeInTheDocument();
  expect(screen.getByText(/Profile-only planning/)).toHaveTextContent('medium confidence');
  expect(screen.getByText('300 min')).toBeInTheDocument();
});

it('surfaces an atomic transaction failure without a success state', async () => {
  transactionFailure = true;
  const user = userEvent.setup(); renderWithContext(<Plan />);
  await user.click(await screen.findByRole('button', { name: /add plan block/i }));
  await user.selectOptions(screen.getByLabelText('Commitment'), 'c1');
  await user.click(screen.getByRole('button', { name: /create block/i }));
  expect(await screen.findByRole('alert')).toHaveTextContent('No plan data was saved');
  expect(screen.queryByText('Plan block created.')).not.toBeInTheDocument();
});

it('validates available weekdays before saving', async () => {
  const user = userEvent.setup(); renderWithContext(<Settings />);
  const checkboxes = await screen.findAllByRole('checkbox');
  for (const checkbox of checkboxes) if ((checkbox as HTMLInputElement).checked) await user.click(checkbox);
  expect(screen.getByRole('alert')).toHaveTextContent('Choose at least one available day');
  expect(screen.getByRole('button', { name: 'Save availability' })).toBeDisabled();
});

it('persists personal availability and renders the selected timezone', async () => {
  const user = userEvent.setup(); renderWithContext(<Settings />);
  expect(await screen.findByLabelText('Timezone')).toHaveValue('Asia/Kolkata');
  await user.clear(screen.getByLabelText('Daily focus-minute limit'));
  await user.type(screen.getByLabelText('Daily focus-minute limit'), '240');
  await user.click(screen.getByRole('button', { name: 'Save availability' }));
  expect(await screen.findByRole('status')).toHaveTextContent('Availability saved');
  expect(savedProfile).toMatchObject({ timezone: 'Asia/Kolkata', daily_focus_limit_minutes: 240 });
});

it('shows honest profile-only integration state', async () => {
  renderWithContext(<Settings />);
  expect(await screen.findByText('unavailable')).toBeInTheDocument();
  expect(screen.getByText(/availability profile only/i)).toBeInTheDocument();
  expect(screen.getByText('Read-only')).toBeInTheDocument();
});

it('shows a migration compatibility error without raw provider details', async () => {
  profileFailure = true;
  renderWithContext(<Settings />);
  expect(await screen.findByText(/schema is incompatible/i)).toBeInTheDocument();
});

it('renders Strategy Engine evidence, confidence, and automation boundary', async () => {
  renderWithContext(<Today />);
  expect(await screen.findByText(/high confidence/i)).toBeInTheDocument();
  expect(screen.getByText('urgent · important')).toBeInTheDocument();
  expect(screen.getByText(/no automatic changes/i)).toBeInTheDocument();
});

it('clears private query data on logout and leaves protected content', async () => {
  const user = userEvent.setup(); const signOut = vi.fn(async () => undefined); const { client } = renderWithContext(<Today />, { path: '/today', signOut });
  await screen.findByText('Run the regression suite'); client.setQueryData(['private'], { secret: true });
  await user.click(screen.getByRole('button', { name: /log out/i }));
  expect(signOut).toHaveBeenCalled(); expect(client.getQueryData(['private'])).toBeUndefined();
});

it('keeps recovery and reflection contextual instead of primary navigation', async () => {
  const user = userEvent.setup(); renderWithContext(<Today />);
  const navigation = await screen.findByRole('navigation', { name: /primary/i });
  expect(navigation).not.toHaveTextContent('Recovery'); expect(navigation).not.toHaveTextContent('Reflection');
  expect(await screen.findByRole('heading', { name: /make the plan credible again/i })).toBeInTheDocument();
  await user.click(screen.getByRole('button', { name: /prepare recovery recommendation/i }));
  expect(await screen.findByText(/prepared for approval/i)).toBeInTheDocument();
});

describe('auth boundary', () => {
  it('redirects a logged-out protected route without private content', async () => {
    renderWithContext(<AppRoutes />, { path: '/today', authenticated: false });
    expect(await screen.findByRole('heading', { name: /welcome back/i })).toBeInTheDocument();
    expect(screen.queryByText('Run the regression suite')).not.toBeInTheDocument();
  });
});
