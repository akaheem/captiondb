"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Logo } from "@/components/ui";
import type { ReactNode } from "react";

const NAV = [
  { href: "/dashboard", icon: "▦", label: "Dashboard" },
  { href: "/upload", icon: "⬆", label: "Upload Video" },
  { href: "/account", icon: "👤", label: "Profile" },
];

/** Green sidebar shell for the authenticated app area. */
export default function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="flex min-h-screen">
      <aside className="w-[250px] bg-green-d text-white py-6 flex-col hidden lg:flex sticky top-0 h-screen">
        <div className="px-5 mb-8">
          <Logo className="block text-center py-3 text-[17px] w-full" />
        </div>
        {NAV.map((item) => {
          const active =
            item.href === "/dashboard"
              ? pathname === "/dashboard" || pathname.startsWith("/projects")
              : pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-7 py-3.5 text-sm transition-colors ${
                active
                  ? "bg-pink/20 text-white border-l-4 border-pink"
                  : "text-[#cfe6d7] hover:text-white border-l-4 border-transparent"
              }`}
            >
              <span>{item.icon}</span> {item.label}
            </Link>
          );
        })}
        <div className="flex-1" />
        <Link
          href="/admin"
          className="mx-5 mb-3 text-center text-[11px] tracking-[2px] text-white/40 hover:text-pink transition-colors"
        >
          ADMIN CONSOLE
        </Link>
        <div className="mx-5 p-3.5 bg-black/25 rounded-lg flex gap-2.5 items-center text-[13px]">
          <div className="w-[34px] h-[34px] rounded-full bg-pink flex items-center justify-center font-bold flex-shrink-0">
            C
          </div>
          <div>
            <b>Creator</b>
            <br />
            <span className="opacity-70 text-[11.5px]">CaptionDB Studio</span>
          </div>
        </div>
      </aside>

      <div className="flex-1 flex flex-col min-w-0">
        {/* Mobile top bar */}
        <div className="lg:hidden bg-green-d px-5 py-3 flex items-center justify-between">
          <Logo className="px-4 py-2 text-sm" />
          <div className="flex gap-4 text-white/85 text-sm">
            {NAV.map((n) => (
              <Link key={n.href} href={n.href} className="hover:text-white">
                {n.icon}
              </Link>
            ))}
          </div>
        </div>
        <main className="flex-1 px-5 md:px-10 py-8">{children}</main>
      </div>
    </div>
  );
}
