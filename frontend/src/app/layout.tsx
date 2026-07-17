import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CaptionDB — AI Video Captions in Five Tones",
  description:
    "Upload any video. CaptionDB detects scenes, analyzes keyframes with vision AI, and writes captions in five distinct tones.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
