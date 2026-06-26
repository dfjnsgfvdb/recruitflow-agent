import { request } from './http';
import type { Interview } from '../types/interview';

export function getInterviews() {
  return request<Interview[]>({
    url: '/api/interviews',
    method: 'GET',
  });
}
