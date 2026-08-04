import { apiFetch, apiUrl, getApiErrorMessage } from './api';
import type { PlanningProfile } from '../types/api';

export async function loadOnboarding(): Promise<PlanningProfile> {
  const response = await apiFetch(apiUrl('/api/v1/settings/onboarding'));
  if (!response.ok) throw new Error(await getApiErrorMessage(response, 'Setup could not be loaded.'));
  return response.json();
}
