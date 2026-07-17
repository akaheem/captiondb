"use client";

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import AppShell from "@/components/AppShell";
import { Kicker, PinkButton } from "@/components/ui";
import {
  uploadVideo,
  formatBytes,
  formatDuration,
  type UploadResponse,
} from "@/lib/api";

const ACCEPTED = [".mp4", ".mov", ".avi", ".webm"];
const MAX_MB = 500;

export default function UploadPage() {
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [projectName, setProjectName] = useState("");
  const [dragOver, setDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<UploadResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  function pickFile(f: File | null) {
    setError(null);
    setResult(null);
    if (!f) return;
    const ext = `.${f.name.split(".").pop()?.toLowerCase()}`;
    if (!ACCEPTED.includes(ext)) {
      setError(`Unsupported format "${ext}". Use MP4, MOV, AVI or WebM.`);
      return;
    }
    if (f.size > MAX_MB * 1024 * 1024) {
      setError(`File is ${formatBytes(f.size)} — the limit is ${MAX_MB} MB.`);
      return;
    }
    setFile(f);
    if (!projectName) {
      setProjectName(f.name.replace(/\.[^.]+$/, "").replace(/[_-]+/g, " "));
    }
  }

  async function onUpload() {
    if (!file || !projectName.trim()) {
      setError("Choose a video and give the project a name.");
      return;
    }
    setUploading(true);
    setError(null);
    try {
      const res = await uploadVideo(projectName.trim(), file);
      setResult(res);
      if (!res.success) {
        setError(res.errors?.join(", ") ?? "Upload failed.");
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed.");
    } finally {
      setUploading(false);
    }
  }

  return (
    <AppShell>
      <Kicker>New Project</Kicker>
      <h1 className="font-serif font-medium text-3xl mt-1 mb-8">Upload a Video</h1>

      <div className="flex flex-col xl:flex-row gap-7 items-start">
        {/* Dropzone */}
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setDragOver(true);
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragOver(false);
            pickFile(e.dataTransfer.files[0] ?? null);
          }}
          onClick={() => inputRef.current?.click()}
          className={`flex-[1.3] w-full bg-white border-[2.5px] border-dashed rounded-xl min-h-[420px] flex flex-col items-center justify-center text-center p-10 cursor-pointer transition-colors shadow-[0_14px_34px_rgba(203,86,120,0.1)] ${
            dragOver ? "border-pink bg-blush" : "border-[#f2a8bd]"
          }`}
        >
          <input
            ref={inputRef}
            type="file"
            accept={ACCEPTED.join(",")}
            className="hidden"
            onChange={(e) => pickFile(e.target.files?.[0] ?? null)}
          />
          <div className="w-[90px] h-[90px] bg-pink flex items-center justify-center text-4xl text-white shadow-[0_14px_30px_rgba(242,84,125,0.4)] mb-6 anim-float">
            ⬆
          </div>
          <h2 className="font-serif font-medium text-2xl">
            {file ? file.name : "Drag & Drop Your Video"}
          </h2>
          <p className="text-gray-400 text-sm mt-2.5 mb-6">
            {file ? formatBytes(file.size) : "or click to browse your files"}
          </p>
          <PinkButton type="button">
            {file ? "Choose a Different File" : "Choose Video File"}
          </PinkButton>
          <div className="flex gap-2.5 mt-6">
            {["MP4", "MOV", "AVI", "WEBM"].map((f) => (
              <span
                key={f}
                className="bg-blush text-[#c22553] px-3.5 py-1.5 rounded-full text-xs font-bold"
              >
                {f}
              </span>
            ))}
          </div>
          <div className="mt-4 text-xs text-gray-300">
            Max {MAX_MB} MB · up to 60 minutes
          </div>
        </div>

        {/* Right column */}
        <div className="flex-1 w-full flex flex-col gap-5">
          <div className="bg-white p-6 shadow-[0_12px_30px_rgba(203,86,120,0.1)]">
            <h3 className="font-serif text-[17px] mb-4">Project Details</h3>
            <label className="block text-[13px] font-semibold text-gray-600 mb-1.5">
              Project Name
            </label>
            <input
              value={projectName}
              onChange={(e) => setProjectName(e.target.value)}
              placeholder="My awesome video"
              className="w-full px-3.5 py-3 border-[1.5px] border-[#eadfe2] rounded-md text-sm bg-[#fdf8f9] focus:outline-none focus:border-pink"
            />
          </div>

          {file && (
            <div className="bg-white p-6 shadow-[0_12px_30px_rgba(203,86,120,0.1)] anim-fade-up">
              <h3 className="font-serif text-[17px] mb-4">Selected File</h3>
              <div className="flex gap-3.5 items-center bg-blush p-3.5 rounded-lg">
                <div className="w-[70px] h-12 rounded bg-gradient-to-br from-[#1c6b40] to-[#39a56b] flex items-center justify-center text-white flex-shrink-0">
                  ▶
                </div>
                <div className="min-w-0">
                  <b className="text-[13.5px] block truncate">{file.name}</b>
                  <span className="text-[11.5px] text-gray-400">
                    {formatBytes(file.size)}
                    {uploading && " · uploading…"}
                  </span>
                </div>
              </div>
              {uploading && (
                <div className="mt-4">
                  <div className="h-2 bg-[#f4e3e7] rounded overflow-hidden">
                    <div className="h-full w-full bg-gradient-to-r from-pink to-[#ff8fab] animate-pulse" />
                  </div>
                  <div className="flex justify-between text-xs text-gray-400 mt-2">
                    <span>Uploading & extracting metadata…</span>
                  </div>
                </div>
              )}
            </div>
          )}

          {result?.success && result.metadata && (
            <div className="bg-white p-6 shadow-[0_12px_30px_rgba(203,86,120,0.1)] anim-fade-up">
              <h3 className="font-serif text-[17px] mb-4">Detected Metadata</h3>
              <div className="grid grid-cols-2 gap-2.5">
                {[
                  { v: formatDuration(result.metadata.duration_seconds), l: "DURATION" },
                  {
                    v: result.metadata.dimensions
                      ? `${result.metadata.dimensions.width}×${result.metadata.dimensions.height}`
                      : result.metadata.resolution,
                    l: "RESOLUTION",
                  },
                  { v: result.metadata.fps.toFixed(2), l: "FPS" },
                  { v: result.metadata.codec.toUpperCase(), l: "CODEC" },
                ].map((m) => (
                  <div key={m.l} className="bg-blush p-3 rounded-md">
                    <b className="block font-serif text-[15px]">{m.v}</b>
                    <span className="text-[11px] text-gray-400 tracking-wider">{m.l}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {error && (
            <div className="bg-[#fde2e6] text-[#c22f4f] text-[13px] rounded-md px-4 py-3">
              ⚠ {error}
            </div>
          )}

          {result?.success && result.video_id ? (
            <button
              onClick={() =>
                router.push(`/projects/${result.video_id}/processing?start=1`)
              }
              className="w-full bg-green-d hover:bg-green text-white font-bold text-[15px] rounded-md py-4 transition-colors cursor-pointer"
            >
              🎬 Start Captioning ➜
            </button>
          ) : (
            <button
              onClick={onUpload}
              disabled={!file || uploading}
              className="w-full bg-green-d hover:bg-green text-white font-bold text-[15px] rounded-md py-4 transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {uploading ? "Uploading…" : "🎬 Create Project ➜"}
            </button>
          )}
        </div>
      </div>
    </AppShell>
  );
}
