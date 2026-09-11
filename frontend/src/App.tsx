import { FormEvent, useEffect, useMemo, useState } from "react";
import {
  Activity, AlertTriangle, ArrowRight, BarChart3, Bot, Building2, CheckCircle2, Clock3,
  FileSearch, Gauge, Landmark, Languages, MapPin, Search, Send, ShieldCheck, Sparkles,
  TicketCheck, Users, Workflow
} from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";
import { Link, NavLink, Route, Routes } from "react-router-dom";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { api, type ComplaintPayload } from "./api";
import { Badge } from "./components/ui/badge";
import { Button } from "./components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "./components/ui/card";
import type { Analytics, ComplaintAnalysis, Ticket } from "./types";
import { cn } from "./lib/utils";

const demoScenarios = [
  { name: "Water supply interruption", text: "There has been no water supply in our area for three days and nobody is responding.", language: "English" },
  { name: "Road pothole", text: "There is a huge pothole near our college and several bikes have nearly fallen.", language: "English" },
  { name: "Garbage not collected", text: "Garbage has not been collected from our street for five days and it is starting to smell.", language: "English" },
  { name: "Broken streetlight", text: "The streetlight outside our building has been broken for two weeks.", language: "English" },
  { name: "Drainage overflow", text: "The drainage line is overflowing near the market and dirty water is entering the road.", language: "English" },
  { name: "Electricity outage", text: "Our neighborhood has had no electricity since yesterday and the transformer is making noise.", language: "English" },
  { name: "Public safety", text: "There is an open manhole near the school and children are walking around it.", language: "English" },
  { name: "Marathi water complaint", text: "आमच्या भागात तीन दिवसांपासून पाणी येत नाही.", language: "Marathi" }
];

function Shell() {
  const nav = [
    ["/submit", "Submit", Send],
    ["/track", "Track", Search],
    ["/officer", "Officer", Building2],
    ["/admin", "Admin", BarChart3],
    ["/command-center", "AI Command Center", Workflow]
  ] as const;

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="sticky top-0 z-40 border-b border-slate-200 bg-white/95 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-5 px-4 py-3 lg:px-8">
          <Link to="/" className="flex items-center gap-3">
            <div className="grid h-10 w-10 place-items-center rounded-xl bg-civic-900 text-white"><Landmark size={21} /></div>
            <div>
              <div className="font-bold tracking-tight text-slate-950">CivicResolve AI</div>
              <div className="text-[11px] font-semibold uppercase tracking-[.18em] text-civic-600">Prototype</div>
            </div>
          </Link>
          <nav className="hidden items-center gap-1 lg:flex">
            {nav.map(([path, label, Icon]) => (
              <NavLink
                key={path}
                to={path}
                className={({ isActive }) => cn(
                  "flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-semibold transition",
                  isActive ? "bg-civic-50 text-civic-700" : "text-slate-600 hover:bg-slate-100 hover:text-slate-950"
                )}
              >
                <Icon size={16} /> {label}
              </NavLink>
            ))}
          </nav>
          <Link className="lg:hidden" to="/submit"><Button size="sm">Submit</Button></Link>
        </div>
      </header>
      <main>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/submit" element={<SubmitPage />} />
          <Route path="/track" element={<TrackPage />} />
          <Route path="/officer" element={<OfficerPage />} />
          <Route path="/admin" element={<AdminPage />} />
          <Route path="/command-center" element={<CommandCenterPage />} />
        </Routes>
      </main>
      <footer className="border-t border-slate-200 bg-white">
        <div className="mx-auto max-w-7xl px-4 py-6 text-xs leading-5 text-slate-500 lg:px-8">
          CivicResolve AI is a hackathon prototype. SLA values are configurable demo rules. Analytics are synthetic/demo data and do not represent official government systems or statistics.
        </div>
      </footer>
    </div>
  );
}

function HomePage() {
  const flow = ["Citizen Complaint", "AI Understanding", "Department Routing", "Action", "Resolution"];
  return (
    <>
      <section className="grid-bg border-b border-slate-200">
        <div className="mx-auto grid max-w-7xl gap-12 px-4 py-16 lg:grid-cols-[1.05fr_.95fr] lg:px-8 lg:py-24">
          <div className="flex flex-col justify-center">
            <div className="mb-5 inline-flex w-fit items-center gap-2 rounded-full border border-civic-100 bg-white px-3 py-1.5 text-xs font-bold text-civic-700">
              <Sparkles size={14} /> AI-assisted civic service orchestration
            </div>
            <h1 className="max-w-3xl text-4xl font-black tracking-[-.035em] text-slate-950 sm:text-5xl lg:text-6xl">
              From Citizen Complaint to Government Action — Automatically.
            </h1>
            <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-600">
              Understand unstructured complaints, detect missing information, route to the responsible department,
              create trackable tickets, monitor configurable SLAs and escalate transparently.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link to="/submit"><Button size="lg">Submit Complaint <ArrowRight className="ml-2" size={18} /></Button></Link>
              <Link to="/track"><Button size="lg" variant="outline">Track Complaint</Button></Link>
              <Link to="/command-center"><Button size="lg" variant="secondary">View Demo</Button></Link>
            </div>
          </div>
          <Card className="overflow-hidden border-civic-100">
            <div className="bg-civic-900 px-6 py-5 text-white">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-bold uppercase tracking-[.2em] text-blue-200">Live workflow preview</p>
                  <h2 className="mt-1 text-xl font-bold">AI Complaint Orchestrator</h2>
                </div>
                <div className="rounded-xl bg-white/10 p-3"><Bot /></div>
              </div>
            </div>
            <CardContent className="space-y-3 pt-5">
              {flow.map((item, index) => (
                <div key={item} className="flex items-center gap-3">
                  <div className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-civic-50 text-sm font-black text-civic-700">{index + 1}</div>
                  <div className="flex-1 rounded-xl border border-slate-200 px-4 py-3 font-semibold text-slate-800">{item}</div>
                  {index < flow.length - 1 && <ArrowRight className="hidden text-slate-300 sm:block" size={18} />}
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      </section>
      <section className="mx-auto max-w-7xl px-4 py-12 lg:px-8">
        <div className="grid gap-4 md:grid-cols-3">
          {[
            [ShieldCheck, "Transparent decisions", "Every classification, routing action, status update and escalation is retained in an audit trail."],
            [Languages, "Multilingual intake", "English, Hindi and Marathi complaint understanding with citizen-facing response support."],
            [Gauge, "SLA-aware workflow", "Priority-driven prototype SLA rules expose SAFE, APPROACHING and BREACHED states with demo escalation."]
          ].map(([Icon, title, body]) => {
            const I = Icon as typeof ShieldCheck;
            return <Card key={String(title)}><CardContent className="pt-5"><I className="text-civic-600" /><h3 className="mt-4 font-bold">{String(title)}</h3><p className="mt-2 text-sm leading-6 text-slate-600">{String(body)}</p></CardContent></Card>;
          })}
        </div>
      </section>
    </>
  );
}

function SubmitPage() {
  const [complaint, setComplaint] = useState(demoScenarios[0].text);
  const [language, setLanguage] = useState("English");
  const [location, setLocation] = useState("");
  const [landmark, setLandmark] = useState("");
  const [contact, setContact] = useState("");
  const [analysis, setAnalysis] = useState<ComplaintAnalysis | null>(null);
  const [ticket, setTicket] = useState<Ticket | null>(null);
  const [duplicateOf, setDuplicateOf] = useState<string | undefined>();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const payload: ComplaintPayload = { complaint, language, location: location || undefined, landmark: landmark || undefined, contact: contact || undefined, duplicate_of: duplicateOf };

  async function analyze(event?: FormEvent) {
    event?.preventDefault();
    setBusy(true); setError(""); setTicket(null);
    try { setAnalysis(await api.analyze(payload)); }
    catch (err) { setError(err instanceof Error ? err.message : "Analysis failed."); }
    finally { setBusy(false); }
  }

  async function createTicket() {
    setBusy(true); setError("");
    try {
      const result = await api.createTicket(payload);
      setTicket(result);
      setAnalysis(null);
    } catch (err) { setError(err instanceof Error ? err.message : "Ticket creation failed."); }
    finally { setBusy(false); }
  }

  function useScenario(index: number) {
    const scenario = demoScenarios[index];
    setComplaint(scenario.text); setLanguage(scenario.language); setLocation(""); setLandmark("");
    setAnalysis(null); setTicket(null); setDuplicateOf(undefined); setError("");
  }

  return (
    <Page title="Submit a civic complaint" eyebrow="Citizen portal" subtitle="Describe the issue naturally. The backend runs an actual deterministic multi-stage analysis pipeline and asks for clarification when required.">
      <div className="grid gap-6 lg:grid-cols-[.95fr_1.05fr]">
        <Card>
          <CardHeader><CardTitle>Complaint intake</CardTitle></CardHeader>
          <CardContent>
            <form className="space-y-4" onSubmit={analyze}>
              <div>
                <label className="mb-2 block text-sm font-semibold">Hackathon Demo Mode</label>
                <select className="focus-field" defaultValue="0" onChange={(e) => useScenario(Number(e.target.value))}>
                  {demoScenarios.map((s, i) => <option value={i} key={s.name}>Scenario {i + 1} — {s.name}</option>)}
                </select>
              </div>
              <div>
                <label className="mb-2 block text-sm font-semibold">Complaint description</label>
                <textarea className="focus-field min-h-40 resize-y" value={complaint} onChange={(e) => setComplaint(e.target.value)} maxLength={5000} />
                <div className="mt-1 text-right text-xs text-slate-400">{complaint.length}/5000</div>
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <Field label="Language">
                  <select className="focus-field" value={language} onChange={(e) => setLanguage(e.target.value)}>
                    <option>English</option><option>Hindi</option><option>Marathi</option><option>Auto</option>
                  </select>
                </Field>
                <Field label="Location / locality">
                  <input className="focus-field" placeholder="e.g. Shivaji Nagar" value={location} onChange={(e) => setLocation(e.target.value)} />
                </Field>
                <Field label="Landmark (optional)">
                  <input className="focus-field" value={landmark} onChange={(e) => setLandmark(e.target.value)} />
                </Field>
                <Field label="Contact (optional)">
                  <input className="focus-field" value={contact} onChange={(e) => setContact(e.target.value)} />
                </Field>
              </div>
              <Button className="w-full" size="lg" disabled={busy || complaint.trim().length < 10}>
                {busy ? <><Activity className="mr-2 animate-spin" size={18} /> Analyzing…</> : <><Sparkles className="mr-2" size={18} /> Analyze Complaint</>}
              </Button>
              {error && <ErrorBox>{error}</ErrorBox>}
            </form>
          </CardContent>
        </Card>

        <div>
          <AnimatePresence mode="wait">
            {!analysis && !ticket && (
              <motion.div key="empty" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                <Card className="border-dashed"><CardContent className="grid min-h-[520px] place-items-center text-center">
                  <div><Bot className="mx-auto text-civic-500" size={44} /><h3 className="mt-4 text-xl font-bold">AI analysis will appear here</h3><p className="mt-2 max-w-md text-sm leading-6 text-slate-500">Classification, entity extraction, urgency, routing, missing information, recommendations and agent execution trace are returned by the API.</p></div>
                </CardContent></Card>
              </motion.div>
            )}
            {analysis && <AnalysisPanel key="analysis" analysis={analysis} location={location} setLocation={setLocation} reanalyze={() => analyze()} busy={busy} createTicket={createTicket} setDuplicateOf={setDuplicateOf} duplicateOf={duplicateOf} />}
            {ticket && <TicketPanel key="ticket" ticket={ticket} />}
          </AnimatePresence>
        </div>
      </div>
    </Page>
  );
}

function AnalysisPanel({
  analysis, location, setLocation, reanalyze, busy, createTicket, setDuplicateOf, duplicateOf
}: {
  analysis: ComplaintAnalysis; location: string; setLocation: (v: string) => void; reanalyze: () => void;
  busy: boolean; createTicket: () => void; setDuplicateOf: (v: string | undefined) => void; duplicateOf?: string;
}) {
  const requiresLocation = analysis.missing_information.includes("location");
  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="space-y-5">
      <Card>
        <CardHeader><div className="flex items-center justify-between gap-3"><CardTitle>AI Understanding</CardTitle><Badge value={analysis.priority} /></div></CardHeader>
        <CardContent>
          <div className="grid gap-3 sm:grid-cols-2">
            <Metric label="Category" value={analysis.category} />
            <Metric label="Location" value={analysis.location || "Missing"} />
            <Metric label="Duration" value={analysis.duration || "Not stated"} />
            <Metric label="Responsible department" value={analysis.department} />
            <Metric label="Confidence" value={`${Math.round(analysis.confidence * 100)}%`} />
            <Metric label="Language" value={analysis.language} />
          </div>
          <p className="mt-4 rounded-xl bg-civic-50 p-3 text-sm leading-6 text-civic-900">{analysis.reasoning_summary}</p>
        </CardContent>
      </Card>

      {analysis.missing_information.length > 0 && (
        <Card className="border-amber-200 bg-amber-50/50">
          <CardHeader><CardTitle className="flex items-center gap-2"><AlertTriangle size={18} className="text-amber-600" /> Missing information</CardTitle></CardHeader>
          <CardContent>
            {analysis.clarification_questions.map((q) => <p className="text-sm text-slate-700" key={q}>{q}</p>)}
            {requiresLocation && <div className="mt-4 flex gap-2"><input className="focus-field" placeholder="Enter locality / ward / landmark" value={location} onChange={(e) => setLocation(e.target.value)} /><Button onClick={reanalyze} disabled={!location.trim() || busy}>Continue</Button></div>}
          </CardContent>
        </Card>
      )}

      {analysis.duplicate_candidates.length > 0 && (
        <Card>
          <CardHeader><CardTitle>Possible related complaint</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            {analysis.duplicate_candidates.map((d) => (
              <button onClick={() => setDuplicateOf(duplicateOf === d.ticket_code ? undefined : d.ticket_code)} key={d.ticket_code}
                className={cn("w-full rounded-xl border p-3 text-left", duplicateOf === d.ticket_code ? "border-civic-500 bg-civic-50" : "border-slate-200")}>
                <div className="flex justify-between gap-3"><span className="font-bold">{d.ticket_code}</span><span className="text-sm font-semibold">{Math.round(d.similarity * 100)}% similar</span></div>
                <p className="mt-1 text-sm text-slate-600">{d.summary}</p>
              </button>
            ))}
            <p className="text-xs text-slate-500">Select a related ticket to link it, or leave all unselected to create a new independent complaint.</p>
          </CardContent>
        </Card>
      )}

      <AgentTimeline trace={analysis.agent_trace} />

      {analysis.missing_information.length === 0 && (
        <Button size="lg" className="w-full" onClick={createTicket} disabled={busy}>
          <TicketCheck className="mr-2" size={18} /> Create Trackable Ticket
        </Button>
      )}
    </motion.div>
  );
}

function TicketPanel({ ticket }: { ticket: Ticket }) {
  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="space-y-5">
      <Card className="overflow-hidden border-emerald-200">
        <div className="bg-emerald-700 px-6 py-5 text-white">
          <div className="text-sm font-bold uppercase tracking-[.18em] text-emerald-100">Ticket created</div>
          <div className="mt-1 text-3xl font-black">{ticket.ticket_code}</div>
        </div>
        <CardContent className="pt-5">
          <div className="grid gap-3 sm:grid-cols-2">
            <Metric label="Status" value={ticket.status} />
            <Metric label="SLA state" value={ticket.sla_state} />
            <Metric label="Category" value={ticket.category} />
            <Metric label="Priority" value={ticket.priority} />
            <Metric label="Department" value={ticket.department} />
            <Metric label="Location" value={ticket.location} />
          </div>
          <p className="mt-4 rounded-xl bg-slate-50 p-3 text-sm leading-6">{ticket.citizen_response}</p>
          <Link className="mt-4 inline-flex" to={`/track?ticket=${encodeURIComponent(ticket.ticket_code)}`}><Button>Track Complaint</Button></Link>
        </CardContent>
      </Card>
      <AuditTimeline ticket={ticket} />
    </motion.div>
  );
}

function TrackPage() {
  const initial = new URLSearchParams(window.location.search).get("ticket") || "";
  const [code, setCode] = useState(initial);
  const [ticket, setTicket] = useState<Ticket | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function load(event?: FormEvent) {
    event?.preventDefault(); if (!code.trim()) return;
    setBusy(true); setError("");
    try { setTicket(await api.getTicket(code.trim())); }
    catch (err) { setTicket(null); setError(err instanceof Error ? err.message : "Ticket lookup failed."); }
    finally { setBusy(false); }
  }
  useEffect(() => { if (initial) void load(); }, []); // eslint-disable-line react-hooks/exhaustive-deps

  async function breach() {
    if (!ticket) return;
    setBusy(true);
    try { setTicket(await api.simulateBreach(ticket.ticket_code)); }
    catch (err) { setError(err instanceof Error ? err.message : "Could not simulate SLA breach."); }
    finally { setBusy(false); }
  }

  return (
    <Page title="Track complaint" eyebrow="Citizen portal" subtitle="Retrieve the current ticket state, SLA condition and immutable-style audit history.">
      <form onSubmit={load} className="mb-6 flex gap-2"><input className="focus-field" placeholder="CR-XXXXXX-XXXXXX" value={code} onChange={(e) => setCode(e.target.value)} /><Button disabled={busy}><Search className="mr-2" size={16} />Track</Button></form>
      {error && <ErrorBox>{error}</ErrorBox>}
      {ticket && <div className="grid gap-6 lg:grid-cols-[.9fr_1.1fr]">
        <Card><CardHeader><div className="flex items-center justify-between gap-3"><CardTitle>{ticket.ticket_code}</CardTitle><Badge value={ticket.sla_state} /></div></CardHeader>
          <CardContent className="space-y-3">
            <Metric label="Status" value={ticket.status} /><Metric label="Department" value={ticket.department} /><Metric label="Priority" value={ticket.priority} /><Metric label="Location" value={ticket.location} />
            <div className="rounded-xl bg-slate-50 p-3 text-sm"><b>Configurable SLA deadline:</b><br />{formatDate(ticket.sla_deadline)}</div>
            <div><h4 className="mb-2 text-sm font-bold">AI-assisted recommendation</h4><ul className="list-disc space-y-1 pl-5 text-sm text-slate-600">{ticket.resolution_recommendation.map((r) => <li key={r}>{r}</li>)}</ul></div>
            {ticket.status !== "RESOLVED" && <Button variant="danger" className="w-full" onClick={breach} disabled={busy}><AlertTriangle className="mr-2" size={16} />Simulate SLA Breach</Button>}
            <p className="text-xs text-slate-500">Simulation is clearly marked prototype behavior and is not an official government SLA policy.</p>
          </CardContent>
        </Card>
        <AuditTimeline ticket={ticket} />
      </div>}
    </Page>
  );
}

function OfficerPage() {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [error, setError] = useState("");
  const [filter, setFilter] = useState("ALL");

  async function refresh() {
    try { setTickets(await api.listTickets()); setError(""); }
    catch (err) { setError(err instanceof Error ? err.message : "Could not load tickets."); }
  }
  useEffect(() => { void refresh(); }, []);

  const shown = filter === "ALL" ? tickets : tickets.filter((t) => t.status === filter);
  const kpis = [
    ["Total Assigned", tickets.length],
    ["Pending", tickets.filter((t) => ["SUBMITTED", "ASSIGNED"].includes(t.status)).length],
    ["In Progress", tickets.filter((t) => t.status === "IN_PROGRESS").length],
    ["Resolved", tickets.filter((t) => t.status === "RESOLVED").length],
    ["SLA Approaching", tickets.filter((t) => t.sla_state === "APPROACHING").length],
    ["SLA Breached", tickets.filter((t) => t.sla_state === "BREACHED").length]
  ];

  async function change(ticket: Ticket, status: string) {
    try { await api.updateStatus(ticket.ticket_code, status, `Officer dashboard changed status to ${status}.`); await refresh(); }
    catch (err) { setError(err instanceof Error ? err.message : "Status update failed."); }
  }

  return (
    <Page title="Department Officer Dashboard" eyebrow="Operations" subtitle="Operational queue for reviewing, accepting, progressing and resolving routed complaints.">
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-6">{kpis.map(([label, value]) => <Kpi key={String(label)} label={String(label)} value={String(value)} />)}</div>
      <div className="mt-6 flex items-center justify-between"><h2 className="text-lg font-bold">Complaint queue</h2>
        <select className="rounded-lg border border-slate-300 px-3 py-2 text-sm" value={filter} onChange={(e) => setFilter(e.target.value)}>
          {["ALL", "SUBMITTED", "ASSIGNED", "IN_PROGRESS", "RESOLVED", "ESCALATED"].map((s) => <option key={s}>{s}</option>)}
        </select>
      </div>
      {error && <div className="mt-4"><ErrorBox>{error}</ErrorBox></div>}
      <Card className="mt-4 overflow-hidden"><div className="overflow-x-auto"><table className="w-full min-w-[980px] text-left text-sm">
        <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500"><tr>{["Ticket", "Category", "Location", "Priority", "Department", "SLA", "Status", "Actions"].map((h) => <th key={h} className="px-4 py-3">{h}</th>)}</tr></thead>
        <tbody>{shown.map((t) => <tr className="border-t border-slate-100" key={t.ticket_code}>
          <td className="px-4 py-3 font-bold">{t.ticket_code}</td><td className="px-4 py-3">{t.category}</td><td className="px-4 py-3">{t.location}</td>
          <td className="px-4 py-3"><Badge value={t.priority} /></td><td className="px-4 py-3">{t.department}</td><td className="px-4 py-3"><Badge value={t.sla_state} /></td><td className="px-4 py-3">{t.status}</td>
          <td className="px-4 py-3"><div className="flex gap-2">{t.status === "SUBMITTED" && <Button size="sm" variant="outline" onClick={() => change(t, "ASSIGNED")}>Accept</Button>}{!["RESOLVED"].includes(t.status) && <Button size="sm" onClick={() => change(t, "IN_PROGRESS")}>In Progress</Button>}{t.status !== "RESOLVED" && <Button size="sm" variant="secondary" onClick={() => change(t, "RESOLVED")}>Resolve</Button>}</div></td>
        </tr>)}</tbody>
      </table>{shown.length === 0 && <div className="p-10 text-center text-sm text-slate-500">No tickets in this view. Create a citizen ticket to populate the operational queue.</div>}</div></Card>
    </Page>
  );
}

function AdminPage() {
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [error, setError] = useState("");
  useEffect(() => { api.analytics().then(setAnalytics).catch((e: Error) => setError(e.message)); }, []);
  const categoryData = useMemo(() => Object.entries(analytics?.by_category ?? {}).map(([name, value]) => ({ name, value })), [analytics]);

  return (
    <Page title="Admin Analytics" eyebrow="Governance" subtitle="Operational prototype analytics. All metrics on this screen are explicitly synthetic/demo data generated from local prototype tickets.">
      <div className="mb-4 inline-flex rounded-full bg-amber-100 px-3 py-1 text-xs font-bold text-amber-800">Synthetic / Demo Data</div>
      {error && <ErrorBox>{error}</ErrorBox>}
      {analytics && <>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <Kpi label="Total Complaints" value={String(analytics.total)} /><Kpi label="Pending" value={String(analytics.pending)} /><Kpi label="In Progress" value={String(analytics.in_progress)} /><Kpi label="Resolved" value={String(analytics.resolved)} />
          <Kpi label="Escalated" value={String(analytics.escalated)} /><Kpi label="SLA Breaches" value={String(analytics.sla_breaches)} /><Kpi label="SLA Compliance" value={`${analytics.sla_compliance}%`} /><Kpi label="Data source" value="Demo" />
        </div>
        <Card className="mt-6"><CardHeader><CardTitle>Complaints by category</CardTitle></CardHeader><CardContent>
          <div className="h-80">{categoryData.length ? <ResponsiveContainer width="100%" height="100%"><BarChart data={categoryData} margin={{ left: 8, right: 8, top: 10, bottom: 36 }}><CartesianGrid strokeDasharray="3 3" vertical={false} /><XAxis dataKey="name" angle={-20} textAnchor="end" height={70} interval={0} fontSize={11} /><YAxis allowDecimals={false} /><Tooltip /><Bar dataKey="value" fill="#3159a7" radius={[6,6,0,0]} /></BarChart></ResponsiveContainer> : <Empty label="No local demo tickets yet." />}</div>
        </CardContent></Card>
      </>}
    </Page>
  );
}

function CommandCenterPage() {
  const [analysis, setAnalysis] = useState<ComplaintAnalysis | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function run() {
    setBusy(true); setError("");
    try { setAnalysis(await api.analyze({ complaint: demoScenarios[0].text, language: "English" })); }
    catch (err) { setError(err instanceof Error ? err.message : "Demo pipeline failed."); }
    finally { setBusy(false); }
  }
  useEffect(() => { void run(); }, []);

  return (
    <div className="command-bg min-h-[calc(100vh-65px)] text-white">
      <div className="mx-auto max-w-7xl px-4 py-10 lg:px-8">
        <div className="flex flex-wrap items-end justify-between gap-5">
          <div><div className="text-xs font-bold uppercase tracking-[.22em] text-blue-300">Judge-facing AI Command Center</div><h1 className="mt-2 text-3xl font-black tracking-tight">Multi-Agent Complaint Orchestrator</h1><p className="mt-2 max-w-2xl text-sm leading-6 text-slate-300">Each stage below corresponds to real deterministic backend processing rather than a client-only animation.</p></div>
          <Button variant="secondary" onClick={run} disabled={busy}>{busy ? "Running…" : "Run Water Demo"}</Button>
        </div>
        {error && <div className="mt-5"><ErrorBox>{error}</ErrorBox></div>}
        {analysis && <div className="mt-8 grid gap-4 lg:grid-cols-[.35fr_.65fr]">
          <div className="rounded-2xl border border-white/10 bg-white/5 p-5">
            <div className="text-xs font-bold uppercase tracking-[.2em] text-blue-300">Citizen complaint</div>
            <p className="mt-3 text-lg font-semibold leading-8">“{demoScenarios[0].text}”</p>
            <div className="mt-5 grid gap-3">
              <DarkMetric label="Category" value={analysis.category} /><DarkMetric label="Priority" value={analysis.priority} /><DarkMetric label="Department" value={analysis.department} /><DarkMetric label="Missing" value={analysis.missing_information.join(", ") || "None"} />
            </div>
          </div>
          <div className="space-y-3">{analysis.agent_trace.map((stage, index) => (
            <motion.div key={stage.name} initial={{ opacity: 0, x: 8 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: index * .04 }} className="rounded-xl border border-white/10 bg-white/[.06] p-4">
              <div className="flex flex-wrap items-center justify-between gap-3"><div className="flex items-center gap-3"><div className="grid h-8 w-8 place-items-center rounded-lg bg-blue-400/10 text-blue-300"><Bot size={16} /></div><div className="font-bold">{stage.name}</div></div><div className="flex items-center gap-2"><span className="text-xs text-slate-400">{stage.processing_ms} ms</span><Badge value={stage.status} /></div></div>
              <p className="mt-2 pl-11 text-sm leading-6 text-slate-300">{stage.output}</p>
            </motion.div>
          ))}</div>
        </div>}
      </div>
    </div>
  );
}

function AgentTimeline({ trace }: { trace: ComplaintAnalysis["agent_trace"] }) {
  return <Card><CardHeader><CardTitle>AI agent execution timeline</CardTitle></CardHeader><CardContent className="space-y-3">
    {trace.map((stage) => <div key={stage.name} className="rounded-xl border border-slate-200 p-3"><div className="flex flex-wrap items-center justify-between gap-2"><div className="font-semibold">{stage.name}</div><div className="flex items-center gap-2"><span className="text-xs text-slate-400">{stage.processing_ms} ms</span><Badge value={stage.status} /></div></div><p className="mt-1 text-sm leading-6 text-slate-600">{stage.output}</p></div>)}
  </CardContent></Card>;
}

function AuditTimeline({ ticket }: { ticket: Ticket }) {
  return <Card><CardHeader><CardTitle>Audit trail</CardTitle></CardHeader><CardContent><div className="space-y-4">
    {ticket.audit_events.map((event, index) => <div className="relative flex gap-3" key={`${event.event}-${event.created_at}-${index}`}><div className="mt-1.5 h-3 w-3 shrink-0 rounded-full bg-civic-500" /><div><div className="text-sm font-bold">{event.event.replaceAll("_", " ")}</div><div className="text-xs text-slate-400">{formatDate(event.created_at)}</div><p className="mt-1 text-sm leading-5 text-slate-600">{event.detail}</p></div></div>)}
  </div></CardContent></Card>;
}

function Page({ title, eyebrow, subtitle, children }: { title: string; eyebrow: string; subtitle: string; children: React.ReactNode }) {
  return <div className="mx-auto max-w-7xl px-4 py-10 lg:px-8"><div className="mb-8"><div className="text-xs font-bold uppercase tracking-[.2em] text-civic-600">{eyebrow}</div><h1 className="mt-2 text-3xl font-black tracking-tight text-slate-950">{title}</h1><p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">{subtitle}</p></div>{children}</div>;
}
function Field({ label, children }: { label: string; children: React.ReactNode }) { return <div><label className="mb-2 block text-sm font-semibold">{label}</label>{children}</div>; }
function Metric({ label, value }: { label: string; value: string }) { return <div className="rounded-xl border border-slate-200 p-3"><div className="text-xs font-semibold uppercase tracking-wide text-slate-400">{label}</div><div className="mt-1 font-bold text-slate-900">{value}</div></div>; }
function DarkMetric({ label, value }: { label: string; value: string }) { return <div className="rounded-xl border border-white/10 bg-black/10 p-3"><div className="text-xs font-semibold uppercase tracking-wide text-slate-400">{label}</div><div className="mt-1 font-bold">{value}</div></div>; }
function Kpi({ label, value }: { label: string; value: string }) { return <Card><CardContent className="pt-5"><div className="text-xs font-semibold uppercase tracking-wide text-slate-400">{label}</div><div className="mt-2 text-2xl font-black text-slate-950">{value}</div></CardContent></Card>; }
function ErrorBox({ children }: { children: React.ReactNode }) { return <div className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm font-medium text-rose-800">{children}</div>; }
function Empty({ label }: { label: string }) { return <div className="grid h-full place-items-center text-sm text-slate-500">{label}</div>; }
function formatDate(value: string) { return new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(new Date(value)); }

export default Shell;
