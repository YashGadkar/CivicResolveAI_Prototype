export type Priority = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export interface User { id: string; name: string; email: string; role: string; created_at: string; }
export interface AgentStage { name: string; status: "WAITING" | "PROCESSING" | "COMPLETED" | "ACTION REQUIRED"; output: string; processing_ms: number; }
export interface DuplicateCandidate { ticket_code: string; summary: string; similarity: number; }
export interface LocationVerification { input: string; valid: boolean; canonical_name: string | null; latitude: number | null; longitude: number | null; provider: string; message: string; }

export interface ComplaintAnalysis {
  source_text?: string | null;
  category: string; location: string | null; landmark: string | null; duration: string | null;
  priority: Priority; urgency: Priority; department: string; missing_information: string[];
  clarification_questions: string[]; resolution_recommendation: string[]; language: string; language_code: string;
  detected_script: string; analysis_mode: string; confidence: number; reasoning_summary: string; citizen_response: string;
  agent_trace: AgentStage[]; duplicate_candidates: DuplicateCandidate[];
  location_verified?: boolean | null; location_display_name?: string | null; location_verification_message?: string | null;
}

export interface ComplaintBatchAnalysis { language: string; language_code: string; issue_count: number; issues: ComplaintAnalysis[]; }

export interface Ticket {
  ticket_code: string; complaint: string; language: string; location: string; landmark: string | null; category: string;
  duration: string | null; priority: Priority; urgency: Priority; department: string; confidence: number; status: string;
  sla_deadline: string; sla_state: string; resolution_recommendation: string[]; citizen_response: string; reasoning_summary: string;
  assigned_officer: string | null; duplicate_of: string | null; created_at: string; updated_at: string;
  audit_events: { event: string; detail: string; created_at: string }[];
}

export interface StaffTicket extends Ticket { citizen: { name: string; email: string; contact: string | null } | null; }
export interface TicketMeta {
  ward: string | null; zone: string | null; city: string | null; latitude: number | null; longitude: number | null;
  emergency: boolean; incident_key: string | null; related_reports: number; archived: boolean; citizen_confirmation: string;
  rating: number | null; feedback: string | null; resolution_note: string | null;
}
export interface Attachment { id: string; kind: string; original_name: string; content_type: string; size_bytes: number; created_at: string; }
export interface EnrichedTicket { ticket: Ticket; meta: TicketMeta; attachments: Attachment[]; citizen: { name: string; email: string; contact?: string | null } | null; }
export interface AssistantAction { type: "NONE" | "OPEN_TICKET" | "OPEN_QUEUE" | "CREATE_COMPLAINT" | "SHOW_MY_TICKETS"; label?: string | null; value?: string | null; }
export interface AssistantResponse { reply: string; actions: AssistantAction[]; data: Record<string, unknown>; }
export interface Incident { incident_key: string; category: string; location: string; department: string; priority: string; report_count: number; active_count: number; latest_ticket: string; }
export interface PlatformAnalytics { incidents: Incident[]; satisfaction_average: number | null; rated_resolutions: number; archived_tickets: number; emergency_tickets: number; by_ward: Record<string, number>; by_zone: Record<string, number>; }

export interface Analytics {
  label: string; total: number; pending: number; in_progress: number; resolved: number; escalated: number; sla_breaches: number;
  sla_compliance: number; by_category: Record<string, number>; by_department: Record<string, number>; by_priority: Record<string, number>;
  by_status: Record<string, number>; by_location: Record<string, number>;
}
