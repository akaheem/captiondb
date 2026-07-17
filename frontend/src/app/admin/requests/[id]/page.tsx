"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import AdminShell from "@/components/AdminShell";
import { Kicker, Spinner, StatusPill } from "@/components/ui";
import {
  adminRequestDetail,
  formatBytes,
  formatDuration,
  TONE_LABELS,
  type AdminRequestDetail,
  type CaptionTone,
} from "@/lib/api";

export default function AdminInspectorPage() {
  const { id } = useParams<{ id: string }>();
  const [data, setData] = useState<AdminRequestDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [toneFilter, setToneFilter] = useState<"all" | CaptionTone>("all");

  useEffect(() => {
    adminRequestDetail(id)
      .then(setData)
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load request."));
  }, [id]);

  const allTones = useMemo(() => {
    const set = new Set<CaptionTone>();
    data?.scenes.forEach((s) =>
      Object.keys(s.captions).forEach((t) => set.add(t as CaptionTone)),
    );
    return [...set];
  }, [data]);

  if (error) {
    return (
      <AdminShell>
        <div className="bg-[#fde2e6] text-[#c22f4f] rounded-md px-5 py-4 text-sm">
          ⚠ {error}{" "}
          <Link href="/admin/requests" className="underline font-bold">
            Back to requests
          </Link>
        </div>
      </AdminShell>
    );
  }

  if (!data) {
    return (
      <AdminShell>
        <div className="flex items-center justify-center py-32 gap-3 text-gray-500">
          <Spinner /> Loading request…
        </div>
      </AdminShell>
    );
  }

  const r = data.request;
  const totalCaptions = data.scenes.reduce(
    (acc, s) => acc + Object.keys(s.captions).length,
    0,
  );

  return (
    <AdminShell>
      <Kicker>Admin · Request Inspector</Kicker>
      <h1 className="font-serif font-medium text-[26px] mt-1 mb-6">
        Request #{r.id.slice(0, 8)} — {r.project_name}
      </h1>

      <div className="flex flex-col xl:flex-row gap-5 items-start">
        {/* Left: data provided */}
        <div className="w-full xl:w-[400px] flex-shrink-0 bg-white shadow-[0_8px_22px_rgba(0,0,0,0.05)]">
          <div className="bg-green-d text-white px-6 py-5">
            <b className="font-serif text-lg">Data Provided</b>
            <span className="block text-xs opacity-80 mt-1">What the user submitted</span>
          </div>
          <div className="p-6 border-b border-[#f5f0f1]">
            <div className="h-[140px] rounded-md bg-gradient-to-br from-[#1c6b40] to-[#39a56b] flex items-center justify-center text-white text-3xl relative">
              ▶
              {r.metadata && (
                <span className="absolute right-2.5 bottom-2 bg-black/60 text-xs px-2 py-0.5 rounded">
                  {formatDuration(r.metadata.duration_seconds)}
                </span>
              )}
            </div>
          </div>
          <div className="px-6 py-4.5 border-b border-[#f5f0f1]">
            <h4 className="text-[11px] tracking-[2px] text-pink font-bold mb-3">UPLOADED FILE</h4>
            {[
              ["Filename", r.original_filename],
              ["Size", r.metadata ? formatBytes(r.metadata.size_bytes) : "—"],
              [
                "Format / Codec",
                r.metadata ? `${r.metadata.format} · ${r.metadata.codec}` : "—",
              ],
              [
                "Resolution",
                r.metadata
                  ? `${r.metadata.resolution} · ${r.metadata.fps.toFixed(2)} fps`
                  : "—",
              ],
              [
                "Duration",
                r.metadata ? formatDuration(r.metadata.duration_seconds) : "—",
              ],
            ].map(([k, v]) => (
              <div key={k} className="flex justify-between py-1.5 text-[13px] text-gray-600">
                <span>{k}</span>
                <b className="text-gray-900 text-right ml-4 truncate max-w-[220px]">{v}</b>
              </div>
            ))}
          </div>
          <div className="px-6 py-4.5 border-b border-[#f5f0f1]">
            <h4 className="text-[11px] tracking-[2px] text-pink font-bold mb-3">REQUEST INFO</h4>
            <div className="flex justify-between py-1.5 text-[13px] text-gray-600">
              <span>Project name</span>
              <b className="text-gray-900">{r.project_name}</b>
            </div>
            <div className="flex justify-between py-1.5 text-[13px] text-gray-600">
              <span>Received</span>
              <b className="text-gray-900">{new Date(r.created_at).toLocaleString()}</b>
            </div>
            <div className="flex justify-between py-1.5 text-[13px] text-gray-600 items-center">
              <span>Status</span>
              <StatusPill status={r.status} />
            </div>
            <div className="flex justify-between py-1.5 text-[13px] text-gray-600">
              <span>Processing time</span>
              <b className="text-gray-900">
                {r.processing_seconds ? formatDuration(r.processing_seconds) : "—"}
              </b>
            </div>
            {r.error_message && (
              <div className="mt-2 bg-[#fde2e6] text-[#c22f4f] text-xs rounded px-3 py-2">
                ✗ {r.error_message}
              </div>
            )}
          </div>
          <div className="px-6 py-4.5">
            <h4 className="text-[11px] tracking-[2px] text-pink font-bold mb-3">
              PIPELINE TIMELINE
            </h4>
            {[
              r.started_at && {
                t: new Date(r.started_at).toLocaleTimeString([], { hour12: false }),
                text: "Processing started",
              },
              r.scenes_count > 0 && {
                t: "",
                text: `${r.scenes_count} scenes detected`,
              },
              totalCaptions > 0 && {
                t: "",
                text: `${totalCaptions} captions written`,
              },
              r.completed_at && {
                t: new Date(r.completed_at).toLocaleTimeString([], { hour12: false }),
                text: "Pipeline completed",
              },
            ]
              .filter(Boolean)
              .map((row, i) => {
                const item = row as { t: string; text: string };
                return (
                  <div key={i} className="flex gap-3 py-1.5 text-[12.5px] text-gray-600 items-baseline">
                    <span className="text-gray-300 text-[11px] w-14 flex-shrink-0">{item.t}</span>
                    <span className="text-green font-bold">✓</span>
                    {item.text}
                  </div>
                );
              })}
            {!r.started_at && (
              <div className="text-[12.5px] text-gray-400 py-1.5">Not processed yet.</div>
            )}
          </div>
        </div>

        {/* Right: results generated */}
        <div className="flex-1 w-full bg-white shadow-[0_8px_22px_rgba(0,0,0,0.05)]">
          <div className="px-6 py-4.5 flex flex-wrap justify-between items-center gap-3 border-b border-[#f5f0f1]">
            <b className="font-serif text-[17px]">
              Results Generated — {totalCaptions} captions
            </b>
            <div className="flex gap-1.5 flex-wrap">
              <button
                onClick={() => setToneFilter("all")}
                className={`px-4 py-2 rounded-full text-[12.5px] font-semibold transition-colors cursor-pointer ${
                  toneFilter === "all" ? "bg-pink text-white" : "text-gray-500 hover:text-pink"
                }`}
              >
                All Tones
              </button>
              {allTones.map((t) => (
                <button
                  key={t}
                  onClick={() => setToneFilter(t)}
                  className={`px-4 py-2 rounded-full text-[12.5px] font-semibold transition-colors cursor-pointer ${
                    toneFilter === t ? "bg-pink text-white" : "text-gray-500 hover:text-pink"
                  }`}
                >
                  {TONE_LABELS[t]?.label ?? t}
                </button>
              ))}
            </div>
          </div>
          {data.scenes.length === 0 && (
            <div className="px-6 py-14 text-center text-gray-400 text-sm">
              No scenes generated for this request yet.
            </div>
          )}
          {data.scenes.map((s, i) => {
            const entries = (
              Object.entries(s.captions) as [CaptionTone, string][]
            ).filter(([t]) => toneFilter === "all" || t === toneFilter);
            return (
              <div key={s.scene_id} className="px-6 py-4.5 border-b border-[#f5f0f1] last:border-0">
                <div className="flex gap-3.5 items-center mb-3 flex-wrap">
                  <div className="w-20 h-[52px] rounded bg-gradient-to-br from-[#1c6b40] to-[#39a56b] flex items-center justify-center text-white flex-shrink-0">
                    ▶
                  </div>
                  <div>
                    <b className="font-serif text-[15px]">{s.title ?? `Scene ${i + 1}`}</b>
                    <span className="block text-[11.5px] text-gray-400 mt-0.5">
                      {formatDuration(s.seconds_start)} – {formatDuration(s.seconds_end)}
                    </span>
                  </div>
                  <div className="ml-auto flex gap-1.5 flex-wrap">
                    {s.tags.slice(0, 4).map((t) => (
                      <span
                        key={t}
                        className="bg-blush text-[#c22553] text-[10.5px] font-bold px-2.5 py-1 rounded-full"
                      >
                        {t}
                      </span>
                    ))}
                  </div>
                </div>
                {s.summary && (
                  <p className="text-[12.5px] text-gray-500 mb-2.5 italic">{s.summary}</p>
                )}
                {entries.length === 0 ? (
                  <div className="text-[12.5px] text-gray-400">
                    No captions {toneFilter !== "all" ? `for tone "${toneFilter}"` : ""} in this
                    scene.
                  </div>
                ) : (
                  entries.map(([tone, text]) => (
                    <div
                      key={tone}
                      className={`bg-[#fbf6f7] border-l-[3px] px-4 py-3 rounded mb-2 text-[13.5px] text-gray-700 font-serif leading-relaxed ${
                        tone === "formal" ? "border-green" : "border-pink"
                      }`}
                    >
                      <span
                        className={`block font-sans text-[10px] tracking-[2px] font-bold mb-1 ${
                          tone === "formal" ? "text-green" : "text-pink"
                        }`}
                      >
                        {(TONE_LABELS[tone]?.label ?? tone).toUpperCase()}
                      </span>
                      &quot;{text}&quot;
                    </div>
                  ))
                )}
              </div>
            );
          })}
        </div>
      </div>
    </AdminShell>
  );
}
