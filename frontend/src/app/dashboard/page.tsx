"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import AppShell from "@/components/AppShell";
import Reveal from "@/components/Reveal";
import { Kicker, PinkButton, StatusPill, Spinner } from "@/components/ui";
import {
  listProjects,
  deleteProject,
  duplicateProject,
  formatDuration,
  timeAgo,
  type Project,
  type VideoStatus,
} from "@/lib/api";

const PAGE_SIZE = 9;
const FILTERS: ("All" | VideoStatus)[] = ["All", "Completed", "Processing", "Failed", "Idle"];

const THUMB_GRADIENTS = [
  "from-[#1c6b40] to-[#39a56b]",
  "from-pink to-[#f98fab]",
  "from-[#0e4f2b] to-[#17603a]",
];

export default function DashboardPage() {
  const router = useRouter();
  const [projects, setProjects] = useState<Project[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [filter, setFilter] = useState<"All" | VideoStatus>("All");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await listProjects({
        limit: PAGE_SIZE,
        offset: page * PAGE_SIZE,
        sort_by: "created_at",
        status: filter === "All" ? undefined : filter,
      });
      setProjects(res.data);
      setTotal(res.total);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load projects.");
    } finally {
      setLoading(false);
    }
  }, [page, filter]);

  useEffect(() => {
    load();
  }, [load]);

  const visible = useMemo(
    () =>
      search
        ? projects.filter((p) =>
            p.project_name.toLowerCase().includes(search.toLowerCase()),
          )
        : projects,
    [projects, search],
  );

  const stats = useMemo(() => {
    const completed = projects.filter((p) => p.status === "Completed").length;
    const processing = projects.filter(
      (p) => p.status === "Processing" || p.status === "Queued",
    ).length;
    const captions = projects.reduce((acc, p) => acc + p.scenes.length * 5, 0);
    return { completed, processing, captions };
  }, [projects]);

  async function onDelete(id: string, name: string) {
    if (!confirm(`Delete "${name}" and all its data? This cannot be undone.`)) return;
    setBusyId(id);
    try {
      await deleteProject(id);
      await load();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Delete failed.");
    } finally {
      setBusyId(null);
    }
  }

  async function onDuplicate(id: string) {
    setBusyId(id);
    try {
      await duplicateProject(id);
      await load();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Duplicate failed.");
    } finally {
      setBusyId(null);
    }
  }

  const pages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <AppShell>
      <div className="flex flex-wrap items-end justify-between gap-4 mb-7">
        <div>
          <Kicker>Your Workspace</Kicker>
          <h1 className="font-serif font-medium text-3xl mt-1">Project Dashboard</h1>
        </div>
        <PinkButton onClick={() => router.push("/upload")}>＋ New Upload</PinkButton>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-5 mb-7">
        {[
          { icon: "🎬", value: total, label: "Total Projects", pink: true },
          { icon: "✓", value: stats.completed, label: "Completed (this page)", pink: false },
          { icon: "⚙", value: stats.processing, label: "Processing Now", pink: true },
          { icon: "✍", value: stats.captions, label: "Captions (est.)", pink: false },
        ].map((s) => (
          <div
            key={s.label}
            className="bg-white p-5 pt-6 relative shadow-[0_10px_26px_rgba(203,86,120,0.1)]"
          >
            <div
              className={`absolute -top-4 -left-2.5 w-[46px] h-[46px] flex items-center justify-center text-[19px] text-white shadow-[0_8px_18px_rgba(242,84,125,0.35)] ${
                s.pink ? "bg-pink" : "bg-green"
              }`}
            >
              {s.icon}
            </div>
            <h3 className="font-serif text-3xl mt-2">{s.value}</h3>
            <span className="text-[12.5px] text-gray-400">{s.label}</span>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 items-center mb-6">
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="🔍 Search projects…"
          className="flex-1 min-w-[220px] px-4 py-3 border-[1.5px] border-[#f0dde2] rounded-md bg-white text-sm focus:outline-none focus:border-pink"
        />
        {FILTERS.map((f) => (
          <button
            key={f}
            onClick={() => {
              setFilter(f);
              setPage(0);
            }}
            className={`px-4.5 py-2.5 rounded-full text-[13px] border-[1.5px] transition-colors cursor-pointer ${
              filter === f
                ? "bg-green-d text-white border-green-d"
                : "bg-white text-gray-600 border-[#f0dde2] hover:border-pink"
            }`}
          >
            {f}
          </button>
        ))}
      </div>

      {/* Grid */}
      {loading ? (
        <div className="flex items-center justify-center py-24 gap-3 text-gray-500">
          <Spinner /> Loading projects…
        </div>
      ) : error ? (
        <div className="bg-[#fde2e6] text-[#c22f4f] rounded-md px-5 py-4 text-sm">
          ⚠ {error} — is the backend running at the configured API URL?
        </div>
      ) : visible.length === 0 ? (
        <div className="bg-white shadow-[0_12px_30px_rgba(203,86,120,0.1)] py-20 text-center">
          <div className="text-5xl mb-4">🎬</div>
          <h3 className="font-serif text-xl mb-2">No projects yet</h3>
          <p className="text-gray-400 text-sm mb-6">
            Upload your first video and let the AI write captions for it.
          </p>
          <PinkButton onClick={() => router.push("/upload")}>
            Upload Your First Video ➜
          </PinkButton>
        </div>
      ) : (
        <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-5">
          {visible.map((p, i) => (
            <Reveal key={p.id} delay={(i % 3) * 90}>
              <div className="lift bg-white shadow-[0_12px_30px_rgba(203,86,120,0.1)]">
                <Link href={`/projects/${p.id}`} className="block relative h-[150px] overflow-hidden">
                  <div
                    className={`absolute inset-0 bg-gradient-to-br ${THUMB_GRADIENTS[i % 3]}`}
                  />
                  <span className="absolute inset-0 flex items-center justify-center text-white/75 text-3xl">
                    ▶
                  </span>
                  <span className="absolute top-2.5 left-2.5">
                    <StatusPill status={p.status} />
                  </span>
                  {p.metadata && (
                    <span className="absolute right-2.5 bottom-2.5 bg-black/60 text-white text-[11px] px-2 py-0.5 rounded">
                      {formatDuration(p.metadata.duration_seconds)}
                    </span>
                  )}
                </Link>
                <div className="p-5">
                  <h3 className="font-serif text-[17px] mb-1.5 truncate">{p.project_name}</h3>
                  <div className="text-xs text-gray-400 mb-3.5">
                    {p.metadata
                      ? `${p.metadata.resolution} · ${Math.round(p.metadata.fps)}fps · ${p.metadata.format} · `
                      : ""}
                    {timeAgo(p.created_at)}
                    {p.scenes.length > 0 && ` · ${p.scenes.length} scenes`}
                  </div>
                  <div className="flex gap-2">
                    {p.status === "Completed" ? (
                      <Link
                        href={`/projects/${p.id}`}
                        className="flex-1 py-2.5 text-xs font-semibold text-center rounded bg-pink text-white hover:bg-pink-d transition-colors"
                      >
                        View Captions
                      </Link>
                    ) : p.status === "Processing" || p.status === "Queued" ? (
                      <Link
                        href={`/projects/${p.id}/processing`}
                        className="flex-1 py-2.5 text-xs font-semibold text-center rounded bg-pink text-white hover:bg-pink-d transition-colors"
                      >
                        View Progress
                      </Link>
                    ) : (
                      <Link
                        href={`/projects/${p.id}/processing?start=1`}
                        className="flex-1 py-2.5 text-xs font-semibold text-center rounded bg-pink text-white hover:bg-pink-d transition-colors"
                      >
                        {p.status === "Failed" ? "↻ Retry" : "▶ Start Processing"}
                      </Link>
                    )}
                    <button
                      onClick={() => onDuplicate(p.id)}
                      disabled={busyId === p.id}
                      title="Duplicate project"
                      className="px-3.5 py-2.5 text-xs rounded border-[1.5px] border-[#f0dde2] hover:border-pink transition-colors cursor-pointer disabled:opacity-50"
                    >
                      ⧉
                    </button>
                    <button
                      onClick={() => onDelete(p.id, p.project_name)}
                      disabled={busyId === p.id}
                      title="Delete project"
                      className="px-3.5 py-2.5 text-xs rounded border-[1.5px] border-[#f0dde2] hover:border-[#c22f4f] hover:text-[#c22f4f] transition-colors cursor-pointer disabled:opacity-50"
                    >
                      🗑
                    </button>
                  </div>
                </div>
              </div>
            </Reveal>
          ))}
        </div>
      )}

      {/* Pagination */}
      {!loading && !error && pages > 1 && (
        <div className="flex justify-center gap-2 mt-8">
          <button
            onClick={() => setPage((p) => Math.max(0, p - 1))}
            disabled={page === 0}
            className="w-9 h-9 rounded-md bg-white border-[1.5px] border-[#f0dde2] text-[13px] disabled:opacity-40 cursor-pointer"
          >
            ←
          </button>
          {Array.from({ length: pages }, (_, i) => (
            <button
              key={i}
              onClick={() => setPage(i)}
              className={`w-9 h-9 rounded-md text-[13px] border-[1.5px] cursor-pointer ${
                i === page
                  ? "bg-pink border-pink text-white"
                  : "bg-white border-[#f0dde2] text-gray-600"
              }`}
            >
              {i + 1}
            </button>
          ))}
          <button
            onClick={() => setPage((p) => Math.min(pages - 1, p + 1))}
            disabled={page === pages - 1}
            className="w-9 h-9 rounded-md bg-white border-[1.5px] border-[#f0dde2] text-[13px] disabled:opacity-40 cursor-pointer"
          >
            →
          </button>
        </div>
      )}
    </AppShell>
  );
}
