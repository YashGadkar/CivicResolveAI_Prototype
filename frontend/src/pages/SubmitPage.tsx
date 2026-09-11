import { FormEvent, useRef, useState } from "react";
import {
  Activity,
  CheckCircle2,
  FileUp,
  MapPinCheck,
  Mic,
  MicOff,
  Paperclip,
  ShieldAlert,
  Sparkles,
  TicketCheck,
  X,
} from "lucide-react";
import { api, type ComplaintPayload } from "../api";
import { Field, Metric, NoticeState, TicketView, Toast } from "../components/app-ui";
import { Button } from "../components/ui/button";
import { Card, CardContent } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import type { ComplaintAnalysis, ComplaintBatchAnalysis, Ticket } from "../types";

export function SubmitPage() {
  const [complaint, setComplaint] = useState("");
  const [location, setLocation] = useState("");
  const [landmark, setLandmark] = useState("");
  const [contact, setContact] = useState("");
  const [analysis, setAnalysis] = useState<ComplaintBatchAnalysis | null>(null);
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [generatedByIssue, setGeneratedByIssue] = useState<Record<number, Ticket>>({});
  const [busy, setBusy] = useState(false);
  const [generatingIndex, setGeneratingIndex] = useState<number | null>(null);
  const [locating, setLocating] = useState(false);
  const [notice, setNotice] = useState<NoticeState>(null);
  const [clarify, setClarify] = useState(false);
  const [listening, setListening] = useState(false);
  const [evidence, setEvidence] = useState<File[]>([]);
  const recognitionRef = useRef<any>(null);

  const payload: ComplaintPayload = {
    complaint,
    location: location || undefined,
    landmark: landmark || undefined,
    contact: contact || undefined,
    verify_location: true,
  };

  function toggleVoice() {
    if (listening) {
      recognitionRef.current?.stop?.();
      setListening(false);
      return;
    }
    const Ctor = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!Ctor) {
      setNotice({
        tone: "info",
        title: "Voice input unavailable",
        message: "This browser does not expose speech recognition. You can continue typing normally.",
      });
      return;
    }
    const recognition = new Ctor();
    recognition.lang = "en-IN";
    recognition.interimResults = false;
    recognition.continuous = true;
    recognition.onresult = (event: any) => {
      let text = "";
      for (let i = event.resultIndex; i < event.results.length; i += 1) text += `${event.results[i][0].transcript} `;
      setComplaint((value) => `${value} ${text}`.trim());
    };
    recognition.onerror = () => {
      setListening(false);
      setNotice({
        tone: "error",
        title: "Voice input stopped",
        message: "Speech recognition could not continue. Your typed text is unchanged.",
      });
    };
    recognition.onend = () => setListening(false);
    recognitionRef.current = recognition;
    recognition.start();
    setListening(true);
  }

  async function useDeviceLocation() {
    if (!navigator.geolocation) {
      setNotice({
        tone: "info",
        title: "Device location unavailable",
        message: "This browser does not provide location access. Enter the affected locality or address manually.",
      });
      return;
    }

    setLocating(true);
    setNotice(null);
    try {
      const position = await new Promise<GeolocationPosition>((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(resolve, reject, {
          enableHighAccuracy: true,
          timeout: 10000,
          maximumAge: 60000,
        });
      });
      const result = await api.reverseDeviceLocation(position.coords.latitude, position.coords.longitude);
      if (!result.valid || !result.canonical_name) throw new Error(result.message || "The current location could not be verified.");
      setLocation(result.canonical_name);
      setNotice({
        tone: "success",
        title: "Current location added",
        message: "The detected place was converted into a civic-service location. Review it before submitting.",
      });
    } catch (error) {
      setNotice({
        tone: "error",
        title: "Could not use current location",
        message: error instanceof Error ? error.message : "Allow location access or enter the place manually.",
      });
    } finally {
      setLocating(false);
    }
  }

  async function analyze(e?: FormEvent) {
    e?.preventDefault();
    setBusy(true);
    setNotice(null);
    try {
      const result = await api.analyzeBatch(payload);
      setAnalysis(result);
      setTickets([]);
      setGeneratedByIssue({});
      const needs = result.issues.some((issue) => issue.missing_information.length > 0);
      if (needs) {
        setClarify(true);
      } else {
        setNotice({
          tone: "success",
          title: result.issue_count > 1 ? `${result.issue_count} civic issues identified` : "Complaint understood",
          message:
            result.issue_count > 1
              ? "Each issue can now be reviewed and generated as its own ticket."
              : "Review the routing and generate the ticket when ready.",
        });
      }
    } catch (error) {
      setNotice({
        tone: "error",
        title: "Could not analyze complaint",
        message: error instanceof Error ? error.message : "Please try again.",
      });
    } finally {
      setBusy(false);
    }
  }

  function issuePayload(issue: ComplaintAnalysis): ComplaintPayload {
    return {
      complaint: issue.source_text || complaint,
      location: issue.location || location || undefined,
      landmark: landmark || undefined,
      contact: contact || undefined,
      verify_location: true,
    };
  }

  async function generateIssue(index: number) {
    if (!analysis || generatedByIssue[index] || generatingIndex !== null) return;
    const issue = analysis.issues[index];
    if (!issue || issue.missing_information.length > 0) return;

    setGeneratingIndex(index);
    setNotice(null);
    try {
      const created = await api.createTicket(issuePayload(issue));
      setGeneratedByIssue((current) => ({ ...current, [index]: created }));
      setTickets((current) => (current.some((ticket) => ticket.ticket_code === created.ticket_code) ? current : [...current, created]));

      if (evidence.length > 0) {
        try {
          for (const file of evidence) await api.uploadEvidence(created.ticket_code, file, "CITIZEN_EVIDENCE");
        } catch (error) {
          setNotice({
            tone: "info",
            title: `${created.ticket_code} created; evidence needs retry`,
            message: error instanceof Error ? error.message : "The ticket exists, but one or more evidence files were not uploaded.",
          });
          return;
        }
      }

      setNotice({
        tone: "success",
        title: `${created.ticket_code} generated`,
        message: evidence.length > 0 ? "Ticket created and supporting evidence uploaded." : "This issue now has its own trackable ticket.",
      });
    } catch (error) {
      setNotice({
        tone: "error",
        title: "Ticket creation stopped",
        message: error instanceof Error ? error.message : "Please retry.",
      });
    } finally {
      setGeneratingIndex(null);
    }
  }

  const critical = analysis?.issues.some((issue) => issue.priority === "CRITICAL") ?? false;

  return (
    <main className="mx-auto max-w-7xl px-4 py-10 lg:px-8">
      <div className="mb-8 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-xs font-black uppercase tracking-[.22em] text-teal-700 dark:text-teal-300">Citizen service desk</p>
          <h1 className="mt-2 text-3xl font-black tracking-tight text-[#081525] dark:text-white sm:text-4xl">Report a civic issue</h1>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-500 dark:text-slate-400">
            Write or speak naturally. If your message contains several different civic problems, CivicResolve separates them and prepares one ticket for each.
          </p>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-xs text-slate-500 shadow-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-400">
          <b className="text-slate-800 dark:text-slate-200">Privacy note:</b> add only details needed to resolve the civic issue.
        </div>
      </div>

      {notice && <Toast notice={notice} onClose={() => setNotice(null)} />}
      {clarify && analysis && (
        <Clarification
          analysis={analysis}
          location={location}
          setLocation={setLocation}
          busy={busy}
          onClose={() => setClarify(false)}
          onContinue={async () => {
            setClarify(false);
            await analyze();
          }}
        />
      )}

      <div className="grid gap-6 lg:grid-cols-[.92fr_1.08fr] lg:items-start">
        <div className="lg:sticky lg:top-24">
          <Card className="border-slate-200 shadow-panel dark:border-slate-700 dark:bg-slate-900">
            <CardContent className="pt-6">
              <form className="space-y-5" onSubmit={analyze}>
                <Field label="Describe what happened">
                  <div className="relative">
                    <textarea
                      className="focus-field min-h-52 resize-y pr-14"
                      value={complaint}
                      onChange={(event) => setComplaint(event.target.value)}
                      placeholder="Example: There is no water supply for three days. Also, garbage has not been collected near the market."
                      maxLength={5000}
                    />
                    <button
                      type="button"
                      onClick={toggleVoice}
                      className={`absolute bottom-3 right-3 grid h-10 w-10 place-items-center rounded-xl border transition ${
                        listening
                          ? "border-rose-300 bg-rose-50 text-rose-600 dark:bg-rose-950"
                          : "border-slate-200 bg-white text-slate-500 hover:text-teal-700 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300"
                      }`}
                      aria-label={listening ? "Stop voice input" : "Start voice input"}
                    >
                      {listening ? <MicOff size={18} /> : <Mic size={18} />}
                    </button>
                  </div>
                  {listening && (
                    <div className="mt-2 flex items-center gap-2 text-xs font-semibold text-rose-600 dark:text-rose-300">
                      <span className="h-2 w-2 animate-pulse rounded-full bg-rose-500" />
                      Listening… speak naturally, then press the microphone again.
                    </div>
                  )}
                </Field>

                <div className="grid gap-4 sm:grid-cols-2">
                  <Field label="Affected location">
                    <input
                      className="focus-field"
                      value={location}
                      onChange={(event) => setLocation(event.target.value)}
                      placeholder="Locality, ward, city or address"
                    />
                    <button
                      type="button"
                      onClick={() => void useDeviceLocation()}
                      disabled={locating}
                      className="mt-2 inline-flex items-center gap-1.5 text-xs font-bold text-teal-700 hover:text-teal-900 disabled:opacity-50 dark:text-teal-300 dark:hover:text-teal-200"
                    >
                      {locating ? <Activity size={14} className="animate-spin" /> : <MapPinCheck size={14} />}
                      {locating ? "Detecting current location…" : "Use my current location"}
                    </button>
                  </Field>
                  <Field label="Landmark (optional)">
                    <input
                      className="focus-field"
                      value={landmark}
                      onChange={(event) => setLandmark(event.target.value)}
                      placeholder="Nearby landmark"
                    />
                  </Field>
                </div>

                <Field label="Contact detail (optional)">
                  <input
                    className="focus-field"
                    value={contact}
                    onChange={(event) => setContact(event.target.value)}
                    placeholder="Phone or preferred contact reference"
                    maxLength={255}
                  />
                </Field>

                <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50/70 p-4 dark:border-slate-700 dark:bg-slate-950/40">
                  <div className="flex items-start gap-3">
                    <Paperclip className="mt-0.5 text-teal-700 dark:text-teal-300" size={19} />
                    <div className="flex-1">
                      <b className="text-sm text-slate-900 dark:text-white">Supporting evidence</b>
                      <p className="mt-1 text-xs leading-5 text-slate-500 dark:text-slate-400">
                        Optional JPG, PNG, WebP, MP4 or PDF. Evidence is attached only to the individual ticket you generate.
                      </p>
                      <input
                        className="mt-3 block w-full text-xs text-slate-500 file:mr-3 file:rounded-lg file:border-0 file:bg-[#0b1f3a] file:px-3 file:py-2 file:font-bold file:text-white dark:text-slate-400"
                        type="file"
                        multiple
                        accept="image/jpeg,image/png,image/webp,video/mp4,application/pdf"
                        onChange={(event) => setEvidence(Array.from(event.target.files || []))}
                      />
                      {evidence.length > 0 && (
                        <div className="mt-2 text-xs font-semibold text-teal-700 dark:text-teal-300">
                          <FileUp className="mr-1 inline" size={14} />
                          {evidence.length} file{evidence.length > 1 ? "s" : ""} ready
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                <Button size="lg" className="w-full" disabled={busy || generatingIndex !== null || complaint.trim().length < 10}>
                  {busy ? <Activity className="mr-2 animate-spin" size={18} /> : <Sparkles className="mr-2" size={18} />}
                  Review complaint
                </Button>
              </form>
            </CardContent>
          </Card>
        </div>

        <div className="space-y-4 lg:max-h-[calc(100vh-7rem)] lg:overflow-y-auto lg:overscroll-contain lg:pr-2">
          {critical && (
            <div className="flex gap-3 rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-900 dark:border-rose-900 dark:bg-rose-950/40 dark:text-rose-100">
              <ShieldAlert className="shrink-0" size={20} />
              <div>
                <b>Potential immediate safety risk detected.</b>
                <p className="mt-1 text-xs leading-5 opacity-80">
                  CivicResolve is not an emergency dispatch service. If there is immediate danger to life or property, contact the appropriate emergency service while also submitting the civic report.
                </p>
              </div>
            </div>
          )}

          {!analysis && tickets.length === 0 && <Placeholder />}
          {analysis && (
            <BatchSummary
              analysis={analysis}
              generatedByIssue={generatedByIssue}
              generatingIndex={generatingIndex}
              onGenerate={(index) => void generateIssue(index)}
            />
          )}

          {tickets.length > 0 && (
            <div className="space-y-4">
              <div className="px-1">
                <p className="text-xs font-black uppercase tracking-[.18em] text-teal-700 dark:text-teal-300">Generated tickets</p>
                <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">Each generated issue is independently trackable and has its own SLA.</p>
              </div>
              {tickets.map((ticket) => (
                <TicketView key={ticket.ticket_code} ticket={ticket} />
              ))}
            </div>
          )}
        </div>
      </div>
    </main>
  );
}

function BatchSummary({
  analysis,
  generatedByIssue,
  generatingIndex,
  onGenerate,
}: {
  analysis: ComplaintBatchAnalysis;
  generatedByIssue: Record<number, Ticket>;
  generatingIndex: number | null;
  onGenerate: (index: number) => void;
}) {
  return (
    <div className="space-y-4">
      <div className="rounded-2xl border border-teal-200 bg-teal-50 px-4 py-3 text-sm text-teal-900 dark:border-teal-900 dark:bg-teal-950/50 dark:text-teal-100">
        <div className="flex items-center gap-2 font-bold">
          <CheckCircle2 size={17} />
          {analysis.issue_count > 1 ? `${analysis.issue_count} separate problems detected` : "1 civic problem detected"}
        </div>
        <p className="mt-1 text-xs opacity-80">
          {analysis.issue_count > 1
            ? "Review each problem below and generate its ticket individually. Each can route to a different department."
            : "Review the service routing and checks below, then generate this ticket."}
        </p>
      </div>

      {analysis.issues.map((issue, index) => (
        <IssueSummary
          key={`${issue.category}-${index}`}
          issue={issue}
          index={index}
          total={analysis.issue_count}
          generatedTicket={generatedByIssue[index]}
          generating={generatingIndex === index}
          generationLocked={generatingIndex !== null}
          onGenerate={() => onGenerate(index)}
        />
      ))}
    </div>
  );
}

function IssueSummary({
  issue,
  index,
  total,
  generatedTicket,
  generating,
  generationLocked,
  onGenerate,
}: {
  issue: ComplaintAnalysis;
  index: number;
  total: number;
  generatedTicket?: Ticket;
  generating: boolean;
  generationLocked: boolean;
  onGenerate: () => void;
}) {
  const ready = issue.missing_information.length === 0;
  const safetyLabel = issue.priority === "CRITICAL" ? "Potential immediate safety risk" : "No immediate safety-risk signal";
  const duplicateLabel = issue.duplicate_candidates.length > 0 ? `${issue.duplicate_candidates.length} related report${issue.duplicate_candidates.length > 1 ? "s" : ""} found` : "No strong duplicate match found";
  const locationLabel = issue.location_verified ? "Location verified" : issue.location ? "Location captured; verification pending" : "Location still required";

  return (
    <Card className="overflow-hidden border-slate-200 shadow-panel dark:border-slate-700 dark:bg-slate-900">
      <div className="border-b border-slate-200 bg-[#0b1f3a] px-6 py-4 text-white dark:border-slate-700">
        <div className="flex items-center justify-between gap-4">
          <div>
            <p className="text-xs font-bold uppercase tracking-[.2em] text-teal-200">Issue {index + 1} of {total}</p>
            <h2 className="mt-1 text-xl font-black">{issue.category}</h2>
          </div>
          <Badge value={issue.priority} />
        </div>
      </div>

      <CardContent className="pt-5">
        <div className="grid gap-3 sm:grid-cols-2">
          <Metric label="Detected language" value={issue.language} />
          <Metric label="Responsible department" value={issue.department} />
          <Metric label="Location" value={issue.location || "Needs verified location"} />
          <Metric label="Duration" value={issue.duration || "Not stated"} />
          <Metric label="Priority" value={issue.priority} />
          <Metric label="Urgency" value={issue.urgency} />
        </div>

        <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50/80 p-4 dark:border-slate-700 dark:bg-slate-800/70">
          <p className="text-[11px] font-black uppercase tracking-[.16em] text-slate-500 dark:text-slate-400">CivicResolve checks</p>
          <div className="mt-3 grid gap-2 sm:grid-cols-2">
            <CheckLine label="Service classification" value={`${issue.category} → ${issue.department}`} />
            <CheckLine label="Location check" value={locationLabel} />
            <CheckLine label="Related-report scan" value={duplicateLabel} />
            <CheckLine label="Safety check" value={safetyLabel} danger={issue.priority === "CRITICAL"} />
          </div>
        </div>

        {issue.location_verified && (
          <div className="mt-4 flex items-start gap-2 rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-xs text-emerald-800 dark:border-emerald-900 dark:bg-emerald-950/40 dark:text-emerald-200">
            <MapPinCheck size={16} className="mt-0.5 shrink-0" />
            <span><b>Verified place.</b> {issue.location_display_name || issue.location}</span>
          </div>
        )}

        {issue.duplicate_candidates.length > 0 && (
          <div className="mt-4 rounded-xl border border-amber-200 bg-amber-50 p-3 text-xs text-amber-900 dark:border-amber-900 dark:bg-amber-950/30 dark:text-amber-200">
            <b>Related reports found:</b> {issue.duplicate_candidates.map((candidate) => candidate.ticket_code).join(", ")}. These remain separate citizen reports but can be grouped operationally.
          </div>
        )}

        {issue.resolution_recommendation.length > 0 && (
          <div className="mt-4 rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
            <p className="text-xs font-black uppercase tracking-[.16em] text-slate-500 dark:text-slate-400">Suggested resolution steps</p>
            <ul className="mt-2 space-y-2 text-sm leading-5 text-slate-700 dark:text-slate-300">
              {issue.resolution_recommendation.map((item, recommendationIndex) => (
                <li key={`${item}-${recommendationIndex}`} className="flex gap-2">
                  <CheckCircle2 size={15} className="mt-0.5 shrink-0 text-teal-700 dark:text-teal-300" />
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        <p className="mt-4 rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm leading-6 text-slate-600 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300">
          {issue.citizen_response}
        </p>

        {generatedTicket ? (
          <div className="mt-4 flex items-center justify-between gap-3 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm dark:border-emerald-900 dark:bg-emerald-950/40">
            <div>
              <b className="text-emerald-900 dark:text-emerald-100">{generatedTicket.ticket_code} generated</b>
              <p className="mt-0.5 text-xs text-emerald-700 dark:text-emerald-300">This issue is now independently trackable.</p>
            </div>
            <TicketCheck className="shrink-0 text-emerald-700 dark:text-emerald-300" size={20} />
          </div>
        ) : ready ? (
          <Button className="mt-4 w-full" size="lg" onClick={onGenerate} disabled={generationLocked}>
            {generating ? <Activity className="mr-2 animate-spin" size={18} /> : <TicketCheck className="mr-2" size={18} />}
            {generating ? "Generating this ticket…" : "Generate this ticket"}
          </Button>
        ) : (
          <div className="mt-4 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-xs font-semibold text-amber-900 dark:border-amber-900 dark:bg-amber-950/30 dark:text-amber-200">
            Complete the requested clarification before this issue can generate a ticket.
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function CheckLine({ label, value, danger = false }: { label: string; value: string; danger?: boolean }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white px-3 py-2.5 dark:border-slate-700 dark:bg-slate-900">
      <p className="text-[10px] font-bold uppercase tracking-[.12em] text-slate-400">{label}</p>
      <p className={`mt-1 text-xs font-bold ${danger ? "text-rose-700 dark:text-rose-300" : "text-slate-700 dark:text-slate-200"}`}>{value}</p>
    </div>
  );
}

function Clarification({
  analysis,
  location,
  setLocation,
  busy,
  onClose,
  onContinue,
}: {
  analysis: ComplaintBatchAnalysis;
  location: string;
  setLocation: (value: string) => void;
  busy: boolean;
  onClose: () => void;
  onContinue: () => void;
}) {
  const issue = analysis.issues.find((item) => item.missing_information.length > 0);
  const asks = issue?.missing_information.includes("location") ?? false;
  const message = issue?.location_verification_message || issue?.clarification_questions[0] || "Please add the missing information.";

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-slate-950/45 p-4 backdrop-blur-sm">
      <div className="w-full max-w-md rounded-3xl border border-slate-200 bg-white p-6 shadow-2xl dark:border-slate-700 dark:bg-slate-900">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-xs font-bold uppercase tracking-[.18em] text-amber-700 dark:text-amber-300">One more detail</p>
            <h3 className="mt-1 text-lg font-black text-slate-900 dark:text-white">Help us route this correctly</h3>
          </div>
          <button className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800" onClick={onClose} aria-label="Close">
            <X size={17} />
          </button>
        </div>
        <p className="mt-3 text-sm leading-6 text-slate-600 dark:text-slate-300">{message}</p>
        {asks && (
          <div className="mt-4">
            <input className="focus-field" value={location} onChange={(event) => setLocation(event.target.value)} placeholder="Locality, city, ward or address" autoFocus />
            <Button className="mt-3 w-full" onClick={onContinue} disabled={!location.trim() || busy}>
              {busy ? "Verifying…" : "Verify and continue"}
            </Button>
          </div>
        )}
        {!asks && (
          <Button className="mt-4 w-full" variant="outline" onClick={onClose}>
            Edit complaint
          </Button>
        )}
      </div>
    </div>
  );
}

function Placeholder() {
  return (
    <Card className="border-dashed border-slate-300 bg-white/60 dark:border-slate-700 dark:bg-slate-900/60">
      <CardContent className="grid min-h-[500px] place-items-center text-center">
        <div className="max-w-md">
          <span className="mx-auto grid h-16 w-16 place-items-center rounded-2xl bg-teal-50 text-teal-700 dark:bg-teal-950 dark:text-teal-300">
            <Sparkles size={30} />
          </span>
          <h3 className="mt-5 text-xl font-black text-slate-900 dark:text-white">A clean review appears here before anything is submitted</h3>
          <p className="mt-2 text-sm leading-6 text-slate-500 dark:text-slate-400">
            CivicResolve separates different problems, verifies the place, classifies the service, checks urgency and safety, scans for related reports, recommends next steps and lets you generate each ticket individually.
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
