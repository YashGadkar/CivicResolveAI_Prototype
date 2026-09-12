import { useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { AlertTriangle, ArrowRightLeft, Building2, FileUp, Languages, MapPin, Phone, Search, ShieldAlert, UserRound, Users, X } from "lucide-react";
import { api } from "../api";
import type { TranslationLanguage, TranslationResult } from "../api";
import { Kpi, NoticeState, Page, ProgressBar, Toast } from "../components/app-ui";
import { ProblemMap } from "../components/problem-map";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import type { EnrichedTicket, StaffMember } from "../types";

export function OfficerPage(){
  const[tickets,setTickets]=useState<EnrichedTicket[]>([]);
  const[departments,setDepartments]=useState<string[]>([]);
  const[languages,setLanguages]=useState<TranslationLanguage[]>([]);
  const[staffMembers,setStaffMembers]=useState<StaffMember[]>([]);
  const[filter,setFilter]=useState("ALL");
  const[search,setSearch]=useState("");
  const[notice,setNotice]=useState<NoticeState>(null);
  const[selected,setSelected]=useState<EnrichedTicket|null>(null);
  const[busy,setBusy]=useState(false);

  async function refresh(){
    try{
      const data=await api.platformStaffTickets();
      setTickets(data);
      if(selected){
        const latest=data.find(x=>x.ticket.ticket_code===selected.ticket.ticket_code);
        if(latest)setSelected(latest);
      }
    }catch(e){
      setNotice({tone:"error",title:"Could not load ticket queue",message:e instanceof Error?e.message:"Please retry."});
    }
  }

  useEffect(()=>{
    void refresh();
    void Promise.all([api.staffDepartments(),api.translationLanguages(),api.staffMembers()])
      .then(([departmentList,languageList,members])=>{setDepartments(departmentList);setLanguages(languageList);setStaffMembers(members)})
      .catch((e:Error)=>setNotice({tone:"error",title:"Staff tools unavailable",message:e.message}));
  },[]);// eslint-disable-line react-hooks/exhaustive-deps

  const shown=useMemo(()=>tickets.filter(item=>{
    const t=item.ticket;
    const ok=filter==="ALL"||t.status===filter;
    const hay=`${t.ticket_code} ${t.category} ${t.location} ${t.department} ${item.citizen?.name||""} ${item.assignee?.name||""} ${t.complaint}`.toLowerCase();
    return ok&&hay.includes(search.trim().toLowerCase());
  }),[tickets,filter,search]);

  const kpis=[["Total",tickets.length],["New",tickets.filter(x=>x.ticket.status==="SUBMITTED").length],["Active",tickets.filter(x=>["ASSIGNED","IN_PROGRESS"].includes(x.ticket.status)).length],["Escalated",tickets.filter(x=>x.ticket.status==="ESCALATED").length],["Safety flags",tickets.filter(x=>x.meta.emergency).length]];

  async function quickStatus(item:EnrichedTicket,status:string){
    setBusy(true);
    try{
      await api.updateStatus(item.ticket.ticket_code,status,`Employee updated ticket to ${status}.`);
      await refresh();
      setNotice({tone:"success",title:"Ticket updated",message:`${item.ticket.ticket_code} is now ${status.replaceAll("_"," ").toLowerCase()}.`});
    }catch(e){
      setNotice({tone:"error",title:"Status update failed",message:e instanceof Error?e.message:"Please retry."});
    }finally{setBusy(false)}
  }

  return <Page title="Civic operations desk" eyebrow="Employee & administrator workspace" subtitle="Review the citizen statement, translate it when needed, verify location, assign accountable staff and route work safely.">
    {notice&&<Toast notice={notice} onClose={()=>setNotice(null)}/>} 
    {selected&&<TicketDrawer key={selected.ticket.ticket_code} item={selected} departments={departments} languages={languages} staffMembers={staffMembers} onClose={()=>setSelected(null)} onChanged={async()=>{await refresh();setSelected(await api.platformTicket(selected.ticket.ticket_code))}} notify={setNotice}/>} 
    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">{kpis.map(([l,v])=><Kpi key={String(l)} label={String(l)} value={String(v)}/>)}</div>
    <Card className="mt-6 overflow-hidden border-slate-200 shadow-panel dark:border-slate-800 dark:bg-slate-900">
      <div className="flex flex-col gap-3 border-b border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900 lg:flex-row lg:items-center lg:justify-between">
        <div className="relative max-w-xl flex-1"><Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16}/><input className="focus-field pl-9" placeholder="Search ticket, citizen, officer, complaint or location…" value={search} onChange={e=>setSearch(e.target.value)}/></div>
        <select className="rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-sm font-semibold dark:border-slate-700 dark:bg-slate-800 dark:text-white" value={filter} onChange={e=>setFilter(e.target.value)}>{["ALL","SUBMITTED","ASSIGNED","IN_PROGRESS","ESCALATED","RESOLVED"].map(s=><option key={s}>{s}</option>)}</select>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[1180px] text-left text-sm">
          <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500 dark:bg-slate-800 dark:text-slate-300"><tr>{["Ticket","Citizen","Issue","Location","Department","Priority","Progress","Incident","Actions"].map(h=><th key={h} className="px-4 py-3">{h}</th>)}</tr></thead>
          <tbody>{shown.map(item=>{const t=item.ticket;return <tr className="border-t border-slate-100 bg-white transition hover:bg-slate-50/70 dark:border-slate-800 dark:bg-slate-900 dark:hover:bg-slate-800/60" key={t.ticket_code}>
            <td className="px-4 py-4"><div className="font-black text-slate-900 dark:text-white">{t.ticket_code}</div><div className="mt-1 text-xs text-slate-400">{t.language}</div>{item.meta.emergency&&<div className="mt-2 inline-flex items-center gap-1 rounded-full bg-rose-50 px-2 py-1 text-[10px] font-black uppercase text-rose-700 dark:bg-rose-950/40 dark:text-rose-200"><ShieldAlert size={11}/>Safety</div>}</td>
            <td className="px-4 py-4"><b className="text-slate-800 dark:text-slate-100">{item.citizen?.name||"Citizen"}</b><div className="mt-1 max-w-44 truncate text-xs text-slate-400">{item.citizen?.email||"No account detail"}</div></td>
            <td className="px-4 py-4"><div className="font-semibold">{t.category}</div><div className="mt-1 max-w-52 line-clamp-2 text-xs leading-5 text-slate-500 dark:text-slate-400">{t.complaint}</div></td>
            <td className="px-4 py-4"><div className="max-w-44 line-clamp-2">{t.location}</div>{item.meta.ward&&<div className="mt-1 text-xs text-slate-400">{item.meta.ward}</div>}</td>
            <td className="px-4 py-4">{t.department}</td><td className="px-4 py-4"><Badge value={t.priority}/></td><td className="px-4 py-4"><ProgressBar ticket={t} compact/></td>
            <td className="px-4 py-4">{item.meta.related_reports>1?<div className="flex items-center gap-1 font-bold text-amber-700 dark:text-amber-300"><Users size={15}/>{item.meta.related_reports} reports</div>:<span className="text-xs text-slate-400">Single report</span>}</td>
            <td className="px-4 py-4"><div className="flex flex-wrap gap-2"><Button size="sm" variant="outline" onClick={()=>setSelected(item)}>Open</Button>{t.status==="SUBMITTED"&&<Button size="sm" onClick={()=>void quickStatus(item,"ASSIGNED")} disabled={busy}>Accept</Button>}{["ASSIGNED","ESCALATED"].includes(t.status)&&<Button size="sm" onClick={()=>void quickStatus(item,"IN_PROGRESS")} disabled={busy}>Start work</Button>}</div></td>
          </tr>})}</tbody>
        </table>
        {shown.length===0&&<div className="p-10 text-center text-sm text-slate-500">No tickets match this view.</div>}
      </div>
    </Card>
  </Page>
}

function TicketDrawer({item,departments,languages,staffMembers,onClose,onChanged,notify}:{item:EnrichedTicket;departments:string[];languages:TranslationLanguage[];staffMembers:StaffMember[];onClose:()=>void;onChanged:()=>Promise<void>;notify:(n:NoticeState)=>void}){
  const t=item.ticket;
  const[officer,setOfficer]=useState(item.assignee?.email||t.assigned_officer||"");
  const[department,setDepartment]=useState(t.department);
  const[reason,setReason]=useState("");
  const[note,setNote]=useState(item.meta.resolution_note||"");
  const[file,setFile]=useState<File|null>(null);
  const[busy,setBusy]=useState(false);
  const[targetLanguage,setTargetLanguage]=useState(()=>languages.find(l=>l.name!==t.language)?.code||"en");
  const[translation,setTranslation]=useState<TranslationResult|null>(null);
  const[translating,setTranslating]=useState(false);
  const departmentOptions=departments.includes(t.department)?departments:[t.department,...departments];
  const hasLegacyAssignment=Boolean(officer)&&!staffMembers.some(member=>(member.email||member.name)===officer);

  async function act(fn:()=>Promise<unknown>,success:string){
    setBusy(true);
    try{await fn();await onChanged();notify({tone:"success",title:"Ticket updated",message:success})}
    catch(e){notify({tone:"error",title:"Action failed",message:e instanceof Error?e.message:"Please retry."})}
    finally{setBusy(false)}
  }

  async function upload(){if(!file)return;await act(()=>api.uploadEvidence(t.ticket_code,file,"RESOLUTION_EVIDENCE"),"Resolution evidence attached and made available to the citizen who owns this ticket.");setFile(null)}

  async function translate(){
    setTranslating(true);
    setTranslation(null);
    try{
      const result=await api.translateTicket(t.ticket_code,targetLanguage);
      setTranslation(result);
    }catch(e){
      notify({tone:"error",title:"Translation failed",message:e instanceof Error?e.message:"Please retry."});
    }finally{setTranslating(false)}
  }

  async function transfer(){
    setBusy(true);
    try{
      await api.transferTicket(t.ticket_code,department,reason);
      setReason("");
      setOfficer("");
      await onChanged();
      notify({tone:"success",title:"Department transferred",message:`${t.ticket_code} moved to ${department}. Previous officer ownership was cleared when required and the transfer was written to the audit trail.`});
    }catch(e){
      notify({tone:"error",title:"Transfer failed",message:e instanceof Error?e.message:"Please retry."});
    }finally{setBusy(false)}
  }

  return <div className="fixed inset-0 z-50 bg-slate-950/55 backdrop-blur-sm">
    <div className="absolute inset-y-0 right-0 w-full max-w-4xl overflow-y-auto border-l border-slate-200 bg-white shadow-2xl dark:border-slate-800 dark:bg-[#0b1726]">
      <div className="sticky top-0 z-10 flex items-start justify-between border-b border-slate-200 bg-white/95 px-5 py-4 backdrop-blur dark:border-slate-800 dark:bg-[#0b1726]/95">
        <div><p className="text-xs font-black uppercase tracking-[.18em] text-teal-700 dark:text-teal-300">Staff ticket detail</p><h2 className="mt-1 text-xl font-black text-slate-950 dark:text-white">{t.ticket_code}</h2></div>
        <button className="rounded-xl border border-slate-200 p-2 text-slate-500 hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-800" onClick={onClose}><X/></button>
      </div>

      <div className="space-y-4 p-5">
        <section className="rounded-2xl bg-[linear-gradient(135deg,#0b1f3a,#0f766e)] p-5 text-white">
          <div className="flex flex-wrap items-start justify-between gap-4"><div><div className="text-xs font-black uppercase tracking-[.18em] text-teal-100">{t.category} · {t.language}</div><h3 className="mt-2 text-xl font-black">Original citizen statement</h3><p className="mt-2 max-w-3xl text-sm leading-6 text-slate-100">{t.complaint}</p></div><Badge value={t.priority}/></div>
        </section>

        <Card className="overflow-hidden border-teal-200 bg-gradient-to-br from-teal-50 to-cyan-50 shadow-sm dark:border-teal-900 dark:from-teal-950/30 dark:to-slate-900">
          <CardHeader className="pb-2"><CardTitle className="flex items-center gap-2 text-lg"><Languages className="text-teal-700 dark:text-teal-300" size={19}/>Translate citizen statement</CardTitle></CardHeader>
          <CardContent>
            <p className="text-sm leading-5 text-slate-600 dark:text-slate-300">Translate the original statement into the language preferred by the officer or administrator. The original text is always preserved.</p>
            <div className="mt-3 grid gap-2 sm:grid-cols-[1fr_auto]">
              <select className="focus-field" value={targetLanguage} onChange={e=>{setTargetLanguage(e.target.value);setTranslation(null)}}>
                {(languages.length?languages:[{code:"en",name:"English"},{code:"hi",name:"Hindi"},{code:"mr",name:"Marathi"}]).map(language=><option key={language.code} value={language.code}>{language.name}</option>)}
              </select>
              <Button onClick={()=>void translate()} disabled={translating}><Languages className="mr-2" size={16}/>{translating?"Translating…":"Translate"}</Button>
            </div>
            {translation&&<div className="mt-3 rounded-xl border border-teal-200 bg-white p-4 dark:border-teal-800 dark:bg-slate-950/40"><div className="flex flex-wrap items-center justify-between gap-2"><b className="text-sm text-slate-900 dark:text-white">{translation.target_language_name} translation</b><span className="text-[10px] font-bold uppercase tracking-wide text-slate-400">{translation.provider}</span></div><p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-slate-700 dark:text-slate-200">{translation.translated_text}</p><p className="mt-2 text-xs text-slate-400">Verify names, addresses and safety-critical details against the original statement before action.</p></div>}
          </CardContent>
        </Card>

        <div className="grid gap-3 md:grid-cols-2"><Info icon={<UserRound/>} title="Citizen"><b>{item.citizen?.name||"Unknown citizen"}</b><p>{item.citizen?.email||"No email available"}</p>{item.citizen?.contact&&<p><Phone className="mr-1 inline" size={13}/>{item.citizen.contact}</p>}</Info><Info icon={<MapPin/>} title="Location"><b>{t.location}</b><p>{[item.meta.ward,item.meta.zone,item.meta.city].filter(Boolean).join(" · ")||"No ward/zone metadata"}</p></Info></div>
        <ProblemMap location={t.location} latitude={item.meta.latitude} longitude={item.meta.longitude} title="Problem location" compact />
        {item.meta.emergency&&<div className="flex gap-3 rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-900 dark:border-rose-900 dark:bg-rose-950/30 dark:text-rose-100"><AlertTriangle className="shrink-0"/><div><b>Potential immediate safety risk</b><p className="mt-1 text-xs leading-5 opacity-80">Prioritize human review. The platform does not replace emergency dispatch.</p></div></div>}
        {item.meta.related_reports>1&&<div className="rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900 dark:border-amber-900 dark:bg-amber-950/30 dark:text-amber-200"><b>{item.meta.related_reports} related citizen reports</b><p className="mt-1 text-xs leading-5">This ticket belongs to a broader incident cluster for the same category and location.</p></div>}

        <Card className="dark:border-slate-800 dark:bg-slate-900">
          <CardHeader className="pb-2"><CardTitle className="text-lg">Ownership & routing</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <div>
              <div className="mb-2 flex items-center justify-between gap-2"><p className="text-xs font-black uppercase tracking-wide text-slate-400">Assigned officer / team</p>{item.assignee&&<span className="text-xs font-semibold text-teal-700 dark:text-teal-300">{item.assignee.name} · {item.assignee.role}</span>}</div>
              <div className="grid gap-2 sm:grid-cols-[1fr_auto]">
                <select className="focus-field" value={officer} onChange={e=>setOfficer(e.target.value)}>
                  <option value="">Unassigned</option>
                  {hasLegacyAssignment&&<option value={officer}>{item.assignee?.name||officer} · current</option>}
                  {staffMembers.map(member=><option key={member.email||member.name} value={member.email||member.name}>{member.name} · {member.role}</option>)}
                </select>
                <Button onClick={()=>void act(()=>api.assignTicket(t.ticket_code,officer),officer?"Officer assignment updated.":"Ticket unassigned.")} disabled={busy}>Assign</Button>
              </div>
              {item.assignee?.email&&<p className="mt-2 text-xs text-slate-500 dark:text-slate-400">Current staff contact: {item.assignee.email}</p>}
            </div>
            <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-800/60">
              <div className="mb-3 flex items-center gap-2"><ArrowRightLeft size={17} className="text-teal-700 dark:text-teal-300"/><b className="text-sm text-slate-900 dark:text-white">Controlled department transfer</b></div>
              <div className="grid gap-2">
                <select className="focus-field" value={department} onChange={e=>setDepartment(e.target.value)}>{departmentOptions.map(value=><option key={value} value={value}>{value}{value===t.department?" · current":""}</option>)}</select>
                <textarea className="focus-field min-h-16" value={reason} onChange={e=>setReason(e.target.value)} placeholder="Reason for transfer"/>
                <p className="text-xs leading-5 text-slate-500 dark:text-slate-400">Every transfer records the previous department, destination, reason, staff identity and timestamp. Existing assignment is cleared when required.</p>
                <Button variant="outline" onClick={()=>void transfer()} disabled={busy||department===t.department||reason.trim().length<3}><Building2 className="mr-2" size={16}/>Transfer department</Button>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="dark:border-slate-800 dark:bg-slate-900"><CardHeader className="pb-2"><CardTitle className="text-lg">Resolution evidence</CardTitle></CardHeader><CardContent><p className="mb-3 text-xs leading-5 text-slate-500 dark:text-slate-400">Evidence uploaded here is visible to the citizen who owns the ticket.</p><div className="space-y-2">{item.attachments.map(a=><a href={api.evidenceUrl(a.id)} target="_blank" rel="noreferrer" className="flex items-center justify-between rounded-xl border border-slate-200 p-3 text-sm dark:border-slate-700" key={a.id}><span><FileUp className="mr-2 inline text-teal-700" size={15}/>{a.original_name}</span><span className="text-xs text-slate-400">{a.kind.replaceAll("_"," ")}</span></a>)}</div><div className="mt-4 flex flex-col gap-2 sm:flex-row"><input type="file" className="min-w-0 flex-1 text-xs" accept="image/jpeg,image/png,image/webp,video/mp4,application/pdf" onChange={e=>setFile(e.target.files?.[0]||null)}/><Button size="sm" variant="outline" onClick={()=>void upload()} disabled={!file||busy}>Upload</Button></div><textarea className="focus-field mt-4 min-h-24" value={note} onChange={e=>setNote(e.target.value)} placeholder="Describe what was done, inspected and any follow-up required…"/><Button className="mt-3 w-full" onClick={()=>void act(()=>api.resolveWithNote(t.ticket_code,note),"Ticket marked resolved and sent for citizen confirmation.")} disabled={busy||note.trim().length<3}>Mark resolved with note</Button></CardContent></Card>

        <Card className="dark:border-slate-800 dark:bg-slate-900"><CardHeader className="pb-2"><CardTitle className="text-lg">Activity history</CardTitle></CardHeader><CardContent className="space-y-3">{t.audit_events.map((e,i)=>{const transferEvent=e.event==="DEPARTMENT_TRANSFERRED";return <div className={transferEvent?"rounded-xl border border-cyan-200 bg-cyan-50 p-3 dark:border-cyan-900 dark:bg-cyan-950/20":"border-l-2 border-teal-200 pl-4 dark:border-teal-800"} key={`${e.event}-${i}`}><b className="flex items-center gap-2 text-sm text-slate-900 dark:text-white">{transferEvent&&<ArrowRightLeft size={15} className="text-cyan-700 dark:text-cyan-300"/>}{e.event.replaceAll("_"," ")}</b><p className="mt-1 text-sm leading-5 text-slate-500 dark:text-slate-400">{e.detail}</p><small className="text-slate-400">{new Date(e.created_at).toLocaleString()}</small></div>})}</CardContent></Card>
      </div>
    </div>
  </div>
}

function Info({icon,title,children}:{icon:ReactNode;title:string;children:ReactNode}){return <div className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900"><div className="mb-2 flex items-center gap-2 text-xs font-black uppercase tracking-[.16em] text-teal-700 dark:text-teal-300"><span className="[&>svg]:h-4 [&>svg]:w-4">{icon}</span>{title}</div><div className="space-y-1 text-sm text-slate-600 dark:text-slate-300">{children}</div></div>}
