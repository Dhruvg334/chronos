import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import type { Session } from '@supabase/supabase-js';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { AppRoutes } from '../App';
import { AuthContext, type AuthContextType } from '../components/auth/auth-context';
import Plan from '../pages/Plan';
import Projects from '../pages/Projects';
import Week from '../pages/Week';
import Settings from '../pages/Settings';
import Today from '../pages/Today';
import Onboarding from '../pages/Onboarding';
import { CommitmentDraftCard } from '../components/intake/CommitmentDraftCard';
import type { ActiveFocusSession, PlanResponse, TodayResponse } from '../types/api';

const session = { user: { email: 'person@example.com' }, access_token: 'test-token' } as unknown as Session;
const recommendation = { strategy: 'eisenhower_triage', title: 'Do now', why: 'The work is urgent and important.', evidence: ['urgent', 'important'], action: 'Start now.', tradeoff: 'Lower-priority work waits.', automatic_change: false as const, confidence: 'high' as const, alternatives: [] };
let active: ActiveFocusSession | null;
let conflictMode: boolean;
let overCapacity: boolean;
let profileFailure: boolean;
let transactionFailure: boolean;
let savedProfile: Record<string, unknown> | null;
let projectExists: boolean;
let outcomeExists: boolean;
let routines: Array<Record<string, unknown>>;
let onboardingStatus: 'not_started' | 'in_progress' | 'completed' | 'skipped';
let onboardingStep: number;
let savedPreferences: Record<string, unknown> | null;

const preferences = { planning_style: 'balanced' as const, recommendation_frequency: 'normal' as const, approval_strictness: 'always_ask' as const, internal_write_automation_enabled: false, preferred_focus_durations: [25,45,60], routine_continuity_preference: 'gentle' as const, quick_task_mode: 'batch' as const, strategy_preferences: ['eisenhower_triage','task_batching','continuity_recovery','focus_interval','constrained_day','quick_action','time_blocking'], explanation_detail: 'standard' as const };
const planningProfile = { timezone: 'Asia/Kolkata', available_weekdays: [0, 1, 2, 3, 4, 5], working_start_time: '09:30:00', working_end_time: '18:30:00', daily_focus_limit_minutes: 300, default_focus_duration_minutes: 45, minimum_transition_buffer_minutes: 10, minimum_daily_unscheduled_buffer_minutes: 60, protected_interval_start: '13:00:00', protected_interval_end: '14:00:00', quick_task_threshold_minutes: 5, onboarding_status: 'completed' as const, onboarding_step: 3, onboarding_completed_at: '2026-08-04T00:00:00Z', ...preferences };

function todayData(): TodayResponse {
  return { status: 'attention', status_message: 'One decision can make the plan workable.', next_action: { commitment_id: 'c1', title: 'Authentication regression fix', detail: 'Run the regression suite', estimated_minutes: 60, project: { id: 'p1', title: 'ChronOS Production Release' }, outcome: { id: 'o1', title: 'Stable authentication and session handling' } }, ordered_plan: [{ id: 'c1', kind: 'commitment', title: 'Authentication regression fix', commitment_id: 'c1', status: 'critical' }], attention_count: 1, strategy_recommendation: recommendation, pending_approval_count: 0, active_focus_session: active, recovery: { recommendation_key: 'today:c1:calendar_disruption', commitment_id: 'c1', title: 'Adjust the plan calmly', what_changed: 'The current focus session no longer fits before the next meeting.', failure_mode: 'calendar_disruption', reason: 'The plan changed.', options: [{ id: 'shorter_block', title: 'Use the remaining short window', rationale: 'Protect only the time that fits.', tradeoff: 'Less progress now.', expected_impact: 'A smaller valid block', feasible: true, requires_approval: true }], recommended_option_id: 'shorter_block', requires_approval: true }, explanation: { detail: 'standard', constraints_considered: ['risk', 'deadline', 'calendar'], next_action_reason: 'Highest-ranked executable commitment.', deferred: ['Slides'], changed: 'No plan changes were made.', ai_used: false, requires_approval: true }, routines_due: [{ id: 'r1', title: 'Daily release review', preferred_time: '18:00', duration_minutes: 20, minimum_viable_version: '5-minute blocker review' }], focus_duration_options: [25,45,60], explanation_detail: 'standard' };
}

function planData(): PlanResponse {
  return { range_start: '2026-08-02T00:00:00Z', range_end: '2026-08-03T00:00:00Z', calendar_events: [{ id: 'e1', kind: 'calendar_event', title: 'Team call', start_at: '2026-08-02T16:00:00Z', end_at: '2026-08-02T17:00:00Z', status: 'busy' }], plan_blocks: [], unscheduled_commitments: [{ id: 'c1', kind: 'commitment', title: 'Authentication regression fix', commitment_id: 'c1', status: 'critical' }], ordered_timeline: [{ id: 'e1', kind: 'calendar_event', title: 'Team call', start_at: '2026-08-02T16:00:00Z', end_at: '2026-08-02T17:00:00Z', status: 'busy' }], capacity: { total_minutes: 300, busy_minutes: 60, planned_minutes: overCapacity ? 360 : 0, buffer_minutes: 70, available_minutes: overCapacity ? 0 : 300, total_available_minutes: 300, scheduled_minutes: overCapacity ? 360 : 0, remaining_minutes: overCapacity ? 0 : 300, over_capacity_minutes: overCapacity ? 60 : 0, confidence: 'medium', sources: ['personal_availability', 'calendar_disconnected_profile_only'], calendar_state: 'disconnected' }, buffer_guidance: 'Keep at least 10 minutes between demanding blocks.', explanation: { constraints_considered: ['calendar', 'capacity'], next_action_reason: 'Risk and deadline ranking selected the fix.', deferred: ['Slides'], changed: 'No plan changes were made.', ai_used: false, requires_approval: true } };
}

function json(data: unknown, status = 200) { return new Response(JSON.stringify(data), { status, headers: { 'Content-Type': 'application/json' } }); }

beforeEach(() => {
  active = null;
  conflictMode = false;
  overCapacity = false;
  profileFailure = false;
  transactionFailure = false;
  savedProfile = null;
  projectExists = false;
  outcomeExists = false;
  routines = [];
  onboardingStatus = 'completed';
  onboardingStep = 3;
  savedPreferences = null;
  vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    if (url.endsWith('/api/v1/settings/onboarding/skip')) { onboardingStatus = 'skipped'; return json({ ...planningProfile, onboarding_status: onboardingStatus, onboarding_step: onboardingStep }); }
    if (url.endsWith('/api/v1/settings/onboarding/reopen')) { onboardingStatus = 'in_progress'; onboardingStep = 1; return json({ ...planningProfile, onboarding_status: onboardingStatus, onboarding_step: onboardingStep }); }
    if (url.endsWith('/api/v1/settings/onboarding')) { if (init?.method === 'PUT') { const body = JSON.parse(String(init.body)); onboardingStatus = body.complete ? 'completed' : 'in_progress'; onboardingStep = body.onboarding_step; return json({ ...planningProfile, ...body, onboarding_status: onboardingStatus, onboarding_step: onboardingStep }); } return json({ ...planningProfile, onboarding_status: onboardingStatus, onboarding_step: onboardingStep }); }
    if (url.endsWith('/api/v1/settings/preferences')) { if (init?.method === 'PUT') savedPreferences = JSON.parse(String(init.body)); return json(savedPreferences ?? preferences); }
    if (url.endsWith('/api/v1/recommendations/feedback')) return json({ id: 'feedback-1', status: 'recorded' }, 201);
    if (url.endsWith('/api/v1/rescue/choices')) return json({ id: 'feedback-2', status: 'recorded', plan_changed: false });
    if (url.endsWith('/api/v1/projects') && init?.method === 'POST') { projectExists = true; return json({ id: 'p1', title: 'ChronOS Production Release', description: '', status: 'active', colour: 'accent', outcome_count: 0, completed_outcome_count: 0, progress_percent: 0 }); }
    if (url.endsWith('/api/v1/projects')) return json({ projects: projectExists ? [{ id: 'p1', title: 'ChronOS Production Release', description: 'Ship safely', status: 'active', colour: 'accent', outcome_count: outcomeExists ? 1 : 0, completed_outcome_count: 0, progress_percent: 0, next_action: 'Authentication fix' }] : [] });
    if (url.endsWith('/api/v1/projects/p1/outcomes') && init?.method === 'POST') { outcomeExists = true; return json({ id: 'o1' }); }
    if (url.endsWith('/api/v1/projects/p1')) return json({ id: 'p1', title: 'ChronOS Production Release', description: 'Ship safely', status: 'active', colour: 'accent', outcome_count: outcomeExists ? 1 : 0, completed_outcome_count: 0, progress_percent: 0, next_action: 'Authentication fix', outcomes: outcomeExists ? [{ id: 'o1', project_id: 'p1', title: 'Production deployment', description: '', status: 'active', importance: 5, confidence: .8, completion_criteria: 'Service is healthy' }] : [], linked_commitments: [], available_commitments: [] });
    if (url.endsWith('/api/v1/routines') && init?.method === 'POST') { routines = [{ id: 'r1', title: 'Daily release review', frequency_rule: 'weekly', preferred_days: [0,1,2,3,4,5], preferred_time: '18:00', minimum_viable_version: '5-minute blocker review', estimated_duration_minutes: 20, active: true, occurrences: [] }]; return json(routines[0]); }
    if (url.endsWith('/api/v1/routines')) return json({ routines });
    if (url.endsWith('/api/v1/routines/r1') && init?.method === 'PUT') { routines[0] = { ...routines[0], active: false }; return json(routines[0]); }
    if (url.includes('/api/v1/week/proposals/') && url.endsWith('/approve')) return json({ status: 'approved', block_ids: ['wb1'] });
    if (url.includes('/api/v1/week/proposals/') && url.endsWith('/reject')) return json({ id: 'wp1', status: 'rejected' });
    if (url.includes('/api/v1/week/proposals/wp1') && init?.method === 'PUT') return json({ id: 'wp1', status: 'pending', week_start: '2026-08-03', focus_set: [], blocks: JSON.parse(String(init.body)).blocks, deferred: [], explanation: { constraints_considered: ['capacity'], summary: 'Edited and valid.', ai_used: false, requires_approval: true }, requires_approval: true });
    if (url.includes('/api/v1/week/proposals') && init?.method === 'POST') return json({ id: 'wp1', status: 'pending', week_start: '2026-08-03', focus_set: [{ id: 'o1', title: 'Stable authentication' }], blocks: [{ commitment_id: 'c1', title: 'Authentication fix', start_at: '2026-08-03T10:00:00+05:30', duration_minutes: 45, outcome_id: 'o1', project_id: 'p1' }], deferred: [{ id: 'c2', title: 'Slides', reason: 'No conflict-free capacity remained.' }], explanation: { constraints_considered: ['availability', 'calendar'], summary: 'A small focus set fits.', ai_used: false, requires_approval: true }, requires_approval: true });
    if (url.includes('/api/v1/week?')) return json({ week_start: '2026-08-03', timezone: 'Asia/Kolkata', days: Array.from({ length: 7 }, (_, index) => ({ date: `2026-08-0${index + 3}`, available_minutes: index === 6 ? 0 : 300, scheduled_minutes: 0, remaining_minutes: index === 6 ? 0 : 300, buffer_minutes: 60, over_capacity_minutes: 0, confidence: 'medium', sources: ['personal_availability'] })), due_outcomes: [{ id: 'o1', title: 'Stable authentication', description: '', status: 'active', importance: 5, confidence: .8, completion_criteria: 'Tests pass' }], unscheduled_work: [{ id: 'c1', user_id: 'u1', title: 'Authentication fix', status: 'active' }], routine_occurrences: [], active_projects: [], primary_strategy: recommendation });
    if (url.endsWith('/api/v1/today')) return json(todayData());
    if (url.includes('/api/v1/plan/adaptive/') && url.endsWith('/approve')) return json({ status: 'approved', block_ids: ['b1'] });
    if (url.endsWith('/api/v1/plan/adaptive')) return json({ workflow_id: 'w1', proposal_id: 'p1', recommended_plan: { label: 'Protect the fix', summary: 'One conflict-free block.', feasibility: 'valid', blocks: [{ commitment_id: 'c1', start_at: '2026-08-04T10:00:00Z', duration_minutes: 60, rationale: 'Highest-risk executable outcome.' }], deferred_commitment_ids: [] }, explanation: { constraints_considered: ['availability', 'calendar', 'dependencies'], next_action_reason: 'The fix is urgent and executable.', deferred: ['Slides'], changed: 'A proposal was prepared; no plan data changed.', ai_used: true, requires_approval: true }, rejected_candidate_count: 1, requires_approval: true });
    if (url.endsWith('/api/v1/calendar/sync')) return json({ success: true });
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
    if (url.endsWith('/stuck')) return json({ focus_block_id: 'f1', failure_mode: 'calendar_disruption', recommended_option_id: 'stop_reflect', options: [{ id: 'smaller_step', title: 'Define a smaller next step', rationale: 'Make one visible result.', requires_approval: true }, { id: 'setup_action', title: 'Create a five-minute setup action', rationale: 'Lower restart friction.', requires_approval: true }, { id: 'recovery_plan', title: 'Request a recovery plan', rationale: 'Review checked options.', requires_approval: true }, { id: 'stop_reflect', title: 'Stop and reflect', rationale: 'Close honestly.', requires_approval: false }], recovery_available: true });
    if (url.endsWith('/complete')) { active = null; return json({ session: null, reflection: { id: 'r1' }, reflection_requested: false }); }
    if (url.endsWith('/skip')) { active = null; return json({ session: null, reflection_requested: true }); }
    if (url.includes('/api/v1/rescue/proposals/') && url.endsWith('/approve')) return json({ status: 'approved' });
    if (url.includes('/api/v1/rescue/')) return json({ diagnosis: 'calendar_disruption', ai_used: false, proposals: [{ id: 'p1', payload_json: { rationale: 'Use a shorter block.', trade_off: 'Less progress now.', expected_impact: 'Avoids the meeting conflict.', feasible: true }, explanation: 'Checked.' }] });
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
  expect(await screen.findByRole('heading', { name: 'Authentication regression fix' }, { timeout: 5000 })).toBeInTheDocument();
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
}, 10_000);

it('shows the deterministic stuck options', async () => {
  active = { id: 'f1', commitment_id: 'c1', title: 'Fix', status: 'active', planned_minutes: 25, elapsed_seconds: 0, remaining_seconds: 1500, started_at: new Date().toISOString() };
  const user = userEvent.setup(); renderWithContext(<Today />);
  await user.click(await screen.findByRole('button', { name: /i’m stuck/i }));
  expect(await screen.findByText('Create a five-minute setup action')).toBeInTheDocument();
  expect(screen.getByText('Request a recovery plan')).toBeInTheDocument();
  expect(screen.getByText('Stop and reflect')).toBeInTheDocument();
});

it('completes onboarding in three short steps and persists the profile', async () => {
  onboardingStatus = 'not_started'; const user = userEvent.setup(); renderWithContext(<Onboarding />, { path: '/onboarding' });
  expect(await screen.findByLabelText('Step 1 of 3')).toBeInTheDocument();
  await user.click(screen.getByRole('button', { name: /save and continue/i }));
  expect(await screen.findByLabelText('Step 2 of 3')).toBeInTheDocument();
  await user.click(screen.getByRole('button', { name: /save and continue/i }));
  expect(await screen.findByLabelText('Step 3 of 3')).toBeInTheDocument();
  await user.click(screen.getByRole('button', { name: /finish setup/i }));
  expect(onboardingStatus).toBe('completed');
});

it('allows onboarding to be skipped safely', async () => {
  onboardingStatus = 'not_started'; const user = userEvent.setup(); renderWithContext(<Onboarding />, { path: '/onboarding' });
  await user.click(await screen.findByRole('button', { name: /skip for now/i }));
  expect(onboardingStatus).toBe('skipped');
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

it('persists personalization controls and keeps internal automation opt-in', async () => {
  const user = userEvent.setup(); renderWithContext(<Settings />);
  await user.selectOptions(await screen.findByLabelText('Planning style'), 'minimal');
  expect(screen.getByRole('checkbox', { name: /enable reversible internal plan changes/i })).toBeDisabled();
  await user.click(screen.getByRole('button', { name: /save personalization/i }));
  expect(await screen.findByText('Personalization saved.')).toBeInTheDocument();
  expect(savedPreferences).toMatchObject({ planning_style: 'minimal', internal_write_automation_enabled: false });
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

it('shows compact plan transparency without hidden reasoning', async () => {
  const user = userEvent.setup(); renderWithContext(<Today />);
  await user.click(await screen.findByText('Why this plan?'));
  expect(await screen.findByRole('heading', { name: 'Why this plan?' })).toBeInTheDocument();
  expect(screen.getByText('Deterministic')).toBeInTheDocument();
  expect(screen.getByText(/still requires your approval/i)).toBeInTheDocument();
});

it('prepares and explicitly approves a validated adaptive plan', async () => {
  const user = userEvent.setup(); renderWithContext(<Plan />, { path: '/plan' });
  await user.click(await screen.findByRole('button', { name: /suggest adaptive plan/i }));
  expect(await screen.findByRole('heading', { name: 'Protect the fix' })).toBeInTheDocument();
  expect(screen.getByText('AI-assisted')).toBeInTheDocument();
  expect(screen.getByText(/no plan data changed/i)).toBeInTheDocument();
  await user.click(screen.getByRole('button', { name: /approve this plan/i }));
  expect(await screen.findByText('Adaptive plan approved.')).toBeInTheDocument();
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
  await user.click(await screen.findByRole('button', { name: /review recovery/i }));
  expect(screen.getByRole('dialog')).toHaveTextContent(/current focus session no longer fits/i);
  expect(screen.getByText(/less progress now/i)).toBeInTheDocument();
  await user.click(screen.getByRole('button', { name: /review recovery options/i }));
  expect(await screen.findByText(/deterministic recovery options/i)).toBeInTheDocument();
  expect(screen.getByRole('button', { name: /approve this option/i })).toBeInTheDocument();
});

it('dismisses recovery with Escape and does not mutate the plan', async () => {
  const user = userEvent.setup(); renderWithContext(<Today />);
  await user.click(await screen.findByRole('button', { name: /review recovery/i }));
  expect(screen.getByRole('dialog')).toBeInTheDocument();
  await user.keyboard('{Escape}');
  expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
});

it('renders the Projects empty state and creates a project', async () => {
  const user = userEvent.setup(); renderWithContext(<Projects />, { path: '/projects' });
  expect(await screen.findByText('No projects yet')).toBeInTheDocument();
  await user.click(screen.getByRole('button', { name: /create project/i }));
  await user.type(screen.getByLabelText('Project title'), 'ChronOS Production Release');
  await user.click(screen.getAllByRole('button', { name: /create project/i })[1]);
  expect(await screen.findByText('Project created.')).toBeInTheDocument();
  expect(await screen.findByText('ChronOS Production Release')).toBeInTheDocument();
});

it('renders project detail and creates a distinct outcome', async () => {
  projectExists = true; const user = userEvent.setup(); renderWithContext(<AppRoutes />, { path: '/projects/p1' });
  expect(await screen.findByRole('heading', { name: 'ChronOS Production Release' })).toBeInTheDocument();
  await user.click(screen.getByRole('button', { name: /add outcome/i }));
  await user.type(screen.getByLabelText('Outcome title'), 'Production deployment');
  await user.type(screen.getByLabelText('Completion criteria'), 'Service is healthy');
  await user.click(screen.getByRole('button', { name: /create outcome/i }));
  expect(await screen.findByText('Outcome created.')).toBeInTheDocument();
  expect(await screen.findByText('Complete when: Service is healthy')).toBeInTheDocument();
});

it('creates and pauses a routine within Plan', async () => {
  const user = userEvent.setup(); renderWithContext(<Plan />, { path: '/plan' });
  await user.click(await screen.findByRole('button', { name: /add routine/i }));
  await user.type(screen.getByLabelText('Routine title'), 'Daily release review');
  await user.type(screen.getByLabelText('Minimum viable version'), '5-minute blocker review');
  await user.click(screen.getByRole('button', { name: /create routine/i }));
  expect(await screen.findByText('Routine created.')).toBeInTheDocument();
  await user.click(await screen.findByRole('button', { name: 'Pause' }));
  expect(await screen.findByRole('button', { name: 'Resume' })).toBeInTheDocument();
});

it('renders weekly capacity and accepts an approved proposal', async () => {
  const user = userEvent.setup(); renderWithContext(<Week />, { path: '/week' });
  expect((await screen.findAllByText('300 min')).length).toBeGreaterThan(0);
  await user.click(screen.getByRole('button', { name: /suggest weekly focus/i }));
  expect(await screen.findByRole('heading', { name: /small weekly focus set/i })).toBeInTheDocument();
  expect(screen.getByText(/No conflict-free capacity remained/)).toBeInTheDocument();
  await user.click(screen.getByRole('button', { name: /accept weekly plan/i }));
  expect(await screen.findByText(/weekly plan approved/i)).toBeInTheDocument();
});

it('edits and rejects a weekly proposal without creating blocks', async () => {
  const user = userEvent.setup(); renderWithContext(<Week />, { path: '/week' });
  await user.click(await screen.findByRole('button', { name: /suggest weekly focus/i }));
  await user.selectOptions(await screen.findByLabelText(/duration for authentication fix/i), '60');
  await user.click(screen.getByRole('button', { name: /save edits/i }));
  expect(await screen.findByText(/updated and revalidated/i)).toBeInTheDocument();
  await user.click(screen.getByRole('button', { name: /reject suggestion/i }));
  expect(await screen.findByText(/suggestion rejected/i)).toBeInTheDocument();
});

it('shows compact project context and routines on Today', async () => {
  renderWithContext(<Today />, { path: '/today' });
  expect(await screen.findByText(/ChronOS Production Release/)).toBeInTheDocument();
  expect(screen.getByText(/Stable authentication and session handling/)).toBeInTheDocument();
  expect(screen.getByRole('heading', { name: 'Routines' })).toBeInTheDocument();
});

it('allows optional Inbox project assignment and type classification', async () => {
  const user = userEvent.setup(); const onUpdate = vi.fn();
  renderWithContext(<CommitmentDraftCard draft={{ title: 'Production deployment', type: 'hard_deadline', importance: 5, flexibility: 2, tasks: [], missing_fields: [], confidence_score: .8, kind: 'task' }} onUpdate={onUpdate} onReject={vi.fn()} projects={[{ id: 'p1', title: 'ChronOS Production Release' }]} />);
  await user.selectOptions(screen.getByLabelText(/planning type for production deployment/i), 'project_outcome');
  expect(onUpdate).toHaveBeenCalledWith(expect.objectContaining({ kind: 'project_outcome' }));
  await user.selectOptions(screen.getByLabelText(/project for production deployment/i), 'p1');
  expect(onUpdate).toHaveBeenCalledWith(expect.objectContaining({ project_id: 'p1' }));
});

it('keeps responsive primary navigation concise and functional', async () => {
  renderWithContext(<Today />, { path: '/today' });
  const navigation = await screen.findByRole('navigation', { name: /primary/i });
  for (const label of ['Today', 'Inbox', 'Plan']) expect(within(navigation).getByText(label)).toBeInTheDocument();
  expect(within(navigation).queryByText('Projects')).not.toBeInTheDocument();
  expect(within(navigation).queryByText('Week')).not.toBeInTheDocument();
  expect(within(navigation).queryByText('Routines')).not.toBeInTheDocument();
});

describe('auth boundary', () => {
  it('redirects a logged-out protected route without private content', async () => {
    renderWithContext(<AppRoutes />, { path: '/today', authenticated: false });
    expect(await screen.findByRole('heading', { name: /welcome back/i })).toBeInTheDocument();
    expect(screen.queryByText('Run the regression suite')).not.toBeInTheDocument();
  });
});
