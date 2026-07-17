"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { adminLogin, setAdminToken } from "@/lib/api";

export default function AdminLoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const res = await adminLogin(email, password);
      if (res.success && res.token) {
        setAdminToken(res.token);
        router.push("/admin");
      } else {
        setError("Invalid credentials.");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="min-h-screen bg-ink flex flex-col items-center justify-center p-6">
      <div className="w-full max-w-[420px] anim-fade-up">
        <div className="text-center mb-8">
          <span className="inline-block bg-pink text-white font-serif italic font-bold rounded-lg px-7 py-3.5 text-xl shadow-[0_8px_24px_rgba(242,84,125,0.5)]">
            🎬 CaptionDB
          </span>
          <div className="text-[11px] tracking-[4px] text-pink font-bold mt-4">
            ADMIN CONSOLE
          </div>
        </div>
        <form
          onSubmit={onSubmit}
          className="bg-white rounded-xl p-9 shadow-[0_30px_70px_rgba(0,0,0,0.4)]"
        >
          <h1 className="font-serif font-medium text-[26px]">Administrator Sign In</h1>
          <p className="text-gray-400 text-[13px] mt-1.5 mb-6">
            Restricted area — platform owner only.
          </p>
          <label className="block text-[13px] font-semibold text-gray-600 mb-1.5">
            Admin Email
          </label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="admin@example.com"
            required
            className="w-full px-4 py-3.5 border-[1.5px] border-[#eadfe2] rounded-md text-sm bg-[#fdf8f9] focus:outline-none focus:border-pink mb-4"
          />
          <label className="block text-[13px] font-semibold text-gray-600 mb-1.5">
            Password
          </label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••••"
            required
            className="w-full px-4 py-3.5 border-[1.5px] border-[#eadfe2] rounded-md text-sm bg-[#fdf8f9] focus:outline-none focus:border-pink"
          />
          {error && (
            <div className="mt-4 bg-[#fde2e6] text-[#c22f4f] text-[13px] rounded-md px-4 py-3">
              ⚠ {error}
            </div>
          )}
          <button
            type="submit"
            disabled={busy}
            className="w-full mt-6 bg-pink hover:bg-pink-d text-white font-bold rounded-md py-4 text-[15px] shadow-[0_8px_20px_rgba(242,84,125,0.35)] transition-colors cursor-pointer disabled:opacity-50"
          >
            {busy ? "Verifying…" : "Enter Console ➜"}
          </button>
        </form>
        <div className="text-center mt-6">
          <Link href="/" className="text-white/40 hover:text-white/70 text-[13px]">
            ← Back to CaptionDB
          </Link>
        </div>
      </div>
    </main>
  );
}
