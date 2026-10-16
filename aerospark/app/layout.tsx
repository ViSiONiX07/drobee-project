import type { Metadata } from "next";
import { Space_Grotesk, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const space = Space_Grotesk({ variable: "--font-space", subsets: ["latin"] });
const jetbrains = JetBrains_Mono({ variable: "--font-jetbrains", subsets: ["latin"] });

export const metadata: Metadata = {
  title: "AeroSpark | 46 g micro-drone",
  description:
    "AeroSpark: a 46-gram micro-drone built on the XIAO ESP32-S3 with time-of-flight altitude sensing and optical-flow drift estimation.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className={`${space.variable} ${jetbrains.variable} antialiased`}>
        {children}
      </body>
    </html>
  );
}
