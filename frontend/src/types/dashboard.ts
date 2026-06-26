import type { RecruitmentEvent } from './event';

export interface StageDistributionItem {
  stage: string;
  count: number;
}

export interface PositionDistributionItem {
  position_name: string;
  count: number;
}

export interface DashboardSummary {
  total_candidates: number;
  today_new_candidates: number;
  pending_interviews: number;
  offer_count: number;
  timeout_followup_count: number;
  stage_distribution: StageDistributionItem[];
  position_distribution: PositionDistributionItem[];
  recent_events: RecruitmentEvent[];
}
