"use client";

import { useEffect, useState } from "react";
import AppShell from "@/components/AppShell";
import { Kicker, PinkButton } from "@/components/ui";
import {
  me,
  listSessions,
  revokeSession,
  revokeAllSessions,
  getUserToken,
  listProjects,
  type UserSchema,
} from "@/lib/api";

type SessionRow = {
  session_id: string;
  created_at: string;
  last_seen_at?: string | null;
  ip_address?: string | null;
  user_agent?: string | null;
};

export default function AccountPage() {
  const [user, setUser] = useState<UserSchema | null>(null);
  const [sessions, setSessions] = useState<SessionRow[]>([]);
  const [projectCount, setProjectCount] = useState<number | null>(null);
  const [authUnavailable, setAuthUnavailable] = useState(false);

  useEffect(() => {
    (async () => {
      // Project stats always work (public endpoint)
      listProjects({ limit: 1 })
        .then((r) => setProjectCount(r.total))
        .catch(() => {});

      // Auth-backed data: gracefully degrade while backend providers are stubbed
      if (!getUserToken()) {
        setAuthUnavailable(true);
        return;
      }
      try {
        const res = await me();
        setUser(res.user);
        const s = await listSessions();
        setSessions(s.sessions);
      } catch {
        setAuthUnavailable(true);
      }
    })();
  }, []);

  async function onRevoke(id: string) {
    try {
      await revokeSession(id);
      setSessions((s) => s.filter((x) => x.session_id !== id));
    } catch (e) {
      alert(e instanceof Error ? e.message : "Revoke failed.");
    }
  }

  async function onRevokeAll() {
    if (!confirm("Log out everywhere? All sessions will be revoked.")) return;
    try {
      await revokeAllSessions();
      setSessions([]);
    } catch (e) {
      alert(e instanceof Error ? e.message : "Revoke failed.");
    }
  }

  const displayName = user?.display_name ?? user?.username ?? "Creator";
  const email = user?.email ?? "guest@captiondb.app";

  return (
    <AppShell>
      <Kicker>Account</Kicker>
      <h1 className="font-serif font-medium text-3xl mt-1 mb-7">Profile &amp; Security</h1>

      {authUnavailable && (
        <div className="mb-6 bg-[#fff3cd] text-[#8a6d00] text-[13px] rounded-md px-5 py-3.5">
          ⓘ Account services aren&apos;t live on this deployment yet — the backend auth
          providers are still being connected. Your projects work without an account.
        </div>
      )}

      <div className="flex flex-col xl:flex-row gap-6 items-start">
        {/* Profile card */}
        <div className="w-full xl:w-[320px] bg-white text-center pb-6 shadow-[0_12px_30px_rgba(203,86,120,0.1)]">
          <div className="h-[90px] bg-gradient-to-br from-green-d to-green-l" />
          <div className="w-[92px] h-[92px] rounded-full bg-pink text-white text-4xl font-bold flex items-center justify-center -mt-11 mx-auto mb-3.5 border-[5px] border-white shadow-[0_10px_24px_rgba(242,84,125,0.35)]">
            {displayName.charAt(0).toUpperCase()}
          </div>
          <h2 className="font-serif text-[22px]">{displayName}</h2>
          <div className="text-gray-400 text-[13px] mt-1.5 mb-3.5">{email}</div>
          <div className="flex gap-2 justify-center flex-wrap px-4">
            {user?.verified && (
              <span className="text-[11.5px] font-bold px-3.5 py-1 rounded-full bg-[#e6f7ec] text-green">
                ✓ Verified
              </span>
            )}
            <span className="text-[11.5px] font-bold px-3.5 py-1 rounded-full bg-blush text-[#c22553]">
              {user?.role ?? "Guest"}
            </span>
            <span className="text-[11.5px] font-bold px-3.5 py-1 rounded-full bg-[#e6f7ec] text-green">
              ● {user?.status ?? "Active"}
            </span>
          </div>
          <div className="flex mt-5 pt-4 border-t border-[#faeef1]">
            <div className="flex-1">
              <b className="block font-serif text-xl">{projectCount ?? "—"}</b>
              <span className="text-[11px] text-gray-400 tracking-wider">PROJECTS</span>
            </div>
            <div className="flex-1">
              <b className="block font-serif text-xl">{user?.identities.length ?? 0}</b>
              <span className="text-[11px] text-gray-400 tracking-wider">IDENTITIES</span>
            </div>
            <div className="flex-1">
              <b className="block font-serif text-xl">{sessions.length}</b>
              <span className="text-[11px] text-gray-400 tracking-wider">SESSIONS</span>
            </div>
          </div>
        </div>

        {/* Right column */}
        <div className="flex-1 w-full flex flex-col gap-5">
          {/* Profile details */}
          <div className="bg-white shadow-[0_12px_30px_rgba(203,86,120,0.1)]">
            <div className="px-6 py-5 border-b border-[#faeef1] flex justify-between items-center">
              <b className="font-serif text-[17px]">Profile Details</b>
              <PinkButton
                className="px-5 py-2.5 text-[13px]"
                disabled={authUnavailable}
                title={authUnavailable ? "Available once account services go live" : undefined}
              >
                Save Changes
              </PinkButton>
            </div>
            <div className="p-6 pt-2">
              <div className="flex flex-col md:flex-row gap-4">
                <div className="flex-1">
                  <label className="block text-[12.5px] font-semibold text-gray-600 mt-3.5 mb-1.5">
                    Display Name
                  </label>
                  <input
                    defaultValue={displayName}
                    disabled={authUnavailable}
                    className="w-full px-3.5 py-3 border-[1.5px] border-[#eadfe2] rounded-md text-sm bg-[#fdf8f9] focus:outline-none focus:border-pink disabled:opacity-60"
                  />
                </div>
                <div className="flex-1">
                  <label className="block text-[12.5px] font-semibold text-gray-600 mt-3.5 mb-1.5">
                    Username
                  </label>
                  <input
                    defaultValue={user?.username ?? ""}
                    disabled={authUnavailable}
                    className="w-full px-3.5 py-3 border-[1.5px] border-[#eadfe2] rounded-md text-sm bg-[#fdf8f9] focus:outline-none focus:border-pink disabled:opacity-60"
                  />
                </div>
              </div>
              <label className="block text-[12.5px] font-semibold text-gray-600 mt-3.5 mb-1.5">
                Email Address
              </label>
              <input
                defaultValue={email}
                disabled={authUnavailable}
                className="w-full px-3.5 py-3 border-[1.5px] border-[#eadfe2] rounded-md text-sm bg-[#fdf8f9] focus:outline-none focus:border-pink disabled:opacity-60"
              />
            </div>
          </div>

          {/* Linked identities */}
          <div className="bg-white shadow-[0_12px_30px_rgba(203,86,120,0.1)]">
            <div className="px-6 py-5 border-b border-[#faeef1]">
              <b className="font-serif text-[17px]">Linked Identities</b>
            </div>
            <div className="px-6 py-2">
              {(user?.identities.length
                ? user.identities.map((i) => ({
                    icon: i.provider === "email" ? "📧" : "🔗",
                    name: i.oauth_provider
                      ? i.oauth_provider.charAt(0).toUpperCase() + i.oauth_provider.slice(1)
                      : "Email & Password",
                    sub: i.linked_at ? `Linked ${new Date(i.linked_at).toLocaleDateString()}` : "Primary sign-in",
                    linked: true,
                  }))
                : [
                    { icon: "📧", name: "Email & Password", sub: "Primary sign-in", linked: true },
                    { icon: "🟢", name: "Google", sub: "Not connected", linked: false },
                    { icon: "⚫", name: "GitHub", sub: "Not connected", linked: false },
                  ]
              ).map((row) => (
                <div
                  key={row.name}
                  className="flex items-center gap-3.5 py-3.5 border-b border-[#faeef1] last:border-0"
                >
                  <div className="w-[42px] h-[42px] rounded-lg bg-blush flex items-center justify-center text-lg">
                    {row.icon}
                  </div>
                  <div className="flex-1">
                    <b className="text-sm">{row.name}</b>
                    <span className="block text-xs text-gray-400 mt-0.5">{row.sub}</span>
                  </div>
                  <button
                    disabled={authUnavailable}
                    className={`border-[1.5px] rounded-md px-4.5 py-2 text-[12.5px] font-semibold transition-colors cursor-pointer disabled:opacity-40 ${
                      row.linked
                        ? "border-[#f6ccd5] text-[#c22f4f] hover:bg-[#fde2e6]"
                        : "border-[#f0dde2] text-gray-600 hover:border-pink"
                    }`}
                  >
                    {row.linked ? (row.name === "Email & Password" ? "Change Password" : "Unlink") : "＋ Link Account"}
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* Sessions */}
          <div className="bg-white shadow-[0_12px_30px_rgba(203,86,120,0.1)]">
            <div className="px-6 py-5 border-b border-[#faeef1] flex justify-between items-center">
              <b className="font-serif text-[17px]">Active Sessions</b>
              <button
                onClick={onRevokeAll}
                disabled={authUnavailable || sessions.length === 0}
                className="border-[1.5px] border-[#f6ccd5] text-[#c22f4f] rounded-md px-4.5 py-2 text-[12.5px] font-semibold hover:bg-[#fde2e6] transition-colors cursor-pointer disabled:opacity-40"
              >
                Log Out Everywhere
              </button>
            </div>
            <div className="px-6 py-2">
              {sessions.length === 0 ? (
                <div className="py-5 text-[13.5px] text-gray-400">
                  {authUnavailable
                    ? "Session management will appear here once account services are live."
                    : "No other active sessions."}
                </div>
              ) : (
                sessions.map((s, i) => (
                  <div
                    key={s.session_id}
                    className="flex items-center gap-3.5 py-3.5 border-b border-[#faeef1] last:border-0"
                  >
                    <div className="w-[42px] h-[42px] rounded-lg bg-[#e6f7ec] flex items-center justify-center text-lg">
                      {s.user_agent?.toLowerCase().includes("mobile") ? "📱" : "💻"}
                    </div>
                    <div className="flex-1 min-w-0">
                      <b className="text-sm block truncate">
                        {s.user_agent ?? "Unknown device"}
                      </b>
                      <span className="block text-xs text-gray-400 mt-0.5">
                        {s.ip_address ?? "unknown IP"} · started{" "}
                        {new Date(s.created_at).toLocaleString()}
                      </span>
                    </div>
                    {i === 0 ? (
                      <span className="text-[11px] font-bold text-green bg-[#e6f7ec] px-3 py-1 rounded-full">
                        This device
                      </span>
                    ) : (
                      <button
                        onClick={() => onRevoke(s.session_id)}
                        className="border-[1.5px] border-[#f6ccd5] text-[#c22f4f] rounded-md px-4.5 py-2 text-[12.5px] font-semibold hover:bg-[#fde2e6] transition-colors cursor-pointer"
                      >
                        Revoke
                      </button>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
