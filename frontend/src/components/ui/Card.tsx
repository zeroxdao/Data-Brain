import { cn } from "@/lib/utils";

interface CardProps {
  className?: string;
  children: React.ReactNode;
  title?: string;
  action?: React.ReactNode;
}

export function Card({ className, children, title, action }: CardProps) {
  return (
    <div
      className={cn(
        "rounded-xl border border-[#30363d] bg-[#161b22] overflow-hidden",
        className
      )}
    >
      {title && (
        <div className="flex items-center justify-between px-5 py-3.5 border-b border-[#30363d]">
          <h3 className="text-sm font-semibold text-[#e6edf3]">{title}</h3>
          {action && <div className="flex items-center gap-2">{action}</div>}
        </div>
      )}
      <div className="p-5">{children}</div>
    </div>
  );
}

export function StatRow({
  label,
  value,
  valueClass,
}: {
  label: string;
  value: React.ReactNode;
  valueClass?: string;
}) {
  return (
    <div className="flex items-center justify-between py-1.5">
      <span className="text-xs text-[#8b949e]">{label}</span>
      <span className={cn("text-sm font-medium", valueClass)}>{value}</span>
    </div>
  );
}
