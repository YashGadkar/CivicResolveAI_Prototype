import { FormEvent, useEffect, useState } from "react";
import { Activity, Eye, EyeOff, FileClock, Landmark, Languages, LockKeyhole, Moon, ShieldCheck, Sun, UserPlus, UserRoundCheck } from "lucide-react";
import { api } from "../api";
import { Button } from "../components/ui/button";
import { Field, NoticeState, Toast } from "../components/app-ui";
import { cn } from "../lib/utils";
import type { User } from "../types";

export function AuthPage({ onAuth,theme,onToggleTheme }: { onAuth: (user: User) => void; theme:"light"|"dark"; onToggleTheme:()=>void }) {
  const [portal,setPortal]=useState<"citizen"|"employee">("citizen"); const [mode,setMode]=useState<"login"|"signup">("login");
  const [name,setName]=useState(""); const [email,setEmail]=useState(""); const [password,setPassword]=useState(""); const [show,setShow]=useState(false); const [busy,setBusy]=useState(false); const [notice,setNotice]=useState<NoticeState>(null);
  const rules=[password.length>=10,/[A-Z]/.test(password),/[a-z]/.test(password),/\d/.test(password),/[^A-Za-z0-9]/.test(password)];
  const clearFields=()=>{setName("");setEmail("");setPassword("");setShow(false)};
  useEffect(()=>{clearFields();const timer=window.setTimeout(clearFields,120);return()=>window.clearTimeout(timer)},[]);
  const switchPortal=(next:"citizen"|"employee")=>{setPortal(next);setMode("login");clearFields();setNotice(null)};
  const switchMode=(next:"login"|"signup")=>{setMode(next);clearFields();setNotice(null)};
  async function submit(e:FormEvent){e.preventDefault();setBusy(true);setNotice(null);try{const u=portal==="employee"?await api.employeeLogin({email,password}):mode==="signup"?await api.signUp({name,email,password}):await api.login({email,password});clearFields();onAuth(u)}catch(err){setNotice({tone:"error",title:"Sign-in failed",message:err instanceof Error?err.message:"Please try again."})}finally{setBusy(false)}}
  return <div className="auth-shell relative min-h-screen overflow-hidden px-4 py-8 text-white lg:py-12"><div className="auth-civic-photo auth-civic-photo-a"/><div className="auth-civic-photo auth-civic-photo-b"/><div className="auth-civic-photo auth-civic-photo-c"/>{notice&&<Toast notice={notice} onClose={()=>setNotice(null)}/>}<button onClick={onToggleTheme} className="absolute right-5 top-5 z-20 grid h-10 w-10 place-items-center rounded-xl border border-white/15 bg-slate-950/30 text-white backdrop-blur" aria-label="Toggle theme">{theme==="dark"?<Sun size={18}/>:<Moon size={18}/>}</button><div className="relative z-10 mx-auto grid min-h-[84vh] max-w-6xl overflow-hidden rounded-[30px] border border-white/10 bg-[#081525]/75 shadow-2xl backdrop-blur-xl lg:grid-cols-[1.05fr_.95fr]">
    <section className="hidden flex-col justify-between p-12 lg:flex"><div><div className="flex items-center gap-3 text-xl font-extrabold"><span className="grid h-12 w-12 place-items-center rounded-2xl border border-white/10 bg-white/10 text-teal-200"><Landmark/></span>CivicResolve AI</div><p className="mt-16 text-xs font-bold uppercase tracking-[.28em] text-teal-200">Civic service intelligence</p><h1 className="mt-5 max-w-xl text-5xl font-black leading-[1.08] tracking-[-.04em]">A clearer path from complaint to action.</h1><p className="mt-6 max-w-lg text-lg leading-8 text-slate-300">Citizens report issues naturally. Employees get a focused operations workspace to review tickets and move them toward resolution.</p></div><div className="grid grid-cols-3 gap-3 text-sm text-slate-200">{[[Languages,"Multilingual intake"],[ShieldCheck,"Protected accounts"],[FileClock,"Trackable progress"]].map(([Icon,label])=>{const I=Icon as typeof Languages;return <div className="rounded-2xl border border-white/10 bg-white/[.06] p-4" key={String(label)}><I className="mb-3 text-teal-200" size={20}/><span className="font-semibold">{String(label)}</span></div>})}</div></section>
    <section className="m-2 rounded-[25px] bg-white p-6 text-slate-900 sm:p-10 lg:m-4 lg:p-12 dark:bg-slate-950 dark:text-slate-100"><div className="mx-auto max-w-md"><p className="text-xs font-bold uppercase tracking-[.22em] text-civic-600 dark:text-teal-300">Secure access</p><h2 className="mt-3 text-3xl font-black">{portal==="employee"?"Employee portal":mode==="signup"?"Create citizen account":"Citizen sign in"}</h2><p className="mt-2 text-sm leading-6 text-slate-500 dark:text-slate-400">{portal==="employee"?"For authorized officers and administrators who manage complaint progress.":mode==="signup"?"Register with a Gmail address to submit and track complaints.":"Access your private complaint workspace."}</p>
      <div className="mt-7 grid grid-cols-2 rounded-2xl bg-slate-100 p-1 dark:bg-slate-900"><button type="button" className={cn("rounded-xl px-3 py-2.5 text-sm font-bold",portal==="citizen"&&"bg-white text-civic-800 shadow-sm dark:bg-slate-800 dark:text-white")} onClick={()=>switchPortal("citizen")}>Citizen</button><button type="button" className={cn("rounded-xl px-3 py-2.5 text-sm font-bold",portal==="employee"&&"bg-white text-civic-800 shadow-sm dark:bg-slate-800 dark:text-white")} onClick={()=>switchPortal("employee")}>Employee</button></div>
      {portal==="citizen"&&<div className="mt-4 flex gap-2 text-sm"><button type="button" className={cn("rounded-full px-3 py-1.5 font-semibold",mode==="login"?"bg-civic-50 text-civic-700 dark:bg-teal-950 dark:text-teal-200":"text-slate-500 dark:text-slate-400")} onClick={()=>switchMode("login")}>Sign in</button><button type="button" className={cn("rounded-full px-3 py-1.5 font-semibold",mode==="signup"?"bg-civic-50 text-civic-700 dark:bg-teal-950 dark:text-teal-200":"text-slate-500 dark:text-slate-400")} onClick={()=>switchMode("signup")}>New user</button></div>}
      <form className="mt-6 space-y-4" onSubmit={submit} autoComplete="off">{portal==="citizen"&&mode==="signup"&&<Field label="Full name"><input className="focus-field" value={name} onChange={e=>setName(e.target.value)} required minLength={2} autoComplete="off"/></Field>}<Field label={portal==="employee"?"Employee email":"Gmail address"}><input className="focus-field" type="email" value={email} onChange={e=>setEmail(e.target.value)} placeholder={portal==="employee"?"officer@department.gov":"name@gmail.com"} required autoComplete="off" name="civicresolve-login-email"/></Field><Field label="Password"><div className="relative"><input className="focus-field pr-12" type={show?"text":"password"} value={password} onChange={e=>setPassword(e.target.value)} required autoComplete="new-password" name="civicresolve-login-password"/><button type="button" aria-label={show?"Hide password":"Show password"} onClick={()=>setShow(v=>!v)} className="absolute right-3 top-1/2 -translate-y-1/2 rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800">{show?<EyeOff size={18}/>:<Eye size={18}/>}</button></div></Field>
      {portal==="citizen"&&mode==="signup"&&<div className="grid grid-cols-2 gap-2 rounded-xl bg-slate-50 p-3 text-xs dark:bg-slate-900">{["10+ characters","Uppercase","Lowercase","Number","Special character"].map((r,i)=><span className={rules[i]?"font-semibold text-emerald-700 dark:text-emerald-300":"text-slate-400"} key={r}>✓ {r}</span>)}</div>}
      <Button size="lg" className="w-full" disabled={busy}>{busy?<Activity className="mr-2 animate-spin" size={18}/>:portal==="employee"?<UserRoundCheck className="mr-2" size={18}/>:mode==="signup"?<UserPlus className="mr-2" size={18}/>:<LockKeyhole className="mr-2" size={18}/>} {portal==="employee"?"Employee sign in":mode==="signup"?"Create account":"Sign in"}</Button></form>
      {portal==="employee" && (
        <div className="mt-5 rounded-2xl border border-slate-200 bg-slate-50/80 p-4 dark:border-slate-800 dark:bg-slate-900/60">
          <div className="flex items-center justify-between">
            <p className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">Demo Employee Quick-Fill</p>
            <span className="text-[11px] font-mono text-slate-400 dark:text-slate-500">Pass: Password@1234</span>
          </div>
          <div className="mt-2.5 flex flex-wrap gap-1.5">
            {[
              { label: "👮‍♂️ Roads Officer", email: "rohan.sharma@civicresolve.gov.in" },
              { label: "💧 Water Officer", email: "priya.water@civicresolve.gov.in" },
              { label: "⚡ Electrical Officer", email: "patil.electrical@civicresolve.gov.in" },
              { label: "🧹 Sanitation Officer", email: "ananya.sanitation@civicresolve.gov.in" },
              { label: "🛡️ Governance Admin", email: "admin@civicresolve.gov.in" },
              { label: "📋 General Officer", email: "officer@civicresolve.local" },
            ].map((item) => (
              <button
                key={item.email}
                type="button"
                onClick={() => {
                  setEmail(item.email);
                  setPassword("Password@1234");
                }}
                className="rounded-lg border border-slate-300 bg-white px-2.5 py-1 text-xs font-semibold text-slate-700 shadow-sm transition hover:border-civic-500 hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
              >
                {item.label}
              </button>
            ))}
          </div>
        </div>
      )}
      <p className="mt-5 text-xs leading-5 text-slate-400">{portal==="employee"?"Employee accounts are provisioned by the system administrator; public employee sign-up is disabled.":"Citizen registration validates Gmail format. Email ownership verification should be added for a real deployment."}</p>
    </div></section>
  </div></div>;
}
