import { request } from './http';
import type { ConfirmationActionResponse, PendingAction } from '../types/confirmation';

export function getPendingActions() {
  return request<PendingAction[]>({
    url: '/api/confirmations/pending',
    method: 'GET',
  });
}

export function approvePendingAction(id: number, approved_by = 'HR负责人') {
  return request<ConfirmationActionResponse>({
    url: `/api/confirmations/${id}/approve`,
    method: 'POST',
    data: { approved_by },
  });
}

export function rejectPendingAction(id: number, approved_by = 'HR负责人', reason?: string) {
  return request<ConfirmationActionResponse>({
    url: `/api/confirmations/${id}/reject`,
    method: 'POST',
    data: { approved_by, reason },
  });
}
