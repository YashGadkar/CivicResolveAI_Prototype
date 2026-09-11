import { useEffect, useState } from "react";
import { Activity, BarChart3, Building2, Landmark, LogOut, Moon, Search, Send, ShieldCheck, Sun, TicketCheck, Workflow } from "lucide-react";
import { Link, NavLink, Route, Routes } from "react-router-dom";
import { api } from "./api";
import { Button } from "./components/ui/button";
import { cn } from "./lib/utils";
import type { User } from "./types";
import { AuthPage } from "./pages/AuthPage";
import { HomePage } from "./pages/HomePage";
import { SubmitPage } from "./pages/SubmitPage";
import { MinePage, TrackPage } from "./pages/TrackMinePages";
import { OfficerPage } from "./pages/OfficerPage";
import { CommandCenterPage } from "./pages/CommandCenterPage";
import { AdminPage } from "./pages/AdminPage";
import { Page } from "./components/app-ui";

type Theme = "light" | "dark";

function initialTheme(): Theme {
  try {
    return localStorage.getItem("civicresolve-theme") === "dark" ? "dark" : "light";
  } catch {
    return "light";
  }
}

export default function App(){
  const[user,setUser]=useState<User|null>(null);
  const[loading,setLoading]=useState(true);
  const[theme,setTheme]=useState<Theme>(initialTheme);
  useEffect(()=>{document.documentElement.classList.toggle("dark",theme==="dark");try{localStorage.setItem("civicresolve-theme",theme)}catch{}},[theme]);
  useEffect(()=>{api.me().then(setUser).catch(()=>setUser(null)).finally(()=>setLoading(false))},[]);
  const toggleTheme=()=>setTheme(t=>t==="light"?"dark":"light");
  if(loading)return <div className="grid min-h-screen place-items-center bg-[#081525] text-white"><div className="text-center"><Activity className="mx-auto animate-spin text-teal-300"/><p className="mt-3 text-sm text-slate-300">Opening CivicResolve…</p></div></div>;
  if(!user)return <AuthPage onAuth={setUser} theme={theme} onToggleTheme={toggleTheme}/>;
  return <Shell user={user} theme={theme} onToggleTheme={toggleTheme} onLogout={async()=>{await api.logout();setUser(null)}}/>
}

function Shell({user,onLogout,theme,onToggleTheme}:{user:User;onLogout:()=>void;theme:Theme;onToggleTheme:()=>void}){
  const staff=["OFFICER","ADMIN"].includes(user.role);const admin=user.role==="ADMIN";
  const citizen:[string,string,typeof Send][]=[["/","Overview",Landmark],["/submit","Submit",Send],["/mine","My complaints",TicketCheck],["/track","Track",Search],["/command-center","Civic Assistant",Workflow]];
  const employee:[string,string,typeof Send][]=[["/","Overview",Landmark],["/officer","Ticket operations",Building2],["/command-center","Civic Assistant",Workflow]];
  if(admin)employee.push(["/admin","Analytics",BarChart3]);const nav=staff?employee:citizen;
  return <div className="min-h-screen bg-[#f5f7fb] text-slate-900 transition-colors dark:bg-[#07111f] dark:text-slate-100"><div className="h-1 bg-[linear-gradient(90deg,#f59e0b_0%,#f59e0b_32%,#f8fafc_32%,#f8fafc_66%,#0f766e_66%,#0f766e_100%)]"/><header className="sticky top-0 z-40 border-b border-slate-200/80 bg-white/95 shadow-[0_8px_30px_rgba(15,23,42,.04)] backdrop-blur dark:border-slate-800 dark:bg-[#0b1726]/95"><div className="mx-auto flex max-w-7xl items-center gap-4 px-4 py-3 lg:px-8"><Link to="/" className="flex shrink-0 items-center gap-3"><span className="grid h-10 w-10 place-items-center rounded-xl bg-[#0b1f3a] text-white dark:bg-teal-700"><Landmark size={20}/></span><span><b className="tracking-tight text-slate-950 dark:text-white">CivicResolve AI</b><small className="block text-[10px] font-bold uppercase tracking-[.16em] text-teal-700 dark:text-teal-300">Civic service platform</small></span></Link><nav className="ml-auto hidden items-center gap-1 lg:flex">{nav.map(([p,l,I])=><NavLink key={p} to={p} className={({isActive})=>cn("flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-semibold transition",isActive?"bg-[#0b1f3a] text-white dark:bg-teal-700":"text-slate-500 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white")}><I size={15}/>{l}</NavLink>)}</nav><div className="ml-auto flex items-center gap-2 lg:ml-2"><button onClick={onToggleTheme} aria-label="Toggle light and dark mode" className="grid h-9 w-9 place-items-center rounded-xl border border-slate-200 bg-white text-slate-600 transition hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200">{theme==="dark"?<Sun size={16}/>:<Moon size={16}/>}</button><div className="hidden text-right sm:block"><div className="text-xs font-bold text-slate-900 dark:text-white">{user.name}</div><div className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">{user.role}</div></div><Button size="sm" variant="outline" onClick={onLogout} aria-label="Sign out"><LogOut size={15}/></Button></div></div><div className="border-t border-slate-100 dark:border-slate-800 lg:hidden"><nav className="mx-auto flex max-w-7xl gap-1 overflow-x-auto px-3 py-2">{nav.map(([p,l,I])=><NavLink key={p} to={p} className={({isActive})=>cn("flex shrink-0 items-center gap-1.5 rounded-lg px-3 py-2 text-xs font-bold",isActive?"bg-[#0b1f3a] text-white dark:bg-teal-700":"text-slate-500 dark:text-slate-300")}><I size={14}/>{l}</NavLink>)}</nav></div></header><Routes><Route path="/" element={<HomePage user={user}/>}/><Route path="/submit" element={staff?<Denied/>:<SubmitPage/>}/><Route path="/mine" element={staff?<Denied/>:<MinePage/>}/><Route path="/track" element={<TrackPage/>}/><Route path="/command-center" element={<CommandCenterPage user={user}/>}/><Route path="/officer" element={staff?<OfficerPage/>:<Denied/>}/><Route path="/admin" element={admin?<AdminPage/>:<Denied/>}/></Routes><footer className="border-t border-slate-200 bg-white px-4 py-6 text-center text-xs text-slate-400 dark:border-slate-800 dark:bg-[#0b1726]">CivicResolve AI prototype · configurable SLA rules · synthetic analytics · no official government dispatch</footer></div>
}
function Denied(){return <Page title="Access restricted" eyebrow="Authorization" subtitle="This workspace is available only to authorized accounts."><div className="rounded-2xl border border-slate-200 bg-white py-12 text-center shadow-panel dark:border-slate-700 dark:bg-slate-900"><ShieldCheck className="mx-auto text-teal-700 dark:text-teal-300" size={44}/><p className="mt-4 text-slate-500 dark:text-slate-300">Your account does not have permission to open this page.</p></div></Page>}
