export type Priority = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export interface AgentStage {
  name: string;
  status: "WAITING" | "PROCESSING" | "COMPLETED" | "ACTION REQUIRED";
  output: string;
  processing_ms: number;
}

export interface DuplicateCandidate {
  ticket_code: string;
  summary: string;
  similarity: number;
}

export interface ComplaintAnalysis {
  category: string;
  location: string | null;
  landmark: string | null;
  duration: string | null;
  priority: Priority;
  urgency: Priority;
  department: string;
  missing_information: string[];
  clarification_questions: string[];
  resolution_recommendation: string[];
  language: string;
  confidence: number;
  reasoning_summary: string;
  citizen_response: string;
  agent_trace: AgentStage[];
  duplicate_candidates: DuplicateCandidate[];
}

export interface Ticket {
  ticket_code: string;
  complaint: string;
  language: string;
  location: string;
  landmark: string | null;
  category: string;
  duration: string | null;
  priority: Priority;
  urgency: Priority;
  department: string;
  confidence: number;
  status: string;
  sla_deadline: string;
  sla_state: string;
  resolution_recommendation: string[];
  citizen_response: string;
  reasoning_summary: string;
  assigned_officer: string | null;
  duplicate_of: string | null;
  created_at: string;
  updated_at: string;
  audit_events: { event: string; detail: string; created_at: string }[];
}

export interface Analytics {
  label: string;
  total: number;
  pending: number;
  in_progress: number;
  resolved: number;
  escalated: number;
  sla_breaches: number;
  sla_compliance: number;
  by_category: Record<string, number>;
  by_department: Record<string, number>;
  by_priority: Record<string, number>;
  by_status: Record<string, number>;
  by_location: Record<string, number>;
}
