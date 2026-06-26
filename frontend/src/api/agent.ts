import { request } from './http';
import type { AgentMessageRequest, AgentProcessResponse } from '../types/agent';

export function processAgentMessage(data: AgentMessageRequest) {
  return request<AgentProcessResponse>({
    url: '/api/agent/process-message',
    method: 'POST',
    data,
  });
}
