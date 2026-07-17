"use client";

import Link from "next/link";
import { Logo } from "@/components/ui";
import type { ReactNode } from "react";

/** Shared split-panel shell for login/signup pages. */
export default function AuthShell({
  headline,
  blurb,
  quote,
  children,
}: {
  headline: ReactNode;
  blurb: string;
  quote: { tone: string; text: string };
  children: ReactNode;
}) {
  return (
    <main className="flex-1 flex flex-col min-h-screen">
      <div className="bg-green-d px-6 md:px-14 py-4 flex items-center justify-between">
        <Logo className="px-6 py-2.5 text-[17px]" />
        <Link href="/" className="text-white/85 hover:text-white text-sm">
          ← Back to Home
        </Link>
      </div>
      <div className="flex-1 flex items-center justify-center p-6 md:p-12">
        <div className="flex flex-col md:flex-row w-full max-w-[960px] shadow-[0_30px_70px_rgba(203,86,120,0.2)] rounded-xl overflow-hidden anim-fade-up">
          {/* Green side */}
          <div className="flex-1 bg-gradient-to-br from-green-d to-green-l text-white p-10 md:p-12 relative overflow-hidden">
            <div className="absolute -right-8 -bottom-16 text-[240px] leading-none text-white/5 font-serif select-none">
              ❝
            </div>
            <Logo className="px-5 py-2.5 text-base" />
            <h1 className="font-serif font-medium text-3xl md:text-[38px] leading-[1.25] mt-8">
              {headline}
            </h1>
            <p className="mt-5 opacity-85 leading-7 text-[14.5px]">{blurb}</p>
            <div className="mt-11 bg-black/30 border-l-4 border-pink rounded-md px-4 py-3.5 text-[13.5px] relative z-10">
              <b className="block text-[#ff9db6] text-[10.5px] tracking-[2px] mb-1">
                {quote.tone}
              </b>
              {quote.text}
            </div>
          </div>
          {/* Form side */}
          <div className="flex-[1.05] bg-white p-10 md:p-14">{children}</div>
        </div>
      </div>
    </main>
  );
}

export function Field({
  label,
  ...props
}: { label: string } & React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <div className="mt-4.5">
      <label className="block text-[13px] font-semibold text-gray-600 mb-1.5">
        {label}
      </label>
      <input
        {...props}
        className="w-full px-4 py-3.5 border-[1.5px] border-[#eadfe2] rounded-md text-sm bg-[#fdf8f9] focus:outline-none focus:border-pink transition-colors"
      />
    </div>
  );
}

export function OAuthRow() {
  return (
    <>
      <div className="flex items-center gap-3.5 my-6 text-gray-400 text-xs before:content-[''] before:flex-1 before:h-px before:bg-gray-200 after:content-[''] after:flex-1 after:h-px after:bg-gray-200">
        OR CONTINUE WITH
      </div>
      <div className="flex gap-3">
        {[
          { icon: "🟢", name: "Google" },
          { icon: "⚫", name: "GitHub" },
          { icon: "🟦", name: "Microsoft" },
        ].map((p) => (
          <button
            key={p.name}
            type="button"
            title="OAuth provider configuration pending on the backend"
            className="flex-1 py-3 border-[1.5px] border-gray-200 rounded-md text-[13.5px] font-semibold text-gray-700 flex items-center justify-center gap-2 hover:border-pink transition-colors cursor-pointer"
          >
            {p.icon} {p.name}
          </button>
        ))}
      </div>
    </>
  );
}
