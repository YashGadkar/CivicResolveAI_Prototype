import { FormEvent, useMemo, useState } from "react";
import { Bot, Building2, Loader2, MessageCircleMore, Send, Sparkles, TicketCheck, UserRound } from "lucide-react";
import { api } from "../api";
import { NoticeState, Toast } from "../components/app-ui";
import { Button } from "../components/ui/button";
import type { ComplaintBatchAnalysis, StaffTicket, Ticket, User } from "../types";

type ChatMessage={id:string;role:"assistant"|"user";text:string};

export function CommandCenterPage({user}:{user:User}){
  const staff=["OFFICER","ADMIN"].includes(user.role);const[input,setInput]=useState("");const[busy,setBusy]=useState(false);const[notice,setNotice]=useState<NoticeState>(null);
  const initial=useMemo<ChatMessage[]>(()=>[{id:"welcome",role:"assistant",text:staff?"I can help you inspect ticket status, summarize a citizen complaint, or understand your active queue. Try a ticket ID such as CR-… or paste a complaint.":"I can help you understand a civic problem, separate multiple issues, or explain the status of one of your tickets. Paste a complaint or enter a CR-… ticket ID."}],[staff]);
  const[messages,setMessages]=useState<ChatMessage[]>(initial);

  async function sendMessage(e?:FormEvent){
    e?.preventDefault();const text=input.trim();if(!text||busy)return;setInput("");setMessages(m=>[...m,{id:crypto.randomUUID(),role:"user",text}]);setBusy(true);setNotice(null);
    try{const reply=await answer(text,staff);setMessages(m=>[...m,{id:crypto.randomUUID(),role:"assistant",text:reply}])}catch(err){setNotice({tone:"error",title:"Civic Assistant could not complete that request",message:err instanceof Error?err.message:"Please try again."})}finally{setBusy(false)}
  }

  const quick=staff?["Summarize my active queue","How many escalated tickets are active?","Classify this citizen complaint"]:["Understand this complaint","How many complaints do I have?","Help me separate multiple civic issues"];
  return <div className="command-bg min-h-[calc(100vh-65px)] text-white">{notice&&<Toast notice={notice} onClose={()=>setNotice(null)}/>}<div className="mx-auto max-w-6xl px-4 py-8 lg:px-8 lg:py-12"><div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between"><div><p className="text-xs font-bold uppercase tracking-[.24em] text-teal-200">Civic Assistant</p><h1 className="mt-2 text-3xl font-black sm:text-4xl">Ask. Understand. Act.</h1><p className="mt-3 max-w-2xl text-sm leading-6 text-slate-300">A role-aware assistant for citizen complaints and employee ticket operations. It shows decisions and next steps without exposing internal model details.</p></div><div className="flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-2 text-xs font-bold uppercase tracking-wide text-slate-300">{staff?<Building2 size={15}/>:<UserRound size={15}/>} {staff?"Employee mode":"Citizen mode"}</div></div>
    <div className="mt-7 overflow-hidden rounded-[26px] border border-white/10 bg-[#07111f]/70 shadow-2xl backdrop-blur"><div className="border-b border-white/10 px-4 py-3 sm:px-6"><div className="flex flex-wrap gap-2">{quick.map(q=><button key={q} type="button" onClick={()=>setInput(q)} className="rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-xs font-semibold text-slate-300 transition hover:bg-white/10 hover:text-white">{q}</button>)}</div></div><div className="h-[52vh] min-h-[420px] overflow-y-auto px-4 py-5 sm:px-6"><div className="mx-auto max-w-3xl space-y-4">{messages.map(message=><div key={message.id} className={`flex ${message.role==="user"?"justify-end":"justify-start"}`}><div className={`max-w-[88%] rounded-2xl px-4 py-3 text-sm leading-6 sm:max-w-[75%] ${message.role==="user"?"rounded-br-md bg-teal-600 text-white":"rounded-bl-md border border-white/10 bg-white/[.07] text-slate-200"}`}><div className="mb-1 flex items-center gap-2 text-[10px] font-bold uppercase tracking-[.16em] opacity-70">{message.role==="assistant"?<Bot size={13}/>:<UserRound size={13}/>} {message.role==="assistant"?"Civic Assistant":"You"}</div><div className="whitespace-pre-wrap">{message.text}</div></div></div>)}{busy&&<div className="flex justify-start"><div className="flex items-center gap-2 rounded-2xl rounded-bl-md border border-white/10 bg-white/[.07] px-4 py-3 text-sm text-slate-300"><Loader2 size={16} className="animate-spin"/> Working on that…</div></div>}</div></div><form onSubmit={sendMessage} className="border-t border-white/10 p-4 sm:p-5"><div className="mx-auto flex max-w-3xl gap-3"><div className="relative flex-1"><MessageCircleMore className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" size={18}/><input value={input} onChange={e=>setInput(e.target.value)} placeholder={staff?"Ask about a ticket, queue, or complaint…":"Describe a civic issue or enter your ticket ID…"} className="w-full rounded-2xl border border-white/10 bg-slate-950/70 py-3.5 pl-11 pr-4 text-sm text-white outline-none placeholder:text-slate-500 focus:border-teal-400/60"/></div><Button type="submit" size="lg" disabled={busy||!input.trim()}><Send size={17} className="mr-2"/>Send</Button></div></form></div>
    <div className="mt-4 grid gap-3 text-xs text-slate-400 sm:grid-cols-3"><div className="rounded-2xl border border-white/10 bg-white/[.03] p-4"><Sparkles className="mb-2 text-teal-200" size={17}/><b className="text-slate-200">Multi-issue understanding</b><p className="mt-1">Separates distinct civic problems instead of merging them.</p></div><div className="rounded-2xl border border-white/10 bg-white/[.03] p-4"><TicketCheck className="mb-2 text-teal-200" size={17}/><b className="text-slate-200">Ticket-aware</b><p className="mt-1">Citizens see their tickets; employees can inspect operational details.</p></div><div className="rounded-2xl border border-white/10 bg-white/[.03] p-4"><Bot className="mb-2 text-teal-200" size={17}/><b className="text-slate-200">Action focused</b><p className="mt-1">Answers with useful outcomes and next steps, not model internals.</p></div></div>
  </div></div>
}

async function answer(text:string,staff:boolean):Promise<string>{
  const ticketCode=text.match(/CR-[A-Z0-9-]+/i)?.[0]?.toUpperCase();
  if(ticketCode){
    if(staff){const ticket=await api.getStaffTicket(ticketCode);return staffTicketSummary(ticket)}
    const ticket=await api.getTicket(ticketCode);return citizenTicketSummary(ticket)
  }
  const lower=text.toLowerCase();
  if(staff&&(lower.includes("queue")||lower.includes("active")||lower.includes("pending")||lower.includes("escalated"))){
    const tickets=await api.listTickets();const active=tickets.filter(t=>["SUBMITTED","ASSIGNED","IN_PROGRESS","ESCALATED"].includes(t.status));const escalated=tickets.filter(t=>t.status==="ESCALATED").length;return `You currently have ${active.length} active tickets in the queue, including ${escalated} escalated ticket${escalated===1?"":"s"}. ${active.slice(0,4).map(t=>`${t.ticket_code} (${t.category}, ${t.status.replaceAll("_"," ")})`).join(" · ")||"No active tickets right now."}`;
  }
  if(!staff&&(lower.includes("my complaint")||lower.includes("my ticket")||lower.includes("how many"))){
    const tickets=await api.myTickets();const active=tickets.filter(t=>t.status!=="RESOLVED").length;return `You have ${tickets.length} complaint ticket${tickets.length===1?"":"s"} in total and ${active} still active. ${tickets.slice(0,4).map(t=>`${t.ticket_code} — ${t.category}: ${t.status.replaceAll("_"," ")}`).join("\n")}`;
  }
  const batch=await api.analyzeBatch({complaint:text,verify_location:false});return complaintSummary(batch,staff);
}

function complaintSummary(batch:ComplaintBatchAnalysis,staff:boolean){
  const lines=batch.issues.map((issue,i)=>`${i+1}. ${issue.category} — ${issue.priority} priority — ${issue.department}${issue.location?` — ${issue.location}`:" — location still needed"}`);
  const intro=batch.issue_count>1?`I found ${batch.issue_count} separate civic problems:`:"I found one civic problem:";
  const next=staff?"You can use this classification while reviewing or routing the citizen's ticket.":"If you want to submit this, open Submit Complaint so the location can be verified before ticket creation.";
  return `${intro}\n${lines.join("\n")}\n\n${next}`;
}
function citizenTicketSummary(ticket:Ticket){return `${ticket.ticket_code}\n${ticket.category} · ${ticket.status.replaceAll("_"," ")} · ${ticket.priority} priority\nDepartment: ${ticket.department}\nLocation: ${ticket.location}\nSLA: ${ticket.sla_state}\n\n${ticket.citizen_response}`}
function staffTicketSummary(ticket:StaffTicket){return `${ticket.ticket_code}\n${ticket.category} · ${ticket.status.replaceAll("_"," ")} · ${ticket.priority} priority\nCitizen: ${ticket.citizen?.name||"Unavailable"}${ticket.citizen?.email?` (${ticket.citizen.email})`:""}\nLocation: ${ticket.location}\nDepartment: ${ticket.department}\n\nProblem statement:\n${ticket.complaint}`}
