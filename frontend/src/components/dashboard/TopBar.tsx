"use client";
import { RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/Button";

interface TopBarProps {
  title: string;
  subtitle?: string;
  onRefresh?: () => void;
  children?: React.ReactNode;
}

export function TopBar({ title, subtitle, onRefresh, children }: TopBarProps) {
  return (
    <header className="h-16 border-b border-[#30363d] flex items-center px-6 gap-4 bg-[#0d1117]">
      <div className="flex-1 min-w-0">
        <h1 className="text-base font-semibold text-[#e6edf3] truncate">{title}</h1>
        {subtitle && (
          <p className="text-xs text-[#8b949e] truncate">{subtitle}</p>
        )}
      </div>
      <div className="flex items-center gap-2 shrink-0">
        {children}
        {onRefresh && (
          <Button size="sm" variant="ghost" onClick={onRefresh} title="刷新">
            <RefreshCw className="w-3.5 h-3.5" />
          </Button>
        )}
      </div>
    </header>
  );
}
