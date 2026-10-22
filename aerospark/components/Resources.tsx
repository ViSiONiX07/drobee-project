// components/Resources.tsx — Footer (website-only project)

const REPO = "https://github.com/ViSiONiX07/drobee-project";

export function Footer() {
  return (
    <footer className="border-t border-[#00F2FE]/15 bg-[#0A0D14] px-6 py-8">
      <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-2 font-mono text-xs tracking-widest text-[#64748B] sm:flex-row">
        <span>AEROSPARK // 46 G MICRO-DRONE</span>
        <a href={REPO} target="_blank" rel="noopener noreferrer" className="transition-colors hover:text-[#00F2FE]">
          GITHUB
        </a>
      </div>
    </footer>
  );
}
