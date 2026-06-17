"use client";
import { cn } from "@/lib/utils";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "danger" | "ghost" | "outline";
  size?: "sm" | "md";
  loading?: boolean;
}

const VARIANTS = {
  primary: "bg-[#238636] hover:bg-[#2ea043] text-white border-transparent",
  danger: "bg-[#da3633]/20 hover:bg-[#da3633]/30 text-red-400 border-[#da3633]/40",
  ghost: "bg-transparent hover:bg-white/5 text-[#8b949e] border-transparent",
  outline: "bg-transparent hover:bg-white/5 text-[#e6edf3] border-[#30363d]",
};

const SIZES = {
  sm: "px-3 py-1.5 text-xs",
  md: "px-4 py-2 text-sm",
};

export function Button({
  variant = "outline",
  size = "md",
  loading,
  className,
  disabled,
  children,
  ...props
}: ButtonProps) {
  return (
    <button
      disabled={disabled || loading}
      className={cn(
        "inline-flex items-center gap-1.5 rounded-lg border font-medium transition-colors",
        "disabled:opacity-50 disabled:cursor-not-allowed",
        VARIANTS[variant],
        SIZES[size],
        className
      )}
      {...props}
    >
      {loading && (
        <svg className="animate-spin h-3.5 w-3.5" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
        </svg>
      )}
      {children}
    </button>
  );
}
