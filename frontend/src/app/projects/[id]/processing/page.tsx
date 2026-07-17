"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";
import AppShell from "@/components/AppShell";
import { Kicker, GhostButton, Spinner } from "@/components/ui";
import {
  getProject,
  getProjectProgress,
  getProjectStatus,
  processProject,
  type Project,
  type VideoStatus,
} from "@/lib/api";

const STAGES = [
  { key: "metadata", icon: "🎞", label: "Metadata" },
  { key: "scene", icon: "🎬", label: "Scene Detection" },
  { key: "keyframe", icon: "🖼", label: "Keyframes" },
  { key: "vision", icon: "👁", label: "Vision Analysis" },
  { key: "caption", icon: "✍", label: "Caption Writing" },
];

function stageIndex(stage: string | null | undefined, percent: number): number {
  if (stage) {
    const s = stage.toLowerCase();
    const idx = STAGES.findIndex((st) => s.includes(st.key));
    if (idx >= 0) return idx;
  }
  return Math.min(STAGES.length - 1, Math.floor((percent / 100) * STAGES.length));
}

export default function ProcessingPage() {
  const { id } = useParams<{ id: string }>();
  const search = useSearchParams();
  const shouldStart = search.get("start") === "1";

  const [project, setProject] = useState<Project | null>(null);
  const [status, setStatus] = useState<VideoStatus>("Idle");
  const [percent, setPercent] = useState(0);
  const [stage, setStage] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [log, setLog] = useState<{ time: string; text: string; done: boolean }[]>([]);
  const startedRef = useRef(false);
  const lastStageRef = useRef<string | null>(null);

  const pushLog = useCallback((text: string, done: boolean) => {
    const time = new Date().toLocaleTimeString([], { hour12: false });
    setLog((l) => [...l.map((e) => ({ ...e, done: true })), { time, text, done }]);
  }, []);

  // Initial fetch + kick off processing if requested
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const p = await getProject(id);
        if (cancelled) return;
        setProject(p);
        setStatus(p.status);
        if (
          shouldStart &&
          !startedRef.current &&
          p.status !== "Processing" &&
          p.status !== "Completed"
        ) {
          startedRef.current = true;
          pushLog("Processing started — the AI pipeline is warming up…", false);
          setStatus("Processing");
          // Synchronous on the backend: resolves when the pipeline finishes.
          processProject(id)
            .then((res) => {
              setStatus(res.status);
              pushLog(res.message, true);
            })
            .catch((e) => {
              setStatus("Failed");
              setErrorMsg(e instanceof Error ? e.message : "Processing failed.");
            });
        }
      } catch (e) {
        setErrorMsg(e instanceof Error ? e.message : "Could not load project.");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [id, shouldStart, pushLog]);

  // Poll progress while processing
  useEffect(() => {
    if (status !== "Processing" && status !== "Queued") return;
    const t = setInterval(async () => {
      try {
        const [prog, st] = await Promise.all([
          getProjectProgress(id),
          getProjectStatus(id),
        ]);
        setPercent(prog.progress_percent);
        setStage(prog.current_stage ?? null);
        setStatus(st.status);
        if (st.error_message) setErrorMsg(st.error_message);
        if (prog.current_stage && prog.current_stage !== lastStageRef.current) {
          lastStageRef.current = prog.current_stage;
          pushLog(`Stage: ${prog.current_stage} — ${Math.round(prog.progress_percent)}%`, false);
        }
      } catch {
        /* transient poll errors are fine */
      }
    }, 2000);
    return () => clearInterval(t);
  }, [status, id, pushLog]);

  const activeStage = stageIndex(stage, percent);
  const displayPercent = status === "Completed" ? 100 : Math.round(percent);

  return (
    <AppShell>
      <div className="text-center max-w-[900px] mx-auto">
        <Kicker>{status === "Completed" ? "Completed" : "Processing"}</Kicker>
        <h1 className="font-serif font-medium text-3xl mt-1">
          {project?.project_name ?? "Loading…"}
        </h1>
        <p className="text-gray-400 text-sm mt-2 mb-9">
          {status === "Completed"
            ? "All scenes captioned. Your results are ready."
            : status === "Failed"
              ? "The pipeline hit an error — details below."
              : "The AI pipeline is working through your video, scene by scene."}
        </p>

        {/* Progress ring */}
        <div className="relative w-[230px] h-[230px] mx-auto mb-9">
          {(status === "Processing" || status === "Queued") && (
            <div className="absolute -inset-3.5 rounded-full border-2 border-dashed border-pink/35 anim-spin-slow" />
          )}
          <div
            className="w-[230px] h-[230px] rounded-full flex items-center justify-center transition-all duration-700"
            style={{
              background: `conic-gradient(${
                status === "Failed" ? "#c22f4f" : "var(--pink)"
              } 0 ${displayPercent}%, #f4dde3 ${displayPercent}% 100%)`,
            }}
          >
            <div className="w-[180px] h-[180px] rounded-full bg-white flex flex-col items-center justify-center shadow-[inset_0_0_0_1px_#fbe9ed]">
              <b className="font-serif text-[44px] text-green-d">
                {status === "Completed" ? "✓" : `${displayPercent}%`}
              </b>
              <span className="text-xs text-gray-400 tracking-wider uppercase px-4 text-center">
                {status === "Completed"
                  ? "Done"
                  : status === "Failed"
                    ? "Failed"
                    : (stage ?? "Working…")}
              </span>
            </div>
          </div>
        </div>

        {/* Stage tracker */}
        <div className="flex justify-center max-w-[860px] mx-auto mb-10">
          {STAGES.map((s, i) => {
            const done = status === "Completed" || i < activeStage;
            const now =
              status !== "Completed" && status !== "Failed" && i === activeStage;
            return (
              <div key={s.key} className="flex-1 relative pt-2">
                {i > 0 && (
                  <div
                    className={`absolute top-[29px] -left-1/2 w-full h-[3px] ${
                      done || now ? "bg-pink" : "bg-[#f0d7dd]"
                    }`}
                  />
                )}
                <div
                  className={`w-11 h-11 rounded-full mx-auto flex items-center justify-center text-[17px] relative z-10 transition-all ${
                    done
                      ? "bg-green border-[3px] border-green text-white"
                      : now
                        ? "bg-pink border-[3px] border-pink text-white shadow-[0_0_0_8px_rgba(242,84,125,0.18)]"
                        : "bg-white border-[3px] border-[#f0d7dd]"
                  }`}
                >
                  {done ? "✓" : s.icon}
                </div>
                <p
                  className={`text-[12.5px] mt-3 font-semibold ${
                    now ? "text-pink" : "text-gray-500"
                  }`}
                >
                  {s.label}
                </p>
              </div>
            );
          })}
        </div>

        {/* Live log */}
        <div className="max-w-[760px] mx-auto bg-white text-left shadow-[0_14px_34px_rgba(203,86,120,0.12)]">
          <div className="bg-green-d text-white px-6 py-4 flex justify-between items-center">
            <b className="font-serif text-base">Live Pipeline Log</b>
            <span
              className={`text-[11.5px] font-bold px-3.5 py-1 rounded-full ${
                status === "Completed"
                  ? "bg-[#e6f7ec] text-green"
                  : status === "Failed"
                    ? "bg-[#fde2e6] text-[#c22f4f]"
                    : "bg-[#fff3cd] text-[#8a6d00]"
              }`}
            >
              ● {status}
            </span>
          </div>
          <div className="px-6 py-3 max-h-[240px] overflow-y-auto">
            {log.length === 0 && (
              <div className="py-4 text-[13.5px] text-gray-400 flex items-center gap-2">
                {status === "Processing" || status === "Queued" ? (
                  <>
                    <Spinner /> Waiting for pipeline events…
                  </>
                ) : status === "Completed" ? (
                  "✓ This project completed processing."
                ) : status === "Failed" ? (
                  "✗ This project failed during processing."
                ) : (
                  "This project has not been processed yet."
                )}
              </div>
            )}
            {log.map((entry, i) => (
              <div
                key={i}
                className="flex gap-3.5 py-2.5 border-b border-[#faf0f2] last:border-0 text-[13.5px] text-gray-600 items-center"
              >
                <span className="text-gray-300 text-xs w-16 flex-shrink-0">{entry.time}</span>
                <span className={entry.done ? "text-green font-bold" : "text-pink font-bold"}>
                  {entry.done ? "✓" : "⟳"}
                </span>
                {entry.text}
              </div>
            ))}
            {errorMsg && (
              <div className="flex gap-3.5 py-2.5 text-[13.5px] text-[#c22f4f] items-center">
                <span className="w-16 flex-shrink-0" />✗ {errorMsg}
              </div>
            )}
          </div>
        </div>

        <div className="flex gap-3.5 justify-center mt-6">
          <Link href="/dashboard">
            <GhostButton>← Back to Dashboard</GhostButton>
          </Link>
          <Link
            href={`/projects/${id}`}
            className={`bg-pink hover:bg-pink-d text-white font-bold rounded-md px-6 py-3 text-sm shadow-[0_8px_20px_rgba(242,84,125,0.35)] transition-colors ${
              status === "Completed" ? "" : "opacity-60"
            }`}
          >
            {status === "Completed" ? "View Results ➜" : "View Partial Results ➜"}
          </Link>
        </div>
      </div>
    </AppShell>
  );
}
