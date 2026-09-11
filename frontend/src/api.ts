import type { Analytics, ComplaintAnalysis, Ticket, User } from "./types";

const API = import.meta.env.VITE_API_URL || "/api/v1";
const pendingTicketKeys = new Map<string, string>();

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API}${path}`, {
    credentials: "include",
    headers: { "Content-Type": "application/json", ...(options?.headers || {}) },
    ...options
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
};

async function createTicket(payload: ComplaintPayload): Promise<Ticket> {
  const payloadKey = JSON.stringify(payload);
  const idempotencyKey = pendingTicketKeys.get(payloadKey) || crypto.randomUUID();
  pendingTicketKeys.set(payloadKey, idempotencyKey);
  const ticket = await request<Ticket>("/tickets", {
    method: "POST",
    headers: { "Idempotency-Key": idempotencyKey },
    body: payloadKey
  });
  pendingTicketKeys.delete(payloadKey);
  return ticket;
}

export const api = {
  signUp: (payload: { name: string; email: string; password: string }) =>
    request<User>("/auth/signup", { method: "POST", body: JSON.stringify(payload) }),
  login: (payload: { email: string; password: string }) =>
    request<User>("/auth/login", { method: "POST", body: JSON.stringify(payload) }),
  logout: () => request<void>("/auth/logout", { method: "POST" }),
  me: () => request<User>("/auth/me"),
  analyze: (payload: ComplaintPayload) =>
    request<ComplaintAnalysis>("/complaints/analyze", { method: "POST", body: JSON.stringify(payload) }),
  createTicket,
  getTicket: (code: string) => request<Ticket>(`/tickets/${encodeURIComponent(code)}`),
  myTickets: () => request<Ticket[]>("/tickets/mine"),
  listTickets: () => request<Ticket[]>("/tickets"),
  simulateBreach: (code: string) => request<Ticket>(`/tickets/${encodeURIComponent(code)}/simulate-breach`, { method: "POST" }),
  updateStatus: (code: string, status: string, note?: string) =>
    request<Ticket>(`/tickets/${encodeURIComponent(code)}/status`, { method: "PATCH", body: JSON.stringify({ status, note }) }),
  analytics: () => request<Analytics>("/analytics")
};
