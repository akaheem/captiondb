import type { Metadata, Viewport } from "next";
import { Inter, Geist } from "next/font/google";
import "./globals.css";
import { RootProviders } from "@/providers";
import { ErrorBoundary } from "@/components/error-boundary";
import { APP_CONFIG } from "@/lib/config";
import { cn } from "@/lib/utils";

const geist = Geist({subsets:['latin'],variable:'--font-sans'});

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: APP_CONFIG.name,
    template: `%s · ${APP_CONFIG.name}`,
  },
  description: APP_CONFIG.description,
  robots: {
    index: false, // Private app — never index
    follow: false,
  },
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#ffffff" },
    { media: "(prefers-color-scheme: dark)", color: "#09090b" },
  ],
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html
      lang="en"
      className={cn("h-full", inter.variable, "font-sans", geist.variable)}
      suppressHydrationWarning
    >
      <body className="h-full bg-background font-sans text-foreground antialiased">
        <ErrorBoundary>
          <RootProviders>{children}</RootProviders>
        </ErrorBoundary>
      </body>
    </html>
  );
}
