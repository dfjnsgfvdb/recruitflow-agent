import { request } from './http';
import type {
  CandidateResumeResponse,
  ResumeFile,
  ResumeScreenRequest,
  ResumeScreeningReport,
  ResumeUploadResponse,
} from '../types/resume';

export function uploadResume(formData: FormData) {
  return request<ResumeUploadResponse>({
    url: '/api/resumes/upload',
    method: 'POST',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
}

export function getResumes() {
  return request<ResumeFile[]>({
    url: '/api/resumes',
    method: 'GET',
  });
}

export function getCandidateResume(candidateId: number, options?: { silent?: boolean }) {
  return request<CandidateResumeResponse>({
    url: `/api/candidates/${candidateId}/resume`,
    method: 'GET',
    skipErrorMessage: options?.silent,
  });
}

export function reparseResume(resumeId: number) {
  return request<ResumeUploadResponse>({
    url: `/api/resumes/${resumeId}/reparse`,
    method: 'POST',
  });
}

export function screenResume(resumeId: number, data: ResumeScreenRequest) {
  return request<ResumeScreeningReport>({
    url: `/api/resumes/${resumeId}/screen`,
    method: 'POST',
    data,
  });
}
