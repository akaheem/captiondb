import Link from "next/link";
import type { VideoStatus } from "@/lib/api";

export function Logo({ className = "" }: { className?: string }) {
  return (
    <Link
      href="/"
      className={`inline-block bg-pink text-white font-serif italic font-bold rounded-lg px-6 py-3 shadow-[0_8px_20px_rgba(242,84,125,0.4)] ${className}`}
    >
      🎬 CaptionDB
    </Link>
  );
}

export function PinkButton({
  children,
  className = "",
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      {...props}
      className={`bg-pink hover:bg-pink-d text-white font-bold rounded-md px-6 py-3 text-sm shadow-[0_8px_20px_rgba(242,84,125,0.35)] transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed ${className}`}
    >
      {children}
    </button>
  );
}

export function GhostButton({
  children,
  className = "",
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      {...props}
      className={`bg-white text-gray-600 font-semibold rounded-md px-5 py-3 text-sm border-[1.5px] border-[#f0dde2] hover:border-pink transition-colors cursor-pointer disabled:opacity-50 ${className}`}
    >
      {children}
    </button>
  );
}

const STATUS_STYLES: Record<VideoStatus, string> = {
  Completed: "bg-[#e6f7ec] text-green",
  Processing: "bg-[#fff3cd] text-[#8a6d00]",
  Queued: "bg-[#fff3cd] text-[#8a6d00]",
  Failed: "bg-[#fde2e6] text-[#c22f4f]",
  Idle: "bg-gray-200 text-gray-600",
};

export function StatusPill({ status }: { status: VideoStatus }) {
  return (
    <span
      className={`inline-block text-[11px] font-bold px-3 py-1 rounded-full ${STATUS_STYLES[status] ?? STATUS_STYLES.Idle}`}
    >
      ● {status}
    </span>
  );
}

export function Kicker({ children }: { children: React.ReactNode }) {
  return (
    <div className="text-pink tracking-[3px] text-[11px] font-bold uppercase">
      {children}
    </div>
  );
}

export function Spinner({ className = "" }: { className?: string }) {
  return (
    <span
      className={`inline-block w-5 h-5 border-2 border-pink border-t-transparent rounded-full animate-spin ${className}`}
    />
  );
}
