import type { Analytics, ComplaintAnalysis, Ticket } from "./types";

const API = import.meta.env.VITE_API_URL || "/api/v1";
const pendingTicketKeys = new Map<string, string>();

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API}${path}`, {
    headers: { "Content-Type": "application/json", ...(options?.headers || {}) },
    ...options
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({ detail: "Request failed." }));
    const detail = typeof payload.detail === "string" ? payload.detail : payload.detail?.message || "Request failed.";
    throw new Error(detail);
  }
  return response.json() as Promise<T>;
}

export type ComplaintPayload = {
  complaint: string;
  language: string;
  location?: string;
  landmark?: string;
  contact?: string;
  duplicate_of?: string;
};

async function createTicket(payload: ComplaintPayload): Promise<Ticket> {
  const payloadKey = JSON.stringify(payload);
  const idempotencyKey = pendingTicketKeys.get(payloadKey) || crypto.randomUUID();
  pendingTicketKeys.set(payloadKey, idempotencyKey);
  try {
    const ticket = await request<Ticket>("/tickets", {
      method: "POST",
      headers: { "Idempotency-Key": idempotencyKey },
      body: payloadKey
    });
    // The response reached the browser, so a future identical complaint is a new
    // citizen action. If the network fails, the key remains for a safe retry.
    pendingTicketKeys.delete(payloadKey);
    return ticket;
  } catch (error) {
    throw error;
  }
}

export const api = {
  analyze: (payload: ComplaintPayload) =>
    request<ComplaintAnalysis>("/complaints/analyze", { method: "POST", body: JSON.stringify(payload) }),
  createTicket,
  getTicket: (code: string) => request<Ticket>(`/tickets/${encodeURIComponent(code)}`),
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
