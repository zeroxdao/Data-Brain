"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  BrainCircuit,
  BarChart3,
  Activity,
  BookOpen,
  Settings,
} from "lucide-react";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/", label: "总览", icon: LayoutDashboard },
  { href: "/orchestrator", label: "调度大脑", icon: BrainCircuit },
  { href: "/analysis", label: "EA 分析", icon: BarChart3 },
  { href: "/regime", label: "市场环境", icon: Activity },
  { href: "/log", label: "决策日志", icon: BookOpen },
];

export function Sidebar() {
  const path = usePathname();
  return (
    <aside className="fixed inset-y-0 left-0 w-56 flex flex-col border-r border-[#30363d] bg-[#0d1117] z-20">
      {/* Logo */}
      <div className="flex items-center gap-2.5 px-5 h-16 border-b border-[#30363d] shrink-0">
        <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-[#58a6ff] to-[#bc8cff] flex items-center justify-center">
          <BrainCircuit className="w-4 h-4 text-white" />
        </div>
        <div>
          <div className="text-sm font-bold text-[#e6edf3] leading-none">DATA BRAIN</div>
          <div className="text-[10px] text-[#8b949e] mt-0.5">AI 交易大脑</div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 py-4 px-3 space-y-0.5 overflow-y-auto">
        {NAV.map(({ href, label, icon: Icon }) => {
          const active = path === href;
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors",
                active
                  ? "bg-[#58a6ff]/10 text-[#58a6ff] font-medium"
                  : "text-[#8b949e] hover:text-[#e6edf3] hover:bg-white/5"
              )}
            >
              <Icon className="w-4 h-4 shrink-0" />
              {label}
            </Link>
          );
        })}
      </nav>

      {/* Bottom */}
      <div className="px-3 py-4 border-t border-[#30363d]">
        <Link
          href="/settings"
          className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-[#8b949e] hover:text-[#e6edf3] hover:bg-white/5 transition-colors"
        >
          <Settings className="w-4 h-4" />
          设置
        </Link>
      </div>
    </aside>
  );
}
