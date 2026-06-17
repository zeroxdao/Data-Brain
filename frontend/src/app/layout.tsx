import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { Sidebar } from "@/components/dashboard/Sidebar";
import { SWRProvider } from "@/components/SWRProvider";

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

export const metadata: Metadata = {
  title: "DATA BRAIN — AI 交易大脑",
  description: "AI/ML 驱动的 CFD 交易分析、策略调度与风控平台",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN" className="dark">
      <body className={`${geistSans.variable} ${geistMono.variable} antialiased bg-[#0d1117]`}>
        <SWRProvider>
          <Sidebar />
          <main className="ml-56 min-h-screen flex flex-col">{children}</main>
        </SWRProvider>
      </body>
    </html>
  );
}
