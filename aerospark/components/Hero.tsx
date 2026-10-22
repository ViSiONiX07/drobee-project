// components/Hero.tsx
// Navbar + Hero section from the Stitch design (AeroSpark colors).
// Only real specs from the team's repo are used here.

const LINKS = [
  { label: "Explore", href: "#explore" },
  { label: "Docs", href: "#docs" },
  { label: "Download", href: "#download" },
  { label: "Team", href: "#team" },
];

const SPECS = [
  { label: "Weight", value: "46 g", note: "Total mass", accent: "cyan" },
  { label: "Brain", value: "XIAO ESP32-S3", note: "Dual-core MCU / Wi-Fi / BLE", accent: "cyan" },
  { label: "Altitude sensor", value: "VL53L0X", note: "Time-of-flight rangefinder", accent: "cyan" },
  { label: "Optical flow", value: "ADNS3080", note: "Surface motion tracker", accent: "amber" },
];

export function Navbar() {
  return (
    <header className="sticky top-0 z-50 border-b border-[#00F2FE]/15 bg-[#0A0D14]/80 backdrop-blur-md">
      <nav className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <a href="#top" className="text-lg font-bold tracking-wide text-[#F0F4F8]">
          Aero<span className="text-[#00F2FE]">Spark</span>
        </a>

        <ul className="hidden gap-8 text-sm text-[#64748B] md:flex">
          {LINKS.map((l) => (
            <li key={l.label}>
              <a href={l.href} className="transition-colors hover:text-[#00F2FE]">
                {l.label}
              </a>
            </li>
          ))}
        </ul>

        <a
          href="#download"
          className="rounded-md bg-[#00F2FE] px-4 py-2 text-sm font-semibold text-[#0A0D14] transition hover:shadow-[0_0_20px_#00F2FE66]"
        >
          Download
        </a>
      </nav>
    </header>
  );
}

export default function Hero() {
  return (
    <section id="top" className="relative overflow-hidden bg-[#0A0D14] px-6 pb-16 pt-20 text-center">
      {/* soft cyan glow behind the headline */}
      <div className="pointer-events-none absolute left-1/2 top-0 h-[420px] w-[720px] -translate-x-1/2 rounded-full bg-[#00F2FE]/10 blur-3xl" />

      <div className="relative mx-auto max-w-4xl">
        <span className="inline-flex items-center gap-2 rounded-full border border-[#00F2FE]/30 bg-[#121824]/80 px-4 py-1.5 font-mono text-xs tracking-widest text-[#00F2FE] backdrop-blur">
          <span className="h-2 w-2 rounded-full bg-[#00F2FE]" />
          AEROSPARK // 46 G MICRO-DRONE
        </span>

        <h1 className="mt-8 text-4xl font-extrabold uppercase leading-tight tracking-tight text-[#F0F4F8] md:text-6xl">
          The 46-gram <span className="text-[#00F2FE]">autonomous</span> micro-drone
        </h1>

        <p className="mx-auto mt-6 max-w-2xl text-base text-[#64748B] md:text-lg">
          Built around the XIAO ESP32-S3, with time-of-flight altitude sensing and
          optical-flow drift estimation.
        </p>

        <div className="mt-10 flex flex-wrap justify-center gap-4">
          <a
            href="#explore"
            className="rounded-md bg-[#00F2FE] px-6 py-3 font-semibold text-[#0A0D14] transition hover:shadow-[0_0_24px_#00F2FE66]"
          >
            Explore the build
          </a>
          <a
            href="#specs"
            className="rounded-md border border-[#FFB300]/60 px-6 py-3 font-semibold text-[#FFB300] transition hover:bg-[#FFB300]/10"
          >
            Technical specs
          </a>
        </div>

        <p className="mt-12 font-mono text-xs tracking-widest text-[#64748B]">
          SCROLL TO TAKE IT APART ↓
        </p>
      </div>
    </section>
  );
}

export function SpecChips() {
  return (
    <section id="specs" className="bg-[#0A0D14] px-6 py-16">
      <div className="mx-auto max-w-6xl">
        <p className="mb-6 font-mono text-xs tracking-widest text-[#00F2FE]">
          CORE SPECIFICATIONS
        </p>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {SPECS.map((s) => (
            <div
              key={s.label}
              className={`rounded-xl border bg-[#121824]/80 p-5 backdrop-blur ${
                s.accent === "amber" ? "border-[#FFB300]/40" : "border-[#00F2FE]/20"
              }`}
            >
              <p className="font-mono text-xs uppercase tracking-widest text-[#64748B]">
                {s.label}
              </p>
              <p className="mt-2 text-2xl font-bold text-[#F0F4F8]">{s.value}</p>
              <p className="mt-1 text-xs text-[#64748B]">{s.note}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
