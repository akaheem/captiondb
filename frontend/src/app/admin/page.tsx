"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import AdminShell from "@/components/AdminShell";
import { Kicker, Spinner, StatusPill } from "@/components/ui";
import {
  adminOverview,
  adminListRequests,
  adminDeleteRequest,
  getHealth,
  formatBytes,
  formatDuration,
  timeAgo,
  type AdminOverview,
  type AdminRequestItem,
  type HealthLive,
  type VideoStatus,
} from "@/lib/api";

const DONUT_COLORS: Record<string, string> = {
  Completed: "#17603a",
  Failed: "#f2547d",
  Processing: "#e8b931",
  Queued: "#e8b931",
  Idle: "#d8d8d8",
};

export default function AdminOverviewPage() {
  const [data, setData] = useState<AdminOverview | null>(null);
  const [recent, setRecent] = useState<AdminRequestItem[]>([]);
  const [health, setHealth] = useState<HealthLive | null>(null);
  const [filter, setFilter] = useState<"All" | VideoStatus>("All");
  const [error, setError] = useState<string | null>(null);

  async function load() {
    try {
      const [ov, reqs, h] = await Promise.all([
        adminOverview(7),
        adminListRequests({ limit: 8 }),
        getHealth().catch(() => null),
      ]);
      setData(ov);
      setRecent(reqs.data);
      setHealth(h);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load overview.");
    }
  }

  useEffect(() => {
    load();
  }, []);

  const donutGradient = useMemo(() => {
    if (!data) return "";
    const entries = Object.entries(data.status_breakdown);
    const total = entries.reduce((a, [, v]) => a + v, 0) || 1;
    let acc = 0;
    const stops = entries.map(([status, count]) => {
      const from = (acc / total) * 100;
      acc += count;
      const to = (acc / total) * 100;
      return `${DONUT_COLORS[status] ?? "#d8d8d8"} ${from}% ${to}%`;
    });
    return `conic-gradient(${stops.join(", ")})`;
  }, [data]);

  const maxDaily = useMemo(
    () =>
      Math.max(1, ...(data?.daily_requests.map((d) => Math.max(d.received, d.completed)) ?? [1])),
    [data],
  );

  const visibleRecent =
    filter === "All" ? recent : recent.filter((r) => r.status === filter);

  async function onDelete(id: string, name: string) {
    if (!confirm(`Delete request "${name}" and all its data?`)) return;
    try {
      await adminDeleteRequest(id);
      await load();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Delete failed.");
    }
  }

  if (error) {
    return (
      <AdminShell>
        <div className="bg-[#fde2e6] text-[#c22f4f] rounded-md px-5 py-4 text-sm">⚠ {error}</div>
      </AdminShell>
    );
  }

  if (!data) {
    return (
      <AdminShell>
        <div className="flex items-center justify-center py-32 gap-3 text-gray-500">
          <Spinner /> Loading platform statistics…
        </div>
      </AdminShell>
    );
  }

  const uptime = health
    ? `${Math.floor(health.uptime_seconds / 86400)}d ${Math.floor((health.uptime_seconds % 86400) / 3600)}h ${Math.floor((health.uptime_seconds % 3600) / 60)}m`
    : "—";

  return (
    <AdminShell>
      <div className="flex flex-wrap items-end justify-between gap-4 mb-6">
        <div>
          <Kicker>Admin · Overview</Kicker>
          <h1 className="font-serif font-medium text-[28px] mt-1">Platform Overview</h1>
        </div>
        <span
          className={`text-xs font-bold px-4.5 py-2 rounded-full ${
            health ? "bg-[#e6f7ec] text-green" : "bg-[#fde2e6] text-[#c22f4f]"
          }`}
        >
          ● Backend {health ? `Online · v${health.version}` : "Unreachable"}
        </span>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
        {[
          { icon: "📥", v: data.requests_received, l: "Requests Received", pink: true },
          { icon: "✓", v: data.requests_accomplished, l: "Accomplished", pink: false },
          { icon: "✗", v: data.requests_failed, l: "Failed", pink: true },
          { icon: "🎬", v: data.total_scenes.toLocaleString(), l: "Scenes Detected", pink: false },
          { icon: "✍", v: data.total_captions.toLocaleString(), l: "Captions Generated", pink: true },
        ].map((s) => (
          <div key={s.l} className="bg-white px-5 py-4 pt-6 relative shadow-[0_8px_22px_rgba(0,0,0,0.05)]">
            <div
              className={`absolute -top-3 -left-2 w-10 h-10 flex items-center justify-center text-base text-white shadow-[0_8px_16px_rgba(242,84,125,0.3)] ${
                s.pink ? "bg-pink" : "bg-green"
              }`}
            >
              {s.icon}
            </div>
            <b className="block font-serif text-[26px]">{s.v}</b>
            <span className="text-[11.5px] text-gray-400">{s.l}</span>
          </div>
        ))}
      </div>

      {/* Charts row */}
      <div className="flex flex-col xl:flex-row gap-5 mb-6">
        {/* Bars */}
        <div className="flex-[1.6] bg-white px-6 py-5 shadow-[0_8px_22px_rgba(0,0,0,0.05)]">
          <h3 className="font-serif text-base mb-4.5">Requests — Last 7 Days</h3>
          <div className="flex items-end gap-3.5 h-[170px] px-1.5">
            {data.daily_requests.map((d) => (
              <div key={d.date} className="flex-1 flex flex-col items-center gap-2 h-full justify-end">
                <div
                  className="w-full rounded-t bg-gradient-to-b from-green-l to-green transition-all"
                  style={{ height: `${(d.received / maxDaily) * 70}%`, minHeight: d.received ? 4 : 0 }}
                  title={`${d.received} received`}
                />
                <div
                  className="w-full rounded-t bg-gradient-to-b from-pink to-[#f98fab] transition-all"
                  style={{ height: `${(d.completed / maxDaily) * 70}%`, minHeight: d.completed ? 4 : 0 }}
                  title={`${d.completed} completed`}
                />
                <span className="text-[10.5px] text-gray-400">
                  {new Date(d.date + "T00:00:00").toLocaleDateString([], { weekday: "short" })}
                </span>
              </div>
            ))}
          </div>
          <div className="flex gap-4.5 mt-3.5 text-xs text-gray-500">
            <span><i className="inline-block w-2.5 h-2.5 rounded-sm bg-green mr-1.5" />Received</span>
            <span><i className="inline-block w-2.5 h-2.5 rounded-sm bg-pink mr-1.5" />Completed</span>
          </div>
        </div>

        {/* Donut */}
        <div className="flex-1 bg-white px-6 py-5 text-center shadow-[0_8px_22px_rgba(0,0,0,0.05)]">
          <h3 className="font-serif text-base mb-3">Status Breakdown</h3>
          <div
            className="w-[150px] h-[150px] rounded-full mx-auto my-3 flex items-center justify-center"
            style={{ background: donutGradient || "#eee" }}
          >
            <div className="w-24 h-24 rounded-full bg-white flex flex-col items-center justify-center">
              <b className="font-serif text-[22px]">{data.requests_received}</b>
              <span className="text-[10px] text-gray-400">TOTAL</span>
            </div>
          </div>
          <div className="text-xs text-gray-500 text-left mt-2.5 leading-8">
            {Object.entries(data.status_breakdown).map(([status, count]) => (
              <div key={status}>
                <i
                  className="inline-block w-2.5 h-2.5 rounded-sm mr-2"
                  style={{ background: DONUT_COLORS[status] ?? "#d8d8d8" }}
                />
                {status} — {count} (
                {Math.round((count / Math.max(1, data.requests_received)) * 100)}%)
              </div>
            ))}
            {Object.keys(data.status_breakdown).length === 0 && (
              <div className="text-gray-400">No requests yet.</div>
            )}
          </div>
        </div>

        {/* Health */}
        <div className="flex-1 bg-white px-6 py-5 shadow-[0_8px_22px_rgba(0,0,0,0.05)]">
          <h3 className="font-serif text-base mb-2">System Health</h3>
          {[
            {
              k: "⚡ API /health/live",
              v: health ? "HEALTHY" : "DOWN",
              ok: !!health,
            },
            { k: "🌱 Environment", v: health?.environment?.toUpperCase() ?? "—", ok: true },
            {
              k: "📦 Stored Video Data",
              v: formatBytes(data.total_storage_bytes),
              ok: true,
              plain: true,
            },
            { k: "⏱ Uptime", v: uptime, ok: true, plain: true },
            {
              k: "🚀 Avg. processing time",
              v: data.avg_processing_seconds
                ? `${formatDuration(data.avg_processing_seconds)} / video`
                : "—",
              ok: true,
              plain: true,
            },
            {
              k: "⚙ In progress now",
              v: String(data.requests_processing),
              ok: true,
              plain: true,
            },
          ].map((row) => (
            <div
              key={row.k}
              className="flex justify-between items-center py-2.5 border-b border-[#f5f0f1] last:border-0 text-[13px]"
            >
              <span>{row.k}</span>
              {row.plain ? (
                <span className="font-bold text-[12.5px]">{row.v}</span>
              ) : (
                <span
                  className={`text-[11.5px] font-bold px-3 py-1 rounded-full ${
                    row.ok ? "bg-[#e6f7ec] text-green" : "bg-[#fde2e6] text-[#c22f4f]"
                  }`}
                >
                  {row.v}
                </span>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Recent requests table */}
      <div className="bg-white shadow-[0_8px_22px_rgba(0,0,0,0.05)]">
        <div className="px-6 py-4.5 flex flex-wrap justify-between items-center gap-3 border-b border-[#f5f0f1]">
          <b className="font-serif text-[17px]">Recent Requests</b>
          <div className="flex gap-2.5">
            {(["All", "Completed", "Failed", "Processing"] as const).map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-4 py-2 rounded-full text-xs border transition-colors cursor-pointer ${
                  filter === f
                    ? "bg-green-d text-white border-green-d"
                    : "bg-[#f7f2f3] text-gray-600 border-gray-200 hover:border-pink"
                }`}
              >
                {f}
              </button>
            ))}
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-[13px] min-w-[860px]">
            <thead>
              <tr className="text-left text-gray-400 text-[11px] tracking-[1.5px]">
                <th className="px-6 py-3 border-b border-[#f5f0f1]">REQUEST / PROJECT</th>
                <th className="px-6 py-3 border-b border-[#f5f0f1]">DATA PROVIDED</th>
                <th className="px-6 py-3 border-b border-[#f5f0f1]">RESULTS GENERATED</th>
                <th className="px-6 py-3 border-b border-[#f5f0f1]">STATUS</th>
                <th className="px-6 py-3 border-b border-[#f5f0f1]">RECEIVED</th>
                <th className="px-6 py-3 border-b border-[#f5f0f1]">ACTIONS</th>
              </tr>
            </thead>
            <tbody>
              {visibleRecent.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center text-gray-400">
                    No requests{filter !== "All" ? ` with status "${filter}"` : " yet"}.
                  </td>
                </tr>
              )}
              {visibleRecent.map((r) => (
                <tr key={r.id} className="border-b border-[#faf5f6] last:border-0">
                  <td className="px-6 py-3.5">
                    <b className="font-serif text-[13.5px] text-gray-900">{r.project_name}</b>
                    <span className="block text-[11.5px] text-gray-400 mt-0.5">
                      {r.original_filename}
                    </span>
                  </td>
                  <td className="px-6 py-3.5 text-gray-600">
                    {r.metadata
                      ? `${formatDuration(r.metadata.duration_seconds)} · ${r.metadata.resolution} · ${Math.round(r.metadata.fps)}fps · ${r.metadata.format} · ${formatBytes(r.metadata.size_bytes)}`
                      : "— no metadata"}
                  </td>
                  <td className="px-6 py-3.5 text-gray-600">
                    {r.status === "Completed"
                      ? `${r.scenes_count} scenes · ${r.captions_count} captions`
                      : r.status === "Processing" || r.status === "Queued"
                        ? `${Math.round(r.progress_percent)}% · ${r.current_stage ?? "in progress…"}`
                        : r.status === "Failed"
                          ? `— ${r.error_message ?? "pipeline failed"}`
                          : "— not started"}
                  </td>
                  <td className="px-6 py-3.5">
                    <StatusPill status={r.status} />
                  </td>
                  <td className="px-6 py-3.5">
                    {new Date(r.created_at).toLocaleString([], {
                      month: "short",
                      day: "numeric",
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                    <span className="block text-[11.5px] text-gray-400 mt-0.5">
                      {r.processing_seconds
                        ? `took ${formatDuration(r.processing_seconds)}`
                        : timeAgo(r.created_at)}
                    </span>
                  </td>
                  <td className="px-6 py-3.5 whitespace-nowrap">
                    <Link
                      href={`/admin/requests/${r.id}`}
                      className="text-pink font-bold text-xs hover:underline"
                    >
                      Inspect
                    </Link>
                    <button
                      onClick={() => onDelete(r.id, r.project_name)}
                      className="text-[#c22f4f] font-bold text-xs ml-3.5 hover:underline cursor-pointer"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="px-6 py-3.5 border-t border-[#f5f0f1] text-right">
          <Link href="/admin/requests" className="text-pink text-[13px] font-bold hover:underline">
            View all requests →
          </Link>
        </div>
      </div>
    </AdminShell>
  );
}
