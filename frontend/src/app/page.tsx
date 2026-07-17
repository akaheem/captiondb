import Link from "next/link";
import { Logo, Kicker } from "@/components/ui";
import { Typewriter, HeroFrame } from "@/components/Hero";
import Reveal from "@/components/Reveal";

const FEATURES = [
  {
    icon: "⬆",
    title: "Upload & Analyze",
    text: "Drop in MP4, MOV, AVI or WebM up to 500 MB. We instantly extract duration, FPS, codec and resolution.",
    num: "01",
  },
  {
    icon: "🎬",
    title: "Scene Detection",
    text: "Smart shot-boundary detection splits your video into meaningful scenes with precise timestamps.",
    num: "02",
  },
  {
    icon: "👁",
    title: "Vision AI Analysis",
    text: "Keyframes are analyzed by a vision language model — objects, activities, colors and on-screen text.",
    num: "03",
  },
  {
    icon: "✍",
    title: "Five Caption Tones",
    text: "Every scene gets captions in formal, sarcastic, humorous-tech, humorous and audio-description styles.",
    num: "04",
  },
];

const TONES = [
  { emoji: "🏛", name: "Formal", label: "Professional", sample: '"A presenter demonstrates the product to an attentive audience."', pink: false },
  { emoji: "😏", name: "Sarcastic", label: "Witty", sample: '"Ah yes, another riveting slide of bullet points. Groundbreaking."', pink: true },
  { emoji: "🤓", name: "Humorous Tech", label: "For Devs", sample: '"POV: the demo works and nobody knows why. Ship it."', pink: false },
  { emoji: "😂", name: "Humorous", label: "For Everyone", sample: '"That moment when the coffee kicks in mid-presentation."', pink: true },
  { emoji: "🔊", name: "Audio", label: "Accessibility", sample: '"[Upbeat music] Footsteps on stage. Audience applause swells."', pink: false },
];

export default function LandingPage() {
  return (
    <main className="flex-1">
      {/* ── Top strip ─────────────────────────────────────── */}
      <div className="bg-green-d text-white flex items-center justify-center gap-6 md:gap-9 px-6 md:px-14 py-3.5 text-[13px] flex-wrap">
        <span className="opacity-90 hidden md:inline">📶 <b>API</b> /api/v1 · online</span>
        <span className="text-pink font-bold hidden md:inline">/</span>
        <span className="opacity-90 hidden sm:inline">📧 hello@captiondb.app</span>
        <span className="text-pink font-bold hidden sm:inline">/</span>
        <Logo className="px-8 py-3.5 text-xl" />
        <span className="text-pink font-bold hidden sm:inline">/</span>
        <span className="opacity-90 hidden sm:inline">📍 Powered by Vision AI</span>
        <span className="text-pink font-bold hidden md:inline">/</span>
        <span className="opacity-90 hidden md:inline">🕐 Processes 24/7</span>
      </div>

      {/* ── Nav ───────────────────────────────────────────── */}
      <div className="bg-green-d px-6 md:px-14">
        <nav className="bg-white rounded-md flex items-center justify-center gap-4 md:gap-8 px-6 py-4 shadow-[0_10px_30px_rgba(0,0,0,0.15)] flex-wrap">
          <Link href="/" className="text-pink font-medium text-[15px]">Home</Link>
          <Link href="#about" className="text-gray-700 font-medium text-[15px] hover:text-pink">About</Link>
          <Link href="#features" className="text-gray-700 font-medium text-[15px] hover:text-pink">Features</Link>
          <Link href="#tones" className="text-gray-700 font-medium text-[15px] hover:text-pink">Tones</Link>
          <Link href="/login" className="text-gray-700 font-medium text-[15px] hover:text-pink">Login</Link>
          <Link href="/signup" className="text-gray-700 font-medium text-[15px] hover:text-pink">Signup</Link>
          <Link
            href="/dashboard"
            className="ml-0 md:ml-5 bg-pink hover:bg-pink-d text-white font-semibold text-sm rounded px-5 py-2.5 shadow-[0_6px_16px_rgba(242,84,125,0.35)] transition-colors"
          >
            Get Started ➜
          </Link>
        </nav>
      </div>

      {/* ── Hero ──────────────────────────────────────────── */}
      <section className="relative flex flex-col lg:flex-row min-h-[520px] overflow-hidden bg-gradient-to-br from-green-d via-green-d to-green">
        <div className="absolute -left-32 -top-32 w-[420px] h-[420px] rounded-full bg-white/5" />
        <div className="absolute left-[46%] -bottom-10 text-[280px] leading-none text-white/5 font-serif select-none pointer-events-none">
          ❝
        </div>
        <div className="flex-[1.1] px-8 md:px-20 py-16 md:py-24 text-white relative z-10">
          <h1 className="font-serif font-medium text-4xl md:text-6xl leading-[1.18] anim-fade-up">
            Captions That
            <br />
            Understand
            <br />
            <Typewriter />
          </h1>
          <p className="mt-6 text-base opacity-85 max-w-[480px] leading-7 anim-fade-up delay-2">
            Upload any video and CaptionDB detects scenes, analyzes keyframes
            with vision AI, and writes captions in five distinct tones — formal
            to sarcastic.
          </p>
          <Link
            href="/upload"
            className="inline-block mt-9 bg-pink hover:bg-pink-d text-white font-bold text-sm rounded px-7 py-3.5 shadow-[0_8px_20px_rgba(242,84,125,0.4)] transition-colors anim-fade-up delay-3"
          >
            Upload Your Video ➜
          </Link>
        </div>
        <div className="flex-1 relative min-h-[380px] lg:min-h-0 mx-6 lg:mx-0 mb-8 lg:mb-0">
          <HeroFrame />
        </div>
      </section>

      {/* ── Features ──────────────────────────────────────── */}
      <section id="features" className="px-6 md:px-20 pt-20 pb-10 text-center">
        <Kicker>Our Pipeline</Kicker>
        <h2 className="font-serif font-medium text-3xl md:text-[42px] mt-3.5 mb-16 max-w-[560px] mx-auto leading-[1.3]">
          Everything in AI Video Captioning
        </h2>
        <div className="flex flex-wrap gap-6 justify-center items-start">
          {FEATURES.map((f, i) => (
            <Reveal key={f.num} delay={i * 120} className={i % 2 === 1 ? "md:mt-14" : ""}>
              <div className="lift bg-white w-[270px] px-6 pt-16 pb-6 relative text-left shadow-[0_14px_34px_rgba(203,86,120,0.12)]">
                <div
                  className={`absolute -top-6 -left-3.5 w-16 h-16 flex items-center justify-center text-[26px] shadow-[0_10px_24px_rgba(242,84,125,0.4)] ${
                    i % 2 === 1 ? "bg-white text-green" : "bg-pink text-white"
                  }`}
                >
                  {f.icon}
                </div>
                <h3 className="font-serif text-[19px] mb-3.5">{f.title}</h3>
                <p className="text-[13.5px] text-gray-500 leading-[1.75]">{f.text}</p>
                <span className="block text-right text-pink text-3xl font-bold mt-4">
                  {f.num}
                </span>
              </div>
            </Reveal>
          ))}
        </div>
      </section>

      {/* ── About ─────────────────────────────────────────── */}
      <section id="about" className="px-6 md:px-20 py-16">
        <Reveal>
          <div className="bg-white flex flex-col lg:flex-row shadow-[0_20px_50px_rgba(203,86,120,0.12)]">
            <div className="flex-[1.1] p-10 md:p-14">
              <h2 className="font-serif font-medium text-3xl md:text-[34px] mb-6">
                About CaptionDB
              </h2>
              <p className="text-gray-500 text-[14.5px] leading-[1.8] mb-4">
                CaptionDB is an AI captioning platform where creators upload
                videos and receive scene-by-scene captions written by vision
                language models. Our goal is to make video accessibility and
                content repurposing simple, fast and delightful.
              </p>
              <p className="text-gray-500 text-[14.5px] leading-[1.8] mb-8">
                Create a project, watch the pipeline process each stage live,
                then browse every scene with its transcript, tags and five
                caption styles — ready to copy or export.
              </p>
              <Link
                href="/dashboard"
                className="inline-block bg-pink hover:bg-pink-d text-white font-bold text-sm rounded px-7 py-3.5 shadow-[0_8px_20px_rgba(242,84,125,0.35)] transition-colors"
              >
                Explore Features
              </Link>
            </div>
            <div className="flex-1 relative min-h-[300px] lg:min-h-[380px] bg-gradient-to-br from-[#194f31] to-green-l">
              <div className="absolute top-14 right-14 text-[110px] opacity-25 anim-float">🎥</div>
              <div className="absolute left-0 bottom-11 bg-green-d text-white px-8 py-4 font-serif text-xl">
                Detect • Caption • Deliver
              </div>
            </div>
          </div>
        </Reveal>
      </section>

      {/* ── CTA banner ────────────────────────────────────── */}
      <section className="px-6 md:px-20 pb-20">
        <Reveal>
          <div className="bg-green-d flex flex-col md:flex-row items-center relative overflow-hidden">
            <div className="w-full md:w-[300px] h-[170px] bg-gradient-to-br from-green-l to-[#123c26] relative flex-shrink-0">
              <span className="absolute inset-0 flex items-center justify-center text-white/70 text-[34px]">▶</span>
            </div>
            <div className="hidden md:flex absolute left-[272px] top-1/2 -translate-y-1/2 w-[58px] h-[58px] bg-pink items-center justify-center text-white text-2xl shadow-[0_10px_24px_rgba(242,84,125,0.5)]">
              🎬
            </div>
            <h2 className="flex-1 text-white font-serif font-medium text-2xl md:text-[32px] px-8 md:pl-24 md:pr-14 py-8 md:py-0">
              Ready To Caption
              <br />
              Your First Video?
            </h2>
            <span className="absolute right-44 font-serif italic text-[64px] text-white/5 select-none hidden lg:inline">
              captions
            </span>
            <Link
              href="/upload"
              className="mb-8 md:mb-0 md:mr-12 bg-pink hover:bg-pink-d text-white font-bold text-sm rounded px-7 py-3.5 shadow-[0_8px_20px_rgba(242,84,125,0.4)] transition-colors relative z-10"
            >
              Upload Now
            </Link>
          </div>
        </Reveal>
      </section>

      {/* ── Tones ─────────────────────────────────────────── */}
      <section id="tones" className="px-6 md:px-20 pb-24 text-center">
        <Kicker>Caption Styles</Kicker>
        <h2 className="font-serif font-medium text-3xl md:text-[40px] mt-3.5 mb-14">
          Meet The Five Tones
        </h2>
        <div className="flex flex-wrap gap-5 justify-center">
          {TONES.map((t, i) => (
            <Reveal key={t.name} delay={i * 100}>
              <div className="lift bg-white w-[230px] text-left shadow-[0_14px_34px_rgba(203,86,120,0.12)]">
                <div
                  className={`h-[150px] flex items-center justify-center text-[44px] ${
                    t.pink
                      ? "bg-gradient-to-br from-pink to-[#f78ba7]"
                      : "bg-gradient-to-br from-[#1c6b40] to-[#39a56b]"
                  }`}
                >
                  {t.emoji}
                </div>
                <div className="bg-white relative -mt-6 mx-3.5 p-5 shadow-[0_-6px_18px_rgba(0,0,0,0.05)]">
                  <h3 className="font-serif text-lg">{t.name}</h3>
                  <span className="block text-pink text-xs font-bold mt-1.5">{t.label}</span>
                  <p className="text-[12.5px] text-gray-500 leading-relaxed mt-2.5 italic">
                    {t.sample}
                  </p>
                </div>
              </div>
            </Reveal>
          ))}
        </div>
      </section>

      {/* ── Footer ────────────────────────────────────────── */}
      <footer className="bg-ink text-[#cfcfcf] px-6 md:px-20 pt-16">
        <div className="flex flex-col md:flex-row gap-12 md:gap-20">
          <div className="flex-[1.2]">
            <Logo className="px-6 py-3 text-[17px]" />
            <p className="mt-5 max-w-[300px] text-[13.5px] leading-8 text-[#b9b9b9]">
              AI-powered scene detection and multi-tone caption generation for
              every video you create.
            </p>
            <h4 className="text-white font-serif text-lg mt-6 mb-4">Follow Us</h4>
            <div className="flex gap-3">
              {["𝕏", "f", "in", "▶"].map((s) => (
                <span
                  key={s}
                  className="w-9 h-9 rounded-full bg-[#1e1e1e] hover:bg-pink transition-colors flex items-center justify-center text-sm text-white cursor-pointer"
                >
                  {s}
                </span>
              ))}
            </div>
          </div>
          <div>
            <h4 className="text-white font-serif text-lg mb-5">Product</h4>
            <ul className="text-[13.5px] leading-8 text-[#b9b9b9]">
              <li><Link href="/upload" className="hover:text-pink">Upload Videos</Link></li>
              <li><Link href="/#features" className="hover:text-pink">Scene Detection</Link></li>
              <li><Link href="/#tones" className="hover:text-pink">Caption Tones</Link></li>
              <li><Link href="/dashboard" className="hover:text-pink">Dashboard</Link></li>
            </ul>
          </div>
          <div>
            <h4 className="text-white font-serif text-lg mb-5">Contact</h4>
            <ul className="text-[13.5px] leading-8 text-[#b9b9b9]">
              <li>📧 hello@captiondb.app</li>
              <li>📍 api/v1 · REST + OpenAPI</li>
            </ul>
            <h4 className="text-white font-serif text-lg mt-6 mb-4">Processing Hours</h4>
            <ul className="text-[13.5px] leading-8 text-[#b9b9b9]">
              <li>Always on — 24 / 7</li>
              <li className="text-pink">Avg. video: under 3 min</li>
            </ul>
          </div>
        </div>
        <div className="border-t border-[#262626] mt-12 py-6 text-center text-[12.5px] text-[#8a8a8a]">
          © All Copyright 2026 by CaptionDB
        </div>
      </footer>
    </main>
  );
}
