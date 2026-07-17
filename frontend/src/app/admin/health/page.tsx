"use client";

import { useEffect, useState } from "react";
import AdminShell from "@/components/AdminShell";
import { Kicker, Spinner } from "@/components/ui";
import { API_BASE, getHealth, type HealthLive } from "@/lib/api";

interface ReadyComponents {
  [key: string]: string;
}

export default function AdminHealthPage() {
  const [live, setLive] = useState<HealthLive | null>(null);
  const [components, setComponents] = useState<ReadyComponents>({});
  const [info, setInfo] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [lastChecked, setLastChecked] = useState<string>("");

  async function load() {
    setError(null);
    try {
      const l = await getHealth();
      setLive(l);
      const [ready, inf] = await Promise.all([
        fetch(`${API_BASE}/api/v1/health/ready`).then((r) => r.json()).catch(() => null),
        fetch(`${API_BASE}/api/v1/health/info`).then((r) => r.json()).catch(() => null),
      ]);
      if (ready?.components) setComponents(ready.components);
      if (inf) setInfo(inf);
      setLastChecked(new Date().toLocaleTimeString());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Backend unreachable.");
    }
  }

  useEffect(() => {
    load();
    const t = setInterval(load, 15000);
    return () => clearInterval(t);
  }, []);

  const uptime = live
    ? `${Math.floor(live.uptime_seconds / 86400)}d ${Math.floor((live.uptime_seconds % 86400) / 3600)}h ${Math.floor((live.uptime_seconds % 3600) / 60)}m ${Math.floor(live.uptime_seconds % 60)}s`
    : "—";

  function componentBadge(status: string) {
    if (status === "healthy" || status === "connected" || status === "ok")
      return "bg-[#e6f7ec] text-green";
    if (status === "not_configured") return "bg-[#fff3cd] text-[#8a6d00]";
    return "bg-[#fde2e6] text-[#c22f4f]";
  }

  return (
    <AdminShell>
      <div className="flex flex-wrap items-end justify-between gap-4 mb-6">
        <div>
          <Kicker>Admin · System Health</Kicker>
          <h1 className="font-serif font-medium text-[28px] mt-1">System Health</h1>
        </div>
        <span className="text-xs text-gray-400">
          Auto-refreshes every 15s{lastChecked && ` · last check ${lastChecked}`}
        </span>
      </div>

      {error ? (
        <div className="bg-[#fde2e6] text-[#c22f4f] rounded-md px-5 py-4 text-sm">
          ⚠ {error} — check that the backend is running at {API_BASE}.
        </div>
      ) : !live ? (
        <div className="flex items-center justify-center py-32 gap-3 text-gray-500">
          <Spinner /> Checking backend health…
        </div>
      ) : (
        <div className="grid md:grid-cols-2 gap-5">
          {/* Liveness */}
          <div className="bg-white shadow-[0_8px_22px_rgba(0,0,0,0.05)]">
            <div className="bg-green-d text-white px-6 py-4.5">
              <b className="font-serif text-base">⚡ Liveness — /health/live</b>
            </div>
            <div className="p-6">
              {[
                ["Status", live.status.toUpperCase(), true],
                ["Service", live.service],
                ["Version", `v${live.version}`],
                ["Environment", live.environment],
                ["Uptime", uptime],
                ["Server time", new Date(live.timestamp).toLocaleString()],
              ].map(([k, v, badge]) => (
                <div
                  key={String(k)}
                  className="flex justify-between items-center py-2.5 border-b border-[#f5f0f1] last:border-0 text-[13.5px]"
                >
                  <span className="text-gray-500">{k}</span>
                  {badge ? (
                    <span className="text-[11.5px] font-bold px-3.5 py-1 rounded-full bg-[#e6f7ec] text-green">
                      ● {v}
                    </span>
                  ) : (
                    <b>{v}</b>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Readiness components */}
          <div className="bg-white shadow-[0_8px_22px_rgba(0,0,0,0.05)]">
            <div className="bg-ink text-white px-6 py-4.5">
              <b className="font-serif text-base">🧩 Components — /health/ready</b>
            </div>
            <div className="p-6">
              {Object.keys(components).length === 0 ? (
                <div className="text-gray-400 text-sm py-3">No component data reported.</div>
              ) : (
                Object.entries(components).map(([name, status]) => (
                  <div
                    key={name}
                    className="flex justify-between items-center py-2.5 border-b border-[#f5f0f1] last:border-0 text-[13.5px]"
                  >
                    <span className="text-gray-500 capitalize">
                      {name.replace(/_/g, " ")}
                    </span>
                    <span
                      className={`text-[11.5px] font-bold px-3.5 py-1 rounded-full uppercase ${componentBadge(status)}`}
                    >
                      {status.replace(/_/g, " ")}
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Build info */}
          <div className="bg-white shadow-[0_8px_22px_rgba(0,0,0,0.05)] md:col-span-2">
            <div className="bg-green-d text-white px-6 py-4.5">
              <b className="font-serif text-base">ℹ Application Info — /health/info</b>
            </div>
            <div className="p-6 grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {info ? (
                Object.entries(info).map(([k, v]) => (
                  <div key={k} className="bg-[#f7f2f3] rounded-md p-4">
                    <span className="block text-[10.5px] tracking-[1.5px] text-gray-400 uppercase mb-1">
                      {k.replace(/_/g, " ")}
                    </span>
                    <b className="font-serif text-[15px] break-all">
                      {typeof v === "object" ? JSON.stringify(v) : String(v)}
                    </b>
                  </div>
                ))
              ) : (
                <div className="text-gray-400 text-sm">No info available.</div>
              )}
            </div>
          </div>
        </div>
      )}
    </AdminShell>
  );
}
