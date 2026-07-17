"use client";

import { useEffect, useState } from "react";

const PHRASES = ["Every Scene", "Every Frame", "Every Moment", "Every Tone"];

/** Typewriter effect cycling through phrases. */
export function Typewriter() {
  const [text, setText] = useState("");
  const [phraseIdx, setPhraseIdx] = useState(0);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    const phrase = PHRASES[phraseIdx];
    let timeout: ReturnType<typeof setTimeout>;

    if (!deleting && text.length < phrase.length) {
      timeout = setTimeout(() => setText(phrase.slice(0, text.length + 1)), 90);
    } else if (!deleting && text.length === phrase.length) {
      timeout = setTimeout(() => setDeleting(true), 2100);
    } else if (deleting && text.length > 0) {
      timeout = setTimeout(() => setText(phrase.slice(0, text.length - 1)), 45);
    } else {
      timeout = setTimeout(() => {
        setDeleting(false);
        setPhraseIdx((i) => (i + 1) % PHRASES.length);
      }, 250);
    }
    return () => clearTimeout(timeout);
  }, [text, deleting, phraseIdx]);

  return <span className="text-[#ffd9e2] typewriter-caret">{text}</span>;
}

const DEMO_CAPTIONS = [
  { tone: "SCENE 02 · FORMAL", text: "A presenter walks across the stage as the audience applauds warmly." },
  { tone: "SCENE 02 · SARCASTIC", text: "Ah yes, another riveting slide of bullet points. Groundbreaking." },
  { tone: "SCENE 02 · HUMOROUS TECH", text: "POV: the demo works and nobody knows why. Ship it." },
  { tone: "SCENE 02 · AUDIO", text: "[Applause swells] Footsteps on stage. Upbeat music fades out." },
];

/** Hero video frame with cycling scene chips and rotating captions. */
export function HeroFrame() {
  const [capIdx, setCapIdx] = useState(0);
  const [sceneIdx, setSceneIdx] = useState(0);

  useEffect(() => {
    const t = setInterval(() => {
      setCapIdx((i) => (i + 1) % DEMO_CAPTIONS.length);
      setSceneIdx((i) => (i + 1) % 4);
    }, 3400);
    return () => clearInterval(t);
  }, []);

  const cap = DEMO_CAPTIONS[capIdx];

  return (
    <div className="absolute inset-y-[60px] left-0 right-[60px] rounded-lg overflow-hidden shadow-[0_30px_60px_rgba(0,0,0,0.35)] anim-float">
      <div className="absolute inset-0 bg-gradient-to-b from-green-l to-[#16552f]" />
      {/* scene chips */}
      <div className="absolute top-6 left-6 flex gap-2">
        {[0, 1, 2, 3].map((i) => (
          <span
            key={i}
            className={`w-[54px] h-[34px] rounded transition-all duration-500 ${
              i === sceneIdx
                ? "border-2 border-pink bg-pink/35"
                : "border border-white/35 bg-white/20"
            }`}
          />
        ))}
      </div>
      {/* play button */}
      <div className="absolute top-[38%] left-[44%] w-[84px] h-[84px] rounded-full bg-white/15 border-2 border-white/60 flex items-center justify-center text-white text-3xl pulse-ring">
        ▶
      </div>
      {/* caption bar */}
      <div
        key={capIdx}
        className="absolute left-6 right-6 bottom-6 bg-black/55 border-l-4 border-pink rounded-md px-4 py-3 text-white text-[15px] anim-fade-in"
      >
        <b className="block text-[#ff9db6] text-[11px] tracking-[2px] mb-1">
          {cap.tone}
        </b>
        {cap.text}
      </div>
    </div>
  );
}
