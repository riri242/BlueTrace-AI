import type { HTMLAttributes } from "react";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  tone?: "default" | "soft";
}

export function Card({
  children,
  className = "",
  tone = "default",
  ...props
}: CardProps) {
  const toneClass =
    tone === "soft"
      ? "border-ocean-100 bg-ocean-50/65 dark:border-cyan-300/15 dark:bg-cyan-950/35"
      : "border-research-line bg-white/88 dark:border-white/10 dark:bg-slate-900/80";

  return (
    <div
      className={[
        "rounded-2xl border p-5 shadow-research backdrop-blur transition-colors duration-300 sm:p-6 dark:shadow-black/30",
        toneClass,
        className
      ]
        .filter(Boolean)
        .join(" ")}
      {...props}
    >
      {children}
    </div>
  );
}

