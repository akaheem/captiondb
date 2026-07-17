"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import AdminShell from "@/components/AdminShell";
import { Kicker, Spinner, StatusPill } from "@/components/ui";
import {
  adminListRequests,
  adminDeleteRequest,
  formatBytes,
  formatDuration,
  timeAgo,
  type AdminRequestItem,
  type VideoStatus,
} from "@/lib/api";

const PAGE_SIZE = 20;
const FILTERS: ("All" | VideoStatus)[] = ["All", "Completed", "Processing", "Failed", "Idle"];

export default function AdminRequestsPage() {
  const [rows, setRows] = useState<AdminRequestItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [filter, setFilter] = useState<"All" | VideoStatus>("All");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await adminListRequests({
        limit: PAGE_SIZE,
        offset: page * PAGE_SIZE,
        status: filter === "All" ? undefined : filter,
      });
      setRows(res.data);
      setTotal(res.total);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load requests.");
    } finally {
      setLoading(false);
    }
  }, [page, filter]);

  useEffect(() => {
    load();
  }, [load]);

  async function onDelete(id: string, name: string) {
    if (!confirm(`Delete request "${name}" and all its data?`)) return;
    try {
      await adminDeleteRequest(id);
      await load();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Delete failed.");
    }
  }

  const pages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <AdminShell>
      <Kicker>Admin · Requests</Kicker>
      <h1 className="font-serif font-medium text-[26px] mt-1 mb-6">
        All Requests <span className="text-gray-400 text-lg">({total})</span>
      </h1>

      <div className="flex gap-2.5 mb-5 flex-wrap">
        {FILTERS.map((f) => (
          <button
            key={f}
            onClick={() => {
              setFilter(f);
              setPage(0);
            }}
            className={`px-4.5 py-2.5 rounded-full text-[13px] border transition-colors cursor-pointer ${
              filter === f
                ? "bg-green-d text-white border-green-d"
                : "bg-white text-gray-600 border-gray-200 hover:border-pink"
            }`}
          >
            {f}
          </button>
        ))}
      </div>

      {error ? (
        <div className="bg-[#fde2e6] text-[#c22f4f] rounded-md px-5 py-4 text-sm">⚠ {error}</div>
      ) : loading ? (
        <div className="flex items-center justify-center py-24 gap-3 text-gray-500">
          <Spinner /> Loading requests…
        </div>
      ) : (
        <div className="bg-white shadow-[0_8px_22px_rgba(0,0,0,0.05)] overflow-x-auto">
          <table className="w-full text-[13px] min-w-[900px]">
            <thead>
              <tr className="text-left text-gray-400 text-[11px] tracking-[1.5px]">
                <th className="px-6 py-3.5 border-b border-[#f5f0f1]">REQUEST / PROJECT</th>
                <th className="px-6 py-3.5 border-b border-[#f5f0f1]">DATA PROVIDED</th>
                <th className="px-6 py-3.5 border-b border-[#f5f0f1]">RESULTS GENERATED</th>
                <th className="px-6 py-3.5 border-b border-[#f5f0f1]">STATUS</th>
                <th className="px-6 py-3.5 border-b border-[#f5f0f1]">RECEIVED</th>
                <th className="px-6 py-3.5 border-b border-[#f5f0f1]">ACTIONS</th>
              </tr>
            </thead>
            <tbody>
              {rows.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-6 py-10 text-center text-gray-400">
                    No requests found.
                  </td>
                </tr>
              )}
              {rows.map((r) => (
                <tr key={r.id} className="border-b border-[#faf5f6] last:border-0 hover:bg-[#fdfafa]">
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
      )}

      {!loading && pages > 1 && (
        <div className="flex justify-center gap-2 mt-6">
          {Array.from({ length: pages }, (_, i) => (
            <button
              key={i}
              onClick={() => setPage(i)}
              className={`w-9 h-9 rounded-md text-[13px] border cursor-pointer ${
                i === page
                  ? "bg-pink border-pink text-white"
                  : "bg-white border-gray-200 text-gray-600"
              }`}
            >
              {i + 1}
            </button>
          ))}
        </div>
      )}
    </AdminShell>
  );
}
