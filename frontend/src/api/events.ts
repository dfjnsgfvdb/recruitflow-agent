import { request } from './http';
import type { RecruitmentEvent } from '../types/event';

export function getEvents() {
  return request<RecruitmentEvent[]>({
    url: '/api/events',
    method: 'GET',
  });
}
