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
      ? "border-ocean-100 bg-ocean-50/65"
      : "border-research-line bg-white/88";

  return (
    <div
      className={[
        "rounded-2xl border p-5 shadow-research backdrop-blur sm:p-6",
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

