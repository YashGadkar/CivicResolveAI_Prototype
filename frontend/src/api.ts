import type { Analytics, AssistantResponse, ComplaintAnalysis, ComplaintBatchAnalysis, EnrichedTicket, Incident, LocationVerification, PlatformAnalytics, StaffMember, StaffTicket, Ticket, User } from "./types";

const API = import.meta.env.VITE_API_URL || "/api/v1";
const pendingTicketKeys = new Map<string, string>();
const pendingBatchKeys = new Map<string, string[]>();

function localBackendHint() {
  if (typeof window === "undefined") return "The CivicResolve backend could not be reached. Please retry.";
  const local = ["localhost", "127.0.0.1"].includes(window.location.hostname);
  return local
    ? "The CivicResolve backend could not be reached. Start the backend on http://localhost:8000 and keep it running, then retry."
    : "The CivicResolve service could not be reached. Please retry in a moment.";
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const { headers, body, ...rest } = options;
  const isForm = typeof FormData !== "undefined" && body instanceof FormData;
  let response: Response;

  try {
    response = await fetch(`${API}${path}`, {
      ...rest,
      body,
      credentials: "include",
      headers: isForm ? { ...(headers || {}) } : { "Content-Type": "application/json", ...(headers || {}) },
    });
  } catch (error) {
    if (error instanceof TypeError) throw new Error(localBackendHint());
    throw error;
  }

  if (!response.ok) {
    const payload = await response.json().catch(() => ({ detail: "Request failed." }));
    const detail = typeof payload.detail === "string" ? payload.detail : payload.detail?.message || payload.detail?.[0]?.msg || "Request failed.";
    throw new Error(detail);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export type ComplaintPayload = { complaint: string; location?: string; landmark?: string; contact?: string; duplicate_of?: string; verify_location?: boolean; };
export type TranslationLanguage = { code: string; name: string };
export type TranslationResult = {
  original_text: string;
  translated_text: string;
  source_language: string;
  target_language: string;
  target_language_name: string;
  provider: string;
};

async function createTicket(payload: ComplaintPayload, explicitIdempotencyKey?: string): Promise<Ticket> {
  const payloadKey = JSON.stringify(payload);
  const idempotencyKey = explicitIdempotencyKey || pendingTicketKeys.get(payloadKey) || crypto.randomUUID();
  if (!explicitIdempotencyKey) pendingTicketKeys.set(payloadKey, idempotencyKey);
  const ticket = await request<Ticket>("/tickets", { method: "POST", headers: { "Idempotency-Key": idempotencyKey }, body: payloadKey });
  if (!explicitIdempotencyKey) pendingTicketKeys.delete(payloadKey);
  return ticket;
}

async function createTickets(payloads: ComplaintPayload[]): Promise<Ticket[]> {
  const batchKey = JSON.stringify(payloads);
  const keys = pendingBatchKeys.get(batchKey) || payloads.map(() => crypto.randomUUID());
  pendingBatchKeys.set(batchKey, keys);
  const tickets: Ticket[] = [];
  for (let i = 0; i < payloads.length; i += 1) tickets.push(await createTicket(payloads[i], keys[i]));
  pendingBatchKeys.delete(batchKey);
  return tickets;
}

async function uploadEvidence(code: string, file: File, kind = "CITIZEN_EVIDENCE") {
  const form = new FormData();
  form.append("file", file);
  return request<EnrichedTicket>(`/platform/tickets/${encodeURIComponent(code)}/evidence?kind=${encodeURIComponent(kind)}`, { method: "POST", body: form });
}

async function downloadEvidence(attachmentId: string, filename: string) {
  let response: Response;
  try {
    response = await fetch(`${API}/platform/attachments/${encodeURIComponent(attachmentId)}`, { credentials: "include" });
  } catch (error) {
    if (error instanceof TypeError) throw new Error(localBackendHint());
    throw error;
  }
  if (!response.ok) {
    const payload = await response.json().catch(() => ({ detail: "Evidence could not be opened." }));
    throw new Error(typeof payload.detail === "string" ? payload.detail : "Evidence could not be opened.");
  }
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 30000);
}

export const api = {
  signUp: (payload: { name: string; email: string; password: string }) => request<User>("/auth/signup", { method: "POST", body: JSON.stringify(payload) }),
  login: (payload: { email: string; password: string }) => request<User>("/auth/login", { method: "POST", body: JSON.stringify(payload) }),
  employeeLogin: (payload: { email: string; password: string }) => request<User>("/auth/employee-login", { method: "POST", body: JSON.stringify(payload) }),
  logout: () => request<void>("/auth/logout", { method: "POST" }),
  me: () => request<User>("/auth/me"),
  verifyLocation: (location: string) => request<LocationVerification>("/locations/verify", { method: "POST", body: JSON.stringify({ location }) }),
  reverseDeviceLocation: (latitude: number, longitude: number) => request<LocationVerification>("/device-location/reverse", { method: "POST", body: JSON.stringify({ latitude, longitude }) }),
  analyze: (payload: ComplaintPayload) => request<ComplaintAnalysis>("/complaints/analyze", { method: "POST", body: JSON.stringify(payload) }),
  analyzeBatch: (payload: ComplaintPayload) => request<ComplaintBatchAnalysis>("/complaints/analyze-batch-v2", { method: "POST", body: JSON.stringify(payload) }),
  createTicket,
  createTickets,
  getTicket: (code: string) => request<Ticket>(`/tickets/${encodeURIComponent(code)}`),
  getStaffTicket: (code: string) => request<StaffTicket>(`/staff/tickets/${encodeURIComponent(code)}`),
  myTickets: () => request<Ticket[]>("/tickets/mine"),
  listTickets: () => request<Ticket[]>("/tickets"),
  simulateBreach: (code: string) => request<Ticket>(`/tickets/${encodeURIComponent(code)}/simulate-breach`, { method: "POST" }),
  updateStatus: (code: string, status: string, note?: string) => request<Ticket>(`/tickets/${encodeURIComponent(code)}/status`, { method: "PATCH", body: JSON.stringify({ status, note }) }),
  analytics: () => request<Analytics>("/analytics"),

  platformMine: () => request<EnrichedTicket[]>("/platform/tickets/mine"),
  platformTicket: (code: string) => request<EnrichedTicket>(`/platform/tickets/${encodeURIComponent(code)}`),
  platformStaffTickets: () => request<EnrichedTicket[]>("/platform/staff/tickets"),
  staffDepartments: () => request<string[]>("/platform/staff/departments"),
  staffMembers: () => request<StaffMember[]>("/platform/staff/members"),
  translationLanguages: () => request<TranslationLanguage[]>("/platform/staff/translation-languages"),
  translateTicket: (code: string, targetLanguage: string) => request<TranslationResult>(`/platform/staff/tickets/${encodeURIComponent(code)}/translate`, { method: "POST", body: JSON.stringify({ target_language: targetLanguage }) }),
  deleteTicket: (code: string) => request<EnrichedTicket>(`/platform/tickets/${encodeURIComponent(code)}`, { method: "DELETE" }),
  restoreTicket: (code: string) => request<EnrichedTicket>(`/platform/tickets/${encodeURIComponent(code)}/restore`, { method: "POST" }),
  confirmResolution: (code: string, payload: { resolved: boolean; rating?: number; feedback?: string }) => request<EnrichedTicket>(`/platform/tickets/${encodeURIComponent(code)}/confirm`, { method: "POST", body: JSON.stringify(payload) }),
  resolveWithNote: (code: string, note: string) => request<EnrichedTicket>(`/platform/staff/tickets/${encodeURIComponent(code)}/resolve`, { method: "POST", body: JSON.stringify({ note }) }),
  transferTicket: (code: string, department: string, reason: string) => request<EnrichedTicket>(`/platform/staff/tickets/${encodeURIComponent(code)}/transfer`, { method: "POST", body: JSON.stringify({ department, reason }) }),
  assignTicket: (code: string, officer?: string) => request<EnrichedTicket>(`/platform/staff/tickets/${encodeURIComponent(code)}/assign`, { method: "POST", body: JSON.stringify({ officer: officer || null }) }),
  uploadEvidence,
  downloadEvidence,
  evidenceUrl: (attachmentId: string) => `${API}/platform/attachments/${encodeURIComponent(attachmentId)}`,
  incidents: () => request<Incident[]>("/platform/incidents"),
  platformAnalytics: () => request<PlatformAnalytics>("/platform/analytics"),
  assistant: (message: string) => request<AssistantResponse>("/platform/assistant", { method: "POST", body: JSON.stringify({ message }) }),
};
