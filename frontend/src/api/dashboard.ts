import { request } from './http';
import type { DashboardSummary } from '../types/dashboard';

export function getDashboardSummary() {
  return request<DashboardSummary>({
    url: '/api/dashboard/summary',
    method: 'GET',
  });
}
