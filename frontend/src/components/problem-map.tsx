import { ExternalLink, MapPin } from "lucide-react";

function mapUrls(latitude: number, longitude: number) {
  const span = 0.012;
  const left = longitude - span;
  const right = longitude + span;
  const bottom = latitude - span;
  const top = latitude + span;
  const embed = `https://www.openstreetmap.org/export/embed.html?bbox=${encodeURIComponent(`${left},${bottom},${right},${top}`)}&layer=mapnik&marker=${encodeURIComponent(`${latitude},${longitude}`)}`;
  const open = `https://www.openstreetmap.org/?mlat=${latitude}&mlon=${longitude}#map=16/${latitude}/${longitude}`;
  return { embed, open };
}

export function ProblemMap({
  location,
  latitude,
  longitude,
  title = "Problem location",
  compact = false,
}: {
  location: string | null | undefined;
  latitude: number | null | undefined;
  longitude: number | null | undefined;
  title?: string;
  compact?: boolean;
}) {
  const hasCoordinates = typeof latitude === "number" && typeof longitude === "number";
  const urls = hasCoordinates ? mapUrls(latitude, longitude) : null;

  return (
    <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-900">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 px-4 py-3 dark:border-slate-700">
        <div className="flex min-w-0 items-center gap-2">
          <span className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-teal-50 text-teal-700 dark:bg-teal-950/60 dark:text-teal-300">
            <MapPin size={18} />
          </span>
          <div className="min-w-0">
            <p className="text-xs font-black uppercase tracking-[.15em] text-slate-500 dark:text-slate-400">{title}</p>
            <p className="mt-0.5 truncate text-sm font-bold text-slate-900 dark:text-white">{location || "Location required"}</p>
          </div>
        </div>
        {urls && (
          <a
            href={urls.open}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 px-2.5 py-1.5 text-xs font-bold text-teal-700 transition hover:bg-teal-50 dark:border-slate-700 dark:text-teal-300 dark:hover:bg-teal-950/40"
          >
            Open map <ExternalLink size={13} />
          </a>
        )}
      </div>

      {urls ? (
        <iframe
          title={`${title}: ${location || "civic issue"}`}
          src={urls.embed}
          className={`w-full border-0 ${compact ? "h-44" : "h-64"}`}
          loading="lazy"
          referrerPolicy="no-referrer"
        />
      ) : (
        <div className={`grid place-items-center bg-slate-50 px-6 text-center dark:bg-slate-950/50 ${compact ? "h-36" : "h-44"}`}>
          <div className="max-w-sm">
            <MapPin className="mx-auto text-slate-300 dark:text-slate-600" size={28} />
            <p className="mt-2 text-sm font-bold text-slate-700 dark:text-slate-200">Map will appear after the location is verified</p>
            <p className="mt-1 text-xs leading-5 text-slate-500 dark:text-slate-400">Add a valid locality, ward, city or address so CivicResolve can place this problem on the map.</p>
          </div>
        </div>
      )}
      <div className="border-t border-slate-100 px-4 py-2 text-[10px] text-slate-400 dark:border-slate-800">Map data © OpenStreetMap contributors</div>
    </section>
  );
}
