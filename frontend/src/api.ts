import type { Analytics, ComplaintAnalysis, ComplaintBatchAnalysis, LocationVerification, StaffTicket, Ticket, User } from "./types";

const API = import.meta.env.VITE_API_URL || "/api/v1";
const pendingTicketKeys = new Map<string, string>();
const pendingBatchKeys = new Map<string, string[]>();

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const { headers, ...rest } = options;
  const response = await fetch(`${API}${path}`, {
    ...rest,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(headers || {})
    }
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => ({ detail: "Request failed." }));
    const detail = typeof payload.detail === "string"
      ? payload.detail
      : payload.detail?.message || payload.detail?.[0]?.msg || "Request failed.";
    throw new Error(detail);
  }

  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export type ComplaintPayload = {
  complaint: string;
  location?: string;
  landmark?: string;
  contact?: string;
  duplicate_of?: string;
  verify_location?: boolean;
};

async function createTicket(payload: ComplaintPayload, explicitIdempotencyKey?: string): Promise<Ticket> {
  const payloadKey = JSON.stringify(payload);
  const idempotencyKey = explicitIdempotencyKey || pendingTicketKeys.get(payloadKey) || crypto.randomUUID();
  if (!explicitIdempotencyKey) pendingTicketKeys.set(payloadKey, idempotencyKey);

  const ticket = await request<Ticket>("/tickets", {
    method: "POST",
    headers: { "Idempotency-Key": idempotencyKey },
    body: payloadKey
  });
  if (!explicitIdempotencyKey) pendingTicketKeys.delete(payloadKey);
  return ticket;
}

async function createTickets(payloads: ComplaintPayload[]): Promise<Ticket[]> {
  const batchKey = JSON.stringify(payloads);
  const keys = pendingBatchKeys.get(batchKey) || payloads.map(() => crypto.randomUUID());
  pendingBatchKeys.set(batchKey, keys);
  const tickets: Ticket[] = [];
  for (let i = 0; i < payloads.length; i += 1) {
    tickets.push(await createTicket(payloads[i], keys[i]));
  }
  pendingBatchKeys.delete(batchKey);
  return tickets;
}

export const api = {
  signUp: (payload: { name: string; email: string; password: string }) =>
    request<User>("/auth/signup", { method: "POST", body: JSON.stringify(payload) }),
  login: (payload: { email: string; password: string }) =>
    request<User>("/auth/login", { method: "POST", body: JSON.stringify(payload) }),
  employeeLogin: (payload: { email: string; password: string }) =>
    request<User>("/auth/employee-login", { method: "POST", body: JSON.stringify(payload) }),
  logout: () => request<void>("/auth/logout", { method: "POST" }),
  me: () => request<User>("/auth/me"),
  verifyLocation: (location: string) =>
    request<LocationVerification>("/locations/verify", { method: "POST", body: JSON.stringify({ location }) }),
  analyze: (payload: ComplaintPayload) =>
    request<ComplaintAnalysis>("/complaints/analyze", { method: "POST", body: JSON.stringify(payload) }),
  analyzeBatch: (payload: ComplaintPayload) =>
    request<ComplaintBatchAnalysis>("/complaints/analyze-batch", { method: "POST", body: JSON.stringify(payload) }),
  createTicket,
  createTickets,
  getTicket: (code: string) => request<Ticket>(`/tickets/${encodeURIComponent(code)}`),
  getStaffTicket: (code: string) => request<StaffTicket>(`/staff/tickets/${encodeURIComponent(code)}`),
  myTickets: () => request<Ticket[]>("/tickets/mine"),
  listTickets: () => request<Ticket[]>("/tickets"),
  simulateBreach: (code: string) =>
    request<Ticket>(`/tickets/${encodeURIComponent(code)}/simulate-breach`, { method: "POST" }),
  updateStatus: (code: string, status: string, note?: string) =>
    request<Ticket>(`/tickets/${encodeURIComponent(code)}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status, note })
    }),
  analytics: () => request<Analytics>("/analytics")
};
