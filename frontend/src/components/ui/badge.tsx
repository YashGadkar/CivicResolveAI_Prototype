import { cn } from "../../lib/utils";

const styles: Record<string, string> = {
  LOW: "bg-slate-100 text-slate-700",
  MEDIUM: "bg-amber-100 text-amber-800",
  HIGH: "bg-orange-100 text-orange-800",
  CRITICAL: "bg-rose-100 text-rose-800",
  SAFE: "bg-emerald-100 text-emerald-800",
  APPROACHING: "bg-amber-100 text-amber-800",
  BREACHED: "bg-rose-100 text-rose-800",
  COMPLETED: "bg-emerald-100 text-emerald-800",
  WAITING: "bg-slate-100 text-slate-700",
  "ACTION REQUIRED": "bg-amber-100 text-amber-800"
};

export function Badge({ value, className }: { value: string; className?: string }) {
  return (
    <span className={cn("inline-flex rounded-full px-2.5 py-1 text-xs font-bold", styles[value] ?? "bg-civic-100 text-civic-700", className)}>
      {value}
    </span>
  );
}
