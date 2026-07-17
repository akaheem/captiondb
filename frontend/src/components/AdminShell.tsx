"use client";

import { useEffect, useState, type ReactNode } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { adminMe, getAdminToken, setAdminToken } from "@/lib/api";
import { Spinner } from "@/components/ui";

const NAV = [
  { href: "/admin", icon: "▦", label: "Overview", exact: true },
  { href: "/admin/requests", icon: "🗂", label: "All Requests", exact: false },
  { href: "/admin/health", icon: "♥", label: "System Health", exact: true },
];

/** Dark admin shell. Verifies the admin token before rendering children. */
export default function AdminShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [state, setState] = useState<"checking" | "ok">("checking");
  const [email, setEmail] = useState("");

  useEffect(() => {
    (async () => {
      if (!getAdminToken()) {
        router.replace("/admin/login");
        return;
      }
      try {
        const res = await adminMe();
        setEmail(res.email);
        setState("ok");
      } catch {
        setAdminToken(null);
        router.replace("/admin/login");
      }
    })();
  }, [router]);

  if (state === "checking") {
    return (
      <div className="min-h-screen bg-[#f7f2f3] flex items-center justify-center gap-3 text-gray-500">
        <Spinner /> Verifying admin session…
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-[#f7f2f3]">
      <aside className="w-[250px] bg-ink text-white py-6 flex-col hidden lg:flex sticky top-0 h-screen">
        <div className="px-5">
          <Link
            href="/admin"
            className="block bg-pink text-white font-serif italic font-bold rounded-lg py-3 text-center text-[17px] shadow-[0_8px_20px_rgba(242,84,125,0.4)]"
          >
            🎬 CaptionDB
          </Link>
        </div>
        <div className="text-center text-[10px] tracking-[3px] text-pink font-bold mt-2 mb-6">
          ADMIN CONSOLE
        </div>
        {NAV.map((item) => {
          const active = item.exact
            ? pathname === item.href
            : pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-7 py-3.5 text-sm transition-colors ${
                active
                  ? "bg-pink/15 text-white border-l-4 border-pink"
                  : "text-[#9fb3a8] hover:text-white border-l-4 border-transparent"
              }`}
            >
              <span>{item.icon}</span> {item.label}
            </Link>
          );
        })}
        <Link
          href="/dashboard"
          className="flex items-center gap-3 px-7 py-3.5 text-sm text-[#9fb3a8] hover:text-white border-l-4 border-transparent"
        >
          ↩ Exit to App
        </Link>
        <div className="flex-1" />
        <div className="mx-5 p-3.5 bg-[#1b1f1d] rounded-lg flex gap-2.5 items-center text-xs">
          <div className="w-[34px] h-[34px] rounded-full bg-green flex items-center justify-center font-bold flex-shrink-0">
            A
          </div>
          <div className="min-w-0">
            <b>Admin</b>
            <br />
            <span className="opacity-60 text-[10.5px] block truncate">{email}</span>
          </div>
        </div>
        <button
          onClick={() => {
            setAdminToken(null);
            router.replace("/admin/login");
          }}
          className="mx-5 mt-3 py-2.5 text-xs text-[#9fb3a8] hover:text-pink border border-[#2a2f2c] rounded-lg transition-colors cursor-pointer"
        >
          Sign out
        </button>
      </aside>

      <div className="flex-1 flex flex-col min-w-0">
        <div className="lg:hidden bg-ink px-5 py-3 flex items-center justify-between">
          <span className="bg-pink text-white font-serif italic font-bold rounded px-3 py-1.5 text-sm">
            🎬 Admin
          </span>
          <div className="flex gap-4 text-white/85 text-sm">
            {NAV.map((n) => (
              <Link key={n.href} href={n.href}>
                {n.icon}
              </Link>
            ))}
          </div>
        </div>
        <main className="flex-1 px-5 md:px-9 py-7">{children}</main>
      </div>
    </div>
  );
}
