// components/Download.tsx
import React from "react";

const DOWNLOADS = [
  { os: "Windows", icon: "🪟", href: "#", version: "v1.0.2", ext: ".exe" },
  { os: "macOS", icon: "🍎", href: "#", version: "v1.0.2", ext: ".dmg" },
  { os: "Linux", icon: "🐧", href: "#", version: "v1.0.2", ext: ".tar.gz" },
];

export default function Download() {
  return (
    <section id="download" className="relative bg-[#0A0D14] px-6 py-24">
      <div className="bg-grid bg-grid-fade pointer-events-none absolute inset-0 opacity-40" />
      <div className="relative mx-auto max-w-4xl text-center">
        <p className="font-mono text-xs tracking-widest text-[#00F2FE]">GET STARTED</p>
        <h2 className="mt-3 text-3xl font-bold text-[#F0F4F8] md:text-4xl">
          Download AeroSpark
        </h2>
        <p className="mx-auto mt-4 max-w-xl text-sm text-[#64748B] md:text-base">
          Get the latest build of the AeroSpark flight controller and ground station
          software for your platform.
        </p>

        <div className="mt-12 grid gap-6 sm:grid-cols-3">
          {DOWNLOADS.map((d) => (
            <a
              key={d.os}
              href={d.href}
              className="glow-card group relative block rounded-2xl border border-[#00F2FE]/20 bg-[#121824]/80 p-8 text-center backdrop-blur transition-all hover:border-[#00F2FE]/50 hover:shadow-[0_0_30px_#00F2FE33]"
            >
              <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-[#00F2FE]/10 text-2xl transition-colors group-hover:bg-[#00F2FE]/20">
                {d.icon}
              </div>
              <h3 className="text-xl font-bold text-[#F0F4F8]">{d.os}</h3>
              <p className="mt-1 font-mono text-xs text-[#64748B]">
                {d.version} {d.ext}
              </p>
              <div className="mt-6 inline-flex items-center gap-2 rounded-lg bg-[#00F2FE] px-4 py-2 text-sm font-bold text-[#0A0D14] transition-transform group-hover:scale-105">
                Download <span>↓</span>
              </div>
            </a>
          ))}
        </div>
      </div>
    </section>
  );
}
