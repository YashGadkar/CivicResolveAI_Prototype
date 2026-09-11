import type { ReactNode } from "react";
import { BellRing, Bot, CheckCircle2, X } from "lucide-react";
import { Link } from "react-router-dom";
import { Button } from "./ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import type { Ticket } from "../types";
import { cn } from "../lib/utils";

export type NoticeState = { tone: "info" | "success" | "error"; title: string; message: string } | null;

export function Toast({ notice, onClose }: { notice: NonNullable<NoticeState>; onClose: () => void }) {
  const tone = notice.tone === "error" ? "border-rose-200 bg-rose-50 text-rose-900" : notice.tone === "success" ? "border-emerald-200 bg-emerald-50 text-emerald-900" : "border-blue-200 bg-blue-50 text-blue-900";
  return <div className={cn("fixed right-4 top-5 z-[70] w-[min(92vw,390px)] rounded-2xl border p-4 shadow-2xl", tone)} role="status"><div className="flex items-start gap-3"><BellRing className="mt-0.5 shrink-0" size={18}/><div className="min-w-0 flex-1"><div className="font-black">{notice.title}</div><p className="mt-1 text-sm leading-5 opacity-80">{notice.message}</p></div><button className="rounded-lg p-1 opacity-60 hover:bg-black/5 hover:opacity-100" onClick={onClose} aria-label="Dismiss"><X size={16}/></button></div></div>;
}

export function Page({ title, eyebrow, subtitle, children }: { title: string; eyebrow: string; subtitle: string; children: ReactNode }) {
  return <main className="mx-auto max-w-7xl px-4 py-10 lg:px-8"><p className="text-xs font-bold uppercase tracking-[.22em] text-teal-700">{eyebrow}</p><h1 className="mt-2 text-3xl font-black tracking-tight text-[#081525] sm:text-4xl">{title}</h1><p className="mb-8 mt-2 max-w-3xl text-sm leading-6 text-slate-500">{subtitle}</p>{children}</main>;
}

export function Field({ label, children }: { label: string; children: ReactNode }) { return <label className="block"><span className="mb-2 block text-sm font-bold text-slate-800">{label}</span>{children}</label>; }
export function Metric({ label, value }: { label: string; value: string }) { return <div className="rounded-xl border border-slate-200 bg-white p-3.5"><div className="text-[10px] font-black uppercase tracking-[.14em] text-slate-400">{label}</div><div className="mt-1 text-sm font-bold text-slate-900">{value}</div></div>; }
export function DarkMetric({ label, value }: { label: string; value: string }) { return <div className="rounded-2xl border border-white/10 bg-white/[.06] p-4"><div className="text-[10px] font-bold uppercase tracking-[.16em] text-slate-400">{label}</div><b className="mt-1 block text-sm text-white">{value}</b></div>; }
export function Kpi({ label, value }: { label: string; value: string }) { return <Card className="border-slate-200"><CardContent className="pt-5"><div className="text-[10px] font-black uppercase tracking-[.15em] text-slate-400">{label}</div><div className="mt-2 text-3xl font-black text-[#081525]">{value}</div></CardContent></Card>; }

export function statusProgress(status: string) { if (status === "RESOLVED") return 100; if (status === "IN_PROGRESS") return 70; if (status === "ESCALATED") return 65; if (status === "ASSIGNED") return 40; return 15; }
export function ProgressBar({ ticket, compact = false }: { ticket: Ticket; compact?: boolean }) { const p = statusProgress(ticket.status); return <div className={compact ? "min-w-40" : "mt-5"}><div className="mb-1.5 flex items-center justify-between text-xs font-semibold text-slate-500"><span>{ticket.status.replaceAll("_", " ")}</span><span>{p}%</span></div><div className="h-2 overflow-hidden rounded-full bg-slate-200"><div className="h-full rounded-full bg-teal-600" style={{ width: `${p}%` }}/></div></div>; }

export function ProgressCard({ ticket }: { ticket: Ticket }) {
  const p = statusProgress(ticket.status); const steps = [["Submitted",10],["Assigned",35],["In progress",65],["Resolved",100]] as const;
  return <Card className="border-slate-200"><CardHeader><CardTitle>Complaint progress</CardTitle></CardHeader><CardContent><ProgressBar ticket={ticket}/><div className="mt-5 grid grid-cols-4 gap-2">{steps.map(([step, threshold], i) => <div className="text-center" key={step}><span className={cn("mx-auto grid h-8 w-8 place-items-center rounded-full border text-xs font-black", p >= threshold ? "border-teal-600 bg-teal-600 text-white" : "border-slate-300 text-slate-400")}>{i+1}</span><div className="mt-2 text-[11px] font-semibold text-slate-500">{step}</div></div>)}</div></CardContent></Card>;
}

export function TicketView({ ticket }: { ticket: Ticket }) {
  return <Card className="overflow-hidden border-slate-200 shadow-panel"><div className="bg-[#0b1f3a] p-5 text-white"><p className="text-xs font-bold uppercase tracking-[.18em] text-teal-200">Ticket reference</p><div className="mt-1 text-2xl font-black">{ticket.ticket_code}</div></div><CardContent className="pt-5"><div className="grid gap-3 sm:grid-cols-2"><Metric label="Status" value={ticket.status.replaceAll("_"," ")}/><Metric label="Category" value={ticket.category}/><Metric label="Department" value={ticket.department}/><Metric label="Location" value={ticket.location}/><Metric label="Priority" value={ticket.priority}/><Metric label="SLA state" value={ticket.sla_state}/></div><ProgressBar ticket={ticket}/><p className="mt-4 rounded-xl bg-slate-50 p-3 text-sm leading-6 text-slate-600">{ticket.citizen_response}</p><Link to={`/track?ticket=${ticket.ticket_code}`}><Button className="mt-4">Track complaint</Button></Link></CardContent></Card>;
}

export function Audit({ ticket }: { ticket: Ticket }) { return <Card className="border-slate-200 shadow-panel"><CardHeader><CardTitle>Activity history</CardTitle></CardHeader><CardContent className="space-y-5">{ticket.audit_events.map((event,i)=><div className="flex gap-3" key={`${event.event}-${i}`}><CheckCircle2 className="mt-0.5 shrink-0 text-teal-600" size={18}/><div><b className="text-sm text-slate-900">{event.event.replaceAll("_"," ")}</b><p className="mt-0.5 text-sm leading-5 text-slate-500">{event.detail}</p><small className="text-slate-400">{new Date(event.created_at).toLocaleString()}</small></div></div>)}</CardContent></Card>; }
export function EmptyState({ title, body }: { title: string; body: string }) { return <div className="grid min-h-40 place-items-center text-center"><div><Bot className="mx-auto text-slate-300" size={34}/><b className="mt-3 block text-slate-700">{title}</b><p className="mt-1 text-sm text-slate-400">{body}</p></div></div>; }
