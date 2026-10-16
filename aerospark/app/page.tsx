import DroneScene from "@/components/drone/DroneScene";
import Hero, { Navbar, SpecChips } from "@/components/HeroV2";
import Resources, { Footer } from "@/components/Resources";
import Download from "@/components/Download";

export default function Home() {
  return (
    <main className="bg-[#0A0D14] text-[#F0F4F8]">
      <Navbar />
      <Hero />
      <div id="explore">
        <DroneScene />
      </div>
      <SpecChips />
      <Download />
      <Footer />
    </main>
  );
}
