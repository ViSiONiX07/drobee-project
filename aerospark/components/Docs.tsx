// components/Docs.tsx
// Documentation section.

const REPO = "https://github.com/ViSiONiX07/drobee-project";

const BUILD_ITEMS = [
  { n: "01", title: "Firmware", note: "ESP32-S3 flight code", href: `${REPO}/tree/main/firmware` },
  { n: "02", title: "Docs", note: "Pin mapping, technical spec, research notes", href: `${REPO}/tree/main/docs` },
  { n: "03", title: "CAD", note: "Frame design and print files", href: `${REPO}/tree/main/cad` },
  { n: "04", title: "Simulation", note: "Webots simulation of the drone", href: `${REPO}/tree/main/simulation` },
];

const NAV = [
  { label: "Build it yourself", href: "#build" },
  { label: "License", href: "#license" },
];

function Table({ head, rows }: { head: string[]; rows: string[][] }) {
  return (
    <div className="overflow-x-auto rounded-xl border border-[#00F2FE]/20 bg-[#121824]/80 backdrop-blur glow-card">
      <table className="w-full min-w-[640px] text-left text-sm">
        <thead>
          <tr className="border-b border-[#00F2FE]/20 font-mono text-xs uppercase tracking-widest text-[#00F2FE]">
            {head.map((h) => (
              <th key={h} className="px-4 py-3 font-medium">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody className="text-[#F0F4F8]">
          {rows.map((r, i) => (
            <tr key={i} className="border-b border-white/5 last:border-0">
              {r.map((c, j) => (
                <td
                  key={j}
                  className={`px-4 py-3 ${j === 0 ? "font-mono text-[#FFB300]" : "text-[#F0F4F8]/90"}`}
                >
                  {c}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function Docs() {
  return (
    <section id="docs" className="bg-[#0A0D14] px-6 py-24">
      <div className="mx-auto max-w-6xl">
        <p className="font-mono text-xs tracking-widest text-[#00F2FE]">DOCUMENTATION</p>
        <h2 className="mt-3 text-3xl font-bold text-[#F0F4F8] md:text-4xl">
          Project Resources
        </h2>

        <div className="mt-12 grid gap-10 md:grid-cols-[180px_1fr]">
          {/* sidebar */}
          <aside className="hidden md:block">
            <ul className="sticky top-24 space-y-3 border-l border-[#00F2FE]/20 pl-4 text-sm text-[#64748B]">
              {NAV.map((n) => (
                <li key={n.label}>
                  <a href={n.href} className="transition-colors hover:text-[#00F2FE]">
                    {n.label}
                  </a>
                </li>
              ))}
            </ul>
          </aside>

          <div className="min-w-0 space-y-16">
            {/* build it yourself */}
            <div id="build" className="scroll-mt-24">
              <h3 className="text-xl font-semibold text-[#F0F4F8]">Build it yourself</h3>
              <p className="mb-6 mt-2 text-sm text-[#64748B]">
                Everything behind AeroSpark is in one open repository: firmware, documentation, CAD
                files and simulation.
              </p>
              <div className="grid gap-4 sm:grid-cols-2">
                {BUILD_ITEMS.map((i) => (
                  <a
                    key={i.title}
                    href={i.href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="glow-card block rounded-xl border border-[#00F2FE]/20 bg-[#121824]/80 p-6 backdrop-blur"
                  >
                    <div className="flex items-center justify-between">
                      <p className="font-mono text-xs uppercase tracking-widest text-[#64748B]">Folder</p>
                      <span className="font-mono text-xs text-[#00F2FE]">{i.n}</span>
                    </div>
                    <p className="mt-3 text-xl font-bold text-[#F0F4F8]">{i.title}</p>
                    <p className="mt-1 text-sm text-[#64748B]">{i.note}</p>
                    <p className="mt-6 font-mono text-xs tracking-widest text-[#00F2FE]">OPEN ON GITHUB →</p>
                  </a>
                ))}
              </div>
            </div>

            {/* license */}
            <div id="license" className="scroll-mt-24">
              <h3 className="text-xl font-semibold text-[#F0F4F8]">License</h3>
              <div className="mt-4 rounded-xl border border-[#00F2FE]/20 bg-[#121824]/80 p-6 backdrop-blur glow-card">
                <p className="text-sm leading-relaxed text-[#64748B]">
                  This project is licensed under the <a href={`${REPO}/blob/main/LICENSE`} target="_blank" rel="noopener noreferrer" className="text-[#00F2FE] hover:underline">MIT License</a>.
                  Feel free to use, modify, and distribute the code and designs for your own drone projects.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
