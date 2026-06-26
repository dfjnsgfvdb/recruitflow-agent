import { request } from './http';
import type { Candidate } from '../types/candidate';

export function getCandidates() {
  return request<Candidate[]>({
    url: '/api/candidates',
    method: 'GET',
  });
}
