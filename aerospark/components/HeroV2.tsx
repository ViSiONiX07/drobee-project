 "use client";
import { useState } from "react";

const LINKS = [
  { label: "Explore", href: "#explore" },
  { label: "Docs", href: "/docs" },
  { label: "Resources", href: "#resources" },
];

const SPECS = [
  { n: "01", label: "Weight", value: "46 g", note: "Total mass", accent: "cyan" },
  { n: "02", label: "Brain", value: "XIAO ESP32-S3", note: "Dual-core MCU / Wi-Fi / BLE", accent: "cyan" },
  { n: "03", label: "Altitude sensor", value: "VL53L0X", note: "Time-of-flight rangefinder", accent: "cyan" },
  { n: "04", label: "Optical flow", value: "ADNS3080", note: "Surface motion tracker", accent: "amber" },
];

const TICKER = ["XIAO ESP32-S3", "VL53L0X TOF", "ADNS3080 FLOW", "4× 8520 MOTORS", "1S LIPO", "20-50 HZ DATA"];

export function Navbar() {
  const [showDownloads, setShowDownloads] = useState(false);

  return (
    <header className="sticky top-0 z-50 border-b border-[#00F2FE]/15 bg-[#0A0D14]/80 backdrop-blur-md">
      <nav className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <a href="#top" className="flex items-center gap-2 text-lg font-bold tracking-wide text-[#F0F4F8]">
          <span className="inline-block h-2.5 w-2.5 rounded-full bg-[#00F2FE] shadow-[0_0_12px_#00F2FE]" />
          <span>Aero<span className="text-[#00F2FE]">Spark</span></span>
        </a>
        <ul className="hidden gap-8 font-mono text-xs uppercase tracking-widest text-[#64748B] md:flex">
          {LINKS.map((l) => (
            <li key={l.label}>
              <a href={l.href} className="transition-colors hover:text-[#00F2FE]">{l.label}</a>
            </li>
          ))}
        </ul>
        <div className="relative flex items-center gap-4">
          {/* Download Dropdown */}
          <div className="relative">
            <button
              onClick={() => setShowDownloads(!showDownloads)}
              className="hidden sm:flex items-center gap-2 rounded-md border border-[#00F2FE]/30 bg-[#121824]/80 px-4 py-2 text-sm font-semibold text-[#F0F4F8] transition hover:bg-[#00F2FE]/10 hover:border-[#00F2FE]"
            >
              <span className="text-[#00F2FE]">↓</span> Download
            </button>

            {showDownloads && (
              <div className="absolute right-0 mt-2 w-48 rounded-xl border border-[#00F2FE]/20 bg-[#121824] p-2 shadow-2xl backdrop-blur-xl animate-in fade-in zoom-in-95 duration-100">
                <div className="flex flex-col gap-1">
                  {[
                    { os: "Windows", icon: "🪟", href: "#win" },
                    { os: "macOS", icon: "🍎", href: "#mac" },
                    { os: "Linux", icon: "🐧", href: "#lin" },
                  ].map((item) => (
                    <a
                      key={item.os}
                      href={item.href}
                      className="flex items-center justify-between rounded-lg px-3 py-2 text-sm text-[#F0F4F8] transition-colors hover:bg-[#00F2FE]/10 hover:text-[#00F2FE]"
                    >
                      <span className="flex items-center gap-2">
                        <span>{item.icon}</span> {item.os}
                      </span>
                      <span className="text-[10px] opacity-50">.exe</span>
                    </a>
                  ))}
                </div>
              </div>
            )}
          </div>

          <a
            href="https://github.com/ViSiONiX07/drobee-project"
            target="_blank"
            rel="noopener noreferrer"
            className="rounded-md bg-[#00F2FE] px-4 py-2 text-sm font-semibold text-[#0A0D14] transition hover:shadow-[0_0_24px_#00F2FE80]"
          >
            GitHub
          </a>
        </div>
      </nav>
      <ul className="flex gap-6 overflow-x-auto px-6 pb-3 font-mono text-[11px] uppercase tracking-widest text-[#64748B] md:hidden">
        {LINKS.map((l) => (
          <li key={l.label}>
            <a href={l.href} className="whitespace-nowrap transition-colors hover:text-[#00F2FE]">{l.label}</a>
          </li>
        ))}
      </ul>
    </header>
  );
}

export default function Hero() {
  return (
    <section id="top" className="relative overflow-hidden bg-[#0A0D14] px-6 pb-14 pt-24 text-center">
      <div className="bg-grid bg-grid-fade pointer-events-none absolute inset-0" />
      <div className="pointer-events-none absolute left-1/2 top-10 h-[460px] w-[760px] -translate-x-1/2 rounded-full bg-[#00F2FE]/10 blur-3xl" />
      <div className="pointer-events-none absolute inset-x-0 top-0 h-full overflow-hidden">
        <div className="scanline h-24 w-full bg-gradient-to-b from-transparent via-[#00F2FE]/10 to-transparent" />
      </div>

      <div className="relative mx-auto max-w-4xl">
        <span className="inline-flex items-center gap-2 rounded-full border border-[#00F2FE]/30 bg-[#121824]/80 px-4 py-1.5 font-mono text-xs tracking-widest text-[#00F2FE] backdrop-blur">
          <span className="h-2 w-2 animate-pulse rounded-full bg-[#00F2FE]" />
          AEROSPARK // 46 G MICRO-DRONE
        </span>

        <h1 className="mt-8 text-balance text-4xl font-bold uppercase leading-[1.05] tracking-tight text-[#F0F4F8] md:text-7xl">
          The 46-gram{" "}
          <span className="bg-gradient-to-r from-[#00F2FE] to-[#7df9ff] bg-clip-text text-transparent">
            autonomous
          </span>{" "}
          <span className="whitespace-nowrap">micro-drone</span>
        </h1>

        <p className="mx-auto mt-6 max-w-2xl text-base text-[#94a3b8] md:text-lg">
          Built around the XIAO ESP32-S3, with time-of-flight altitude sensing and
          optical-flow drift estimation.
        </p>

        <div className="mt-10 flex flex-wrap justify-center gap-4">
          <a
            href="/docs#build"
            className="rounded-md bg-[#00F2FE] px-7 py-3 font-semibold text-[#0A0D14] transition hover:shadow-[0_0_28px_#00F2FE80]"
          >
            Explore the build
          </a>
          <a
            href="#specs"
            className="rounded-md border border-[#FFB300]/60 px-7 py-3 font-semibold text-[#FFB300] transition hover:bg-[#FFB300]/10"
          >
            Technical specs
          </a>
        </div>
      </div>

      <div className="relative mx-auto mt-16 flex max-w-5xl flex-wrap justify-center gap-x-8 gap-y-2 border-y border-[#00F2FE]/15 py-3 font-mono text-[11px] tracking-widest text-[#64748B]">
        {TICKER.map((t) => (
          <span key={t} className="flex items-center gap-2">
            <span className="h-1 w-1 rounded-full bg-[#FFB300]" />
            {t}
          </span>
        ))}
      </div>

      <p className="relative mt-10 font-mono text-xs tracking-widest text-[#64748B]">
        SCROLL TO TAKE IT APART ↓
      </p>
    </section>
  );
}

export function SpecChips() {
  return (
    <section id="specs" className="relative bg-[#0A0D14] px-6 py-20">
      <div className="bg-grid bg-grid-fade pointer-events-none absolute inset-0 opacity-60" />
      <div className="relative mx-auto max-w-6xl">
        <p className="mb-6 font-mono text-xs tracking-widest text-[#00F2FE]">// CORE SPECIFICATIONS</p>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {SPECS.map((s) => (
            <div
              key={s.label}
              className={`glow-card rounded-xl border bg-[#121824]/80 p-5 backdrop-blur ${
                s.accent === "amber" ? "border-[#FFB300]/40" : "border-[#00F2FE]/20"
              }`}
            >
              <div className="flex items-center justify-between">
                <p className="font-mono text-xs uppercase tracking-widest text-[#64748B]">{s.label}</p>
                <span className={`font-mono text-xs ${s.accent === "amber" ? "text-[#FFB300]" : "text-[#00F2FE]"}`}>
                  {s.n}
                </span>
              </div>
              <p className="mt-3 text-2xl font-bold text-[#F0F4F8]">{s.value}</p>
              <p className="mt-1 text-xs text-[#64748B]">{s.note}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
