import Docs from "@/components/Docs";
import { Navbar } from "@/components/HeroV2";
import { Footer } from "@/components/Resources";

export default function DocsPage() {
  return (
    <main className="bg-[#0A0D14] text-[#F0F4F8] min-h-screen">
      <Navbar />
      <Docs />
      <Footer />
    </main>
  );
}
