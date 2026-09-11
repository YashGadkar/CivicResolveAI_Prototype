import { FormEvent, useState } from "react";
import { Activity, CheckCircle2, MapPinCheck, Sparkles, TicketCheck, X } from "lucide-react";
import { api, type ComplaintPayload } from "../api";
import { Field, Metric, NoticeState, TicketView, Toast } from "../components/app-ui";
import { Button } from "../components/ui/button";
import { Card, CardContent } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import type { ComplaintAnalysis, ComplaintBatchAnalysis, Ticket } from "../types";

export function SubmitPage(){
  const[complaint,setComplaint]=useState("");const[location,setLocation]=useState("");const[landmark,setLandmark]=useState("");
  const[analysis,setAnalysis]=useState<ComplaintBatchAnalysis|null>(null);const[tickets,setTickets]=useState<Ticket[]>([]);const[busy,setBusy]=useState(false);const[notice,setNotice]=useState<NoticeState>(null);const[clarify,setClarify]=useState(false);
  const payload:ComplaintPayload={complaint,location:location||undefined,landmark:landmark||undefined,verify_location:true};

  async function analyze(e?:FormEvent){
    e?.preventDefault();setBusy(true);setNotice(null);
    try{
      const result=await api.analyzeBatch(payload);setAnalysis(result);setTickets([]);
      const needs=result.issues.some(issue=>issue.missing_information.length>0);
      if(needs)setClarify(true);else setNotice({tone:"success",title:result.issue_count>1?`${result.issue_count} civic issues identified`:"Complaint understood",message:result.issue_count>1?"Each issue will receive its own ticket.":"Review the routing and create your ticket."});
    }catch(err){setNotice({tone:"error",title:"Could not analyze complaint",message:err instanceof Error?err.message:"Please try again."})}finally{setBusy(false)}
  }

  async function create(){
    if(!analysis)return;setBusy(true);setNotice(null);
    try{
      const payloads=analysis.issues.map(issue=>({
        complaint:issue.source_text||complaint,
        location:issue.location||location||undefined,
        landmark:landmark||undefined,
        verify_location:true
      }));
      const created=await api.createTickets(payloads);setTickets(created);setAnalysis(null);
      setNotice({tone:"success",title:created.length>1?`${created.length} tickets created`:"Ticket created",message:created.length>1?"Each detected civic problem now has a separate trackable ticket.":`${created[0].ticket_code} is ready to track.`});
    }catch(err){setNotice({tone:"error",title:"Ticket creation stopped",message:err instanceof Error?err.message:"Please retry."})}finally{setBusy(false)}
  }

  const ready=analysis?.issues.every(issue=>issue.missing_information.length===0)??false;
  return <main className="mx-auto max-w-7xl px-4 py-10 lg:px-8"><p className="text-xs font-bold uppercase tracking-[.22em] text-teal-700 dark:text-teal-300">Citizen services</p><h1 className="mt-2 text-3xl font-black tracking-tight text-[#081525] dark:text-white sm:text-4xl">Submit a civic complaint</h1><p className="mb-8 mt-2 max-w-3xl text-sm leading-6 text-slate-500 dark:text-slate-400">Describe one or several civic problems naturally. CivicResolve separates different issues, verifies locations, and prepares one ticket per problem.</p>{notice&&<Toast notice={notice} onClose={()=>setNotice(null)}/>} {clarify&&analysis&&<Clarification analysis={analysis} location={location} setLocation={setLocation} busy={busy} onClose={()=>setClarify(false)} onContinue={async()=>{setClarify(false);await analyze()}}/>}
  <div className="grid gap-6 lg:grid-cols-[.92fr_1.08fr]"><Card className="border-slate-200 shadow-panel dark:border-slate-700 dark:bg-slate-900"><CardContent className="pt-6"><form className="space-y-5" onSubmit={analyze}><Field label="What happened?"><textarea className="focus-field min-h-56 resize-y" value={complaint} onChange={e=>setComplaint(e.target.value)} placeholder="Example: There is no water supply for three days. Also, garbage has not been collected near the market." maxLength={5000}/></Field><div className="grid gap-4 sm:grid-cols-2"><Field label="Location"><input className="focus-field" value={location} onChange={e=>setLocation(e.target.value)} placeholder="Locality / ward / city"/></Field><Field label="Landmark (optional)"><input className="focus-field" value={landmark} onChange={e=>setLandmark(e.target.value)} placeholder="Nearby landmark"/></Field></div><Button size="lg" className="w-full" disabled={busy||complaint.trim().length<10}>{busy?<Activity className="mr-2 animate-spin" size={18}/>:<Sparkles className="mr-2" size={18}/>}Analyze complaint</Button></form></CardContent></Card><div>{!analysis&&!tickets.length&&<Placeholder/>}{analysis&&<BatchSummary analysis={analysis} onCreate={create} busy={busy} ready={ready}/>} {tickets.length>0&&<div className="space-y-4">{tickets.map(ticket=><TicketView key={ticket.ticket_code} ticket={ticket}/>)}</div>}</div></div></main>
}

function BatchSummary({analysis,onCreate,busy,ready}:{analysis:ComplaintBatchAnalysis;onCreate:()=>void;busy:boolean;ready:boolean}){
  return <div className="space-y-4"><div className="rounded-2xl border border-teal-200 bg-teal-50 px-4 py-3 text-sm text-teal-900 dark:border-teal-900 dark:bg-teal-950/50 dark:text-teal-100"><div className="flex items-center gap-2 font-bold"><CheckCircle2 size={17}/>{analysis.issue_count>1?`${analysis.issue_count} separate problems detected`:`1 civic problem detected`}</div>{analysis.issue_count>1&&<p className="mt-1 text-xs opacity-80">CivicResolve will create one ticket for each problem instead of combining them.</p>}</div>{analysis.issues.map((issue,index)=><IssueSummary key={`${issue.category}-${index}`} issue={issue} index={index}/>) }{ready&&<Button size="lg" className="w-full" onClick={onCreate} disabled={busy}><TicketCheck className="mr-2" size={18}/>{analysis.issue_count>1?`Create ${analysis.issue_count} trackable tickets`:"Create trackable ticket"}</Button>}</div>
}

function IssueSummary({issue,index}:{issue:ComplaintAnalysis;index:number}){
  const ready=issue.missing_information.length===0;
  return <Card className="overflow-hidden border-slate-200 shadow-panel dark:border-slate-700 dark:bg-slate-900"><div className="border-b border-slate-200 bg-[#0b1f3a] px-6 py-4 text-white dark:border-slate-700"><div className="flex items-center justify-between gap-4"><div><p className="text-xs font-bold uppercase tracking-[.2em] text-teal-200">Issue {index+1}</p><h2 className="mt-1 text-xl font-black">{issue.category}</h2></div><Badge value={issue.priority}/></div></div><CardContent className="pt-5"><div className="grid gap-3 sm:grid-cols-2"><Metric label="Detected language" value={issue.language}/><Metric label="Responsible department" value={issue.department}/><Metric label="Location" value={issue.location||"Needs verified location"}/><Metric label="Duration" value={issue.duration||"Not stated"}/><Metric label="Priority" value={issue.priority}/><Metric label="Status" value={ready?"Ready for ticket":"Needs clarification"}/></div>{issue.location_verified&&<div className="mt-4 flex items-start gap-2 rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-xs text-emerald-800 dark:border-emerald-900 dark:bg-emerald-950/40 dark:text-emerald-200"><MapPinCheck size={16} className="mt-0.5 shrink-0"/><span><b>Verified location.</b> {issue.location_display_name||issue.location}</span></div>}<p className="mt-4 rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm leading-6 text-slate-600 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300">{issue.citizen_response}</p></CardContent></Card>
}

function Clarification({analysis,location,setLocation,busy,onClose,onContinue}:{analysis:ComplaintBatchAnalysis;location:string;setLocation:(v:string)=>void;busy:boolean;onClose:()=>void;onContinue:()=>void}){
  const issue=analysis.issues.find(item=>item.missing_information.length>0);const asks=issue?.missing_information.includes("location")??false;const message=issue?.location_verification_message||issue?.clarification_questions[0]||"Please add the missing information.";
  return <div className="fixed inset-0 z-50 grid place-items-center bg-slate-950/35 p-4 backdrop-blur-[2px]"><div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-5 shadow-2xl dark:border-slate-700 dark:bg-slate-900"><div className="flex items-start justify-between gap-4"><div><p className="text-xs font-bold uppercase tracking-[.18em] text-amber-700 dark:text-amber-300">One more detail</p><h3 className="mt-1 text-lg font-black text-slate-900 dark:text-white">Help us route this correctly</h3></div><button className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800" onClick={onClose} aria-label="Close"><X size={17}/></button></div><p className="mt-3 text-sm leading-6 text-slate-600 dark:text-slate-300">{message}</p>{asks&&<div className="mt-4"><input className="focus-field" value={location} onChange={e=>setLocation(e.target.value)} placeholder="Locality, city, ward or address" autoFocus/><Button className="mt-3 w-full" onClick={onContinue} disabled={!location.trim()||busy}>{busy?"Verifying…":"Verify and continue"}</Button></div>}{!asks&&<Button className="mt-4 w-full" variant="outline" onClick={onClose}>Edit complaint</Button>}</div></div>
}

function Placeholder(){return <Card className="border-dashed border-slate-300 bg-white/60 dark:border-slate-700 dark:bg-slate-900/60"><CardContent className="grid min-h-[480px] place-items-center text-center"><div><Sparkles className="mx-auto text-teal-600 dark:text-teal-300" size={42}/><h3 className="mt-4 text-xl font-black text-slate-900 dark:text-white">Your complaint summary will appear here</h3><p className="mt-2 max-w-md text-sm leading-6 text-slate-500 dark:text-slate-400">Different civic issues are separated automatically, and locations are checked before ticket creation.</p></div></CardContent></Card>}
