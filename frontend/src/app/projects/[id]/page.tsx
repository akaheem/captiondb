"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import AppShell from "@/components/AppShell";
import { Kicker, StatusPill, Spinner, GhostButton } from "@/components/ui";
import {
  getProject,
  getProjectCaptions,
  getProjectSummary,
  duplicateProject,
  formatDuration,
  TONE_LABELS,
  type Project,
  type SceneCaptions,
  type ProjectSummary,
  type CaptionTone,
} from "@/lib/api";

export default function ProjectResultsPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();

  const [project, setProject] = useState<Project | null>(null);
  const [captions, setCaptions] = useState<SceneCaptions[]>([]);
  const [summary, setSummary] = useState<ProjectSummary | null>(null);
  const [selectedScene, setSelectedScene] = useState(0);
  const [selectedTone, setSelectedTone] = useState<CaptionTone | null>(null);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [p, caps, sum] = await Promise.all([
          getProject(id),
          getProjectCaptions(id).catch(() => ({ data: [], total: 0 })),
          getProjectSummary(id).catch(() => null),
        ]);
        if (cancelled) return;
        setProject(p);
        setCaptions(caps.data);
        setSummary(sum);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "Failed to load project.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [id]);

  const scenes = project?.scenes ?? [];
  const scene = scenes[selectedScene];
  const sceneCaps = useMemo(
    () => captions.find((c) => c.scene_id === scene?.scene_id)?.captions ?? {},
    [captions, scene],
  );
  const tones = Object.keys(sceneCaps) as CaptionTone[];
  const activeTone = selectedTone && tones.includes(selectedTone) ? selectedTone : tones[0];
  const totalDuration = project?.metadata?.duration_seconds ?? 0;

  async function copyCaption() {
    if (!activeTone || !sceneCaps[activeTone]) return;
    await navigator.clipboard.writeText(sceneCaps[activeTone]!);
    setCopied(true);
    setTimeout(() => setCopied(false), 1600);
  }

  async function onDuplicate() {
    try {
      const copy = await duplicateProject(id);
      router.push(`/projects/${copy.id}`);
    } catch (e) {
      alert(e instanceof Error ? e.message : "Duplicate failed.");
    }
  }

  function exportCaptions() {
    const payload = {
      project: project?.project_name,
      exported_at: new Date().toISOString(),
      scenes: scenes.map((s) => ({
        scene: s.title ?? s.scene_id,
        start: s.seconds_start,
        end: s.seconds_end,
        tags: s.tags,
        summary: s.summary,
        captions: captions.find((c) => c.scene_id === s.scene_id)?.captions ?? {},
      })),
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${(project?.project_name ?? "captions").replace(/\s+/g, "_")}_captions.json`;
    a.click();
    URL.revokeObjectURL(url);
  }

  if (loading) {
    return (
      <AppShell>
        <div className="flex items-center justify-center py-32 gap-3 text-gray-500">
          <Spinner /> Loading project…
        </div>
      </AppShell>
    );
  }

  if (error || !project) {
    return (
      <AppShell>
        <div className="bg-[#fde2e6] text-[#c22f4f] rounded-md px-5 py-4 text-sm">
          ⚠ {error ?? "Project not found."}{" "}
          <Link href="/dashboard" className="underline font-bold">
            Back to dashboard
          </Link>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      {/* Header */}
      <div className="flex flex-wrap items-end justify-between gap-4 mb-6">
        <div>
          <Kicker>Project Results</Kicker>
          <h1 className="font-serif font-medium text-[28px] mt-1 flex items-center gap-3 flex-wrap">
            {project.project_name}
            <StatusPill status={project.status} />
          </h1>
        </div>
        <div className="flex gap-2.5">
          <GhostButton onClick={onDuplicate}>⧉ Duplicate</GhostButton>
          <button
            onClick={exportCaptions}
            className="bg-pink hover:bg-pink-d text-white font-bold rounded-md px-5 py-3 text-sm shadow-[0_8px_18px_rgba(242,84,125,0.3)] transition-colors cursor-pointer"
          >
            ⬇ Export Captions
          </button>
        </div>
      </div>

      {/* Summary strip */}
      {summary && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          {[
            { icon: "🎬", v: summary.total_scenes, l: "Total Scenes", pink: true },
            { icon: "✓", v: summary.successful_scenes, l: "Successful", pink: false },
            { icon: "✍", v: summary.total_captions, l: "Captions", pink: true },
            {
              icon: "⏱",
              v: summary.processing_duration_seconds
                ? `${Math.floor(summary.processing_duration_seconds / 60)}m ${Math.round(summary.processing_duration_seconds % 60)}s`
                : "—",
              l: "Processing Time",
              pink: false,
            },
          ].map((s) => (
            <div
              key={s.l}
              className="bg-white px-5 py-4 pt-5 relative shadow-[0_10px_24px_rgba(203,86,120,0.08)]"
            >
              <div
                className={`absolute -top-3 -left-2 w-[38px] h-[38px] flex items-center justify-center text-[15px] text-white ${
                  s.pink ? "bg-pink" : "bg-green"
                }`}
              >
                {s.icon}
              </div>
              <b className="block font-serif text-[22px] mt-2">{s.v}</b>
              <span className="text-[11.5px] text-gray-400">{s.l}</span>
            </div>
          ))}
        </div>
      )}

      {/* Timeline */}
      {scenes.length > 0 && totalDuration > 0 && (
        <div className="bg-white px-5 py-4 shadow-[0_10px_24px_rgba(203,86,120,0.08)] mb-6">
          <h3 className="font-serif text-[15px] mb-3">
            Scene Timeline — {formatDuration(totalDuration)}
          </h3>
          <div className="flex h-[52px] rounded-md overflow-hidden gap-[3px]">
            {scenes.map((s, i) => (
              <button
                key={s.scene_id}
                onClick={() => setSelectedScene(i)}
                style={{
                  flexGrow: Math.max(1, s.seconds_end - s.seconds_start),
                }}
                className={`relative transition-all cursor-pointer ${
                  i % 3 === 2
                    ? "bg-gradient-to-br from-[#0e4f2b] to-[#17603a]"
                    : "bg-gradient-to-br from-[#1c6b40] to-[#39a56b]"
                } ${i === selectedScene ? "outline-[3px] outline outline-pink -outline-offset-[3px] opacity-100" : "opacity-85 hover:opacity-100"}`}
              >
                <span className="absolute bottom-1 left-1.5 text-white text-[10px]">
                  {formatDuration(s.seconds_start)}
                </span>
              </button>
            ))}
          </div>
        </div>
      )}

      {scenes.length === 0 ? (
        <div className="bg-white py-16 text-center shadow-[0_12px_30px_rgba(203,86,120,0.1)]">
          <div className="text-5xl mb-4">🎞</div>
          <h3 className="font-serif text-xl mb-2">No scenes yet</h3>
          <p className="text-gray-400 text-sm mb-6">
            This project hasn&apos;t been processed. Run the AI pipeline to detect
            scenes and generate captions.
          </p>
          <Link
            href={`/projects/${id}/processing?start=1`}
            className="inline-block bg-pink hover:bg-pink-d text-white font-bold text-sm rounded px-7 py-3.5 transition-colors"
          >
            ▶ Start Processing
          </Link>
        </div>
      ) : (
        <div className="flex flex-col lg:flex-row gap-5 items-start">
          {/* Scene list */}
          <div className="w-full lg:w-[290px] flex-shrink-0 max-h-[560px] overflow-y-auto pr-1">
            {scenes.map((s, i) => (
              <button
                key={s.scene_id}
                onClick={() => setSelectedScene(i)}
                className={`w-full text-left bg-white p-3.5 mb-3 flex gap-3 shadow-[0_8px_20px_rgba(203,86,120,0.07)] cursor-pointer transition-all ${
                  i === selectedScene ? "border-l-4 border-pink" : "hover:translate-x-1"
                }`}
              >
                <div
                  className={`w-[76px] h-[50px] rounded flex-shrink-0 flex items-center justify-center text-white text-[13px] ${
                    i === selectedScene
                      ? "bg-gradient-to-br from-pink to-[#f98fab]"
                      : "bg-gradient-to-br from-[#1c6b40] to-[#39a56b]"
                  }`}
                >
                  ▶
                </div>
                <div className="min-w-0">
                  <b className="text-[13px] font-serif block truncate">
                    {s.title ?? `Scene ${i + 1}`}
                  </b>
                  <span className="block text-[11px] text-gray-400 mt-1 truncate">
                    {formatDuration(s.seconds_start)} – {formatDuration(s.seconds_end)}
                    {s.tags.length > 0 && ` · ${s.tags.slice(0, 2).join(", ")}`}
                  </span>
                </div>
              </button>
            ))}
          </div>

          {/* Detail */}
          {scene && (
            <div className="flex-1 w-full bg-white shadow-[0_12px_30px_rgba(203,86,120,0.1)]">
              <div className="bg-green-d text-white px-6 py-5">
                <b className="font-serif text-[19px]">
                  {scene.title ?? `Scene ${selectedScene + 1}`}
                </b>
                <span className="block text-[12.5px] opacity-80 mt-1">
                  {formatDuration(scene.seconds_start)} – {formatDuration(scene.seconds_end)} ·{" "}
                  {Math.round(scene.seconds_end - scene.seconds_start)} seconds
                </span>
              </div>
              <div className="p-6">
                {/* Tags */}
                {scene.tags.length > 0 && (
                  <div className="flex gap-2 flex-wrap mb-5">
                    {scene.tags.map((t, i) => (
                      <span
                        key={t}
                        className={`text-[11.5px] font-bold px-3 py-1.5 rounded-full ${
                          i % 2 === 0
                            ? "bg-[#e6f7ec] text-green"
                            : "bg-blush text-[#c22553]"
                        }`}
                      >
                        {t}
                      </span>
                    ))}
                  </div>
                )}

                {/* Tone tabs */}
                {tones.length > 0 ? (
                  <>
                    <div className="flex gap-1.5 border-b-2 border-[#f7e8ec] mb-4.5 flex-wrap">
                      {tones.map((t) => (
                        <button
                          key={t}
                          onClick={() => setSelectedTone(t)}
                          className={`px-4 py-2.5 text-[13px] font-semibold -mb-0.5 border-b-[3px] transition-colors cursor-pointer ${
                            t === activeTone
                              ? "text-pink border-pink"
                              : "text-gray-400 border-transparent hover:text-gray-600"
                          }`}
                        >
                          {TONE_LABELS[t]?.emoji} {TONE_LABELS[t]?.label ?? t}
                        </button>
                      ))}
                    </div>
                    <div className="flex justify-between items-center mb-2.5">
                      <span className="text-pink tracking-[2px] text-[11px] font-bold uppercase">
                        {TONE_LABELS[activeTone!]?.label ?? activeTone} · Scene {selectedScene + 1}
                      </span>
                      <button
                        onClick={copyCaption}
                        className="bg-white border-[1.5px] border-[#f0dde2] hover:border-pink rounded px-3.5 py-1.5 text-xs font-semibold text-gray-600 transition-colors cursor-pointer"
                      >
                        {copied ? "✓ Copied!" : "⧉ Copy"}
                      </button>
                    </div>
                    <div className="bg-blush border-l-4 border-pink px-5 py-4 rounded-md text-[15px] leading-7 text-gray-800 font-serif">
                      &quot;{sceneCaps[activeTone!]}&quot;
                    </div>
                  </>
                ) : (
                  <div className="text-gray-400 text-sm py-4">
                    No captions were generated for this scene.
                  </div>
                )}

                {/* AI summary */}
                {scene.summary && (
                  <div className="mt-5 text-[13.5px] text-gray-500 leading-[1.75]">
                    <b className="font-serif text-gray-800 text-[14.5px] block mb-1.5">
                      AI Scene Summary
                    </b>
                    {scene.summary}
                  </div>
                )}
                {scene.transcript && (
                  <div className="mt-4 text-[13.5px] text-gray-500 leading-[1.75]">
                    <b className="font-serif text-gray-800 text-[14.5px] block mb-1.5">
                      Transcript
                    </b>
                    {scene.transcript}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </AppShell>
  );
}
