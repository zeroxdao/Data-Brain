import { cn } from "@/lib/utils";

interface BadgeProps {
  children: React.ReactNode;
  className?: string;
  variant?: "default" | "green" | "red" | "yellow" | "purple" | "blue";
}

const VARIANTS = {
  default: "bg-white/5 border-white/10 text-[#8b949e]",
  green: "bg-green-500/10 border-green-500/30 text-green-400",
  red: "bg-red-500/10 border-red-500/30 text-red-400",
  yellow: "bg-yellow-500/10 border-yellow-500/30 text-yellow-400",
  purple: "bg-purple-500/10 border-purple-500/30 text-purple-400",
  blue: "bg-blue-500/10 border-blue-500/30 text-blue-400",
};

export function Badge({ children, className, variant = "default" }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border",
        VARIANTS[variant],
        className
      )}
    >
      {children}
    </span>
  );
}
