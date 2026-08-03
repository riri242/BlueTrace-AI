import type { ButtonHTMLAttributes } from "react";

type ButtonVariant = "primary" | "secondary" | "ghost";
type ButtonSize = "md" | "lg";

interface ButtonStyleOptions {
  variant?: ButtonVariant;
  size?: ButtonSize;
  className?: string;
}

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  isLoading?: boolean;
  variant?: ButtonVariant;
  size?: ButtonSize;
}

export function buttonStyles({
  variant = "primary",
  size = "md",
  className = ""
}: ButtonStyleOptions = {}) {
  const base =
    "inline-flex items-center justify-center rounded-full font-semibold transition duration-200 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 disabled:cursor-not-allowed disabled:opacity-55";
  const variants: Record<ButtonVariant, string> = {
    primary:
      "bg-ocean-600 text-white shadow-lg shadow-ocean-600/20 hover:bg-ocean-700 focus-visible:outline-ocean-500",
    secondary:
      "border border-research-line bg-white text-research-ink hover:border-ocean-500 hover:text-ocean-700 focus-visible:outline-ocean-500",
    ghost:
      "text-research-muted hover:bg-ocean-50 hover:text-ocean-700 focus-visible:outline-ocean-500"
  };
  const sizes: Record<ButtonSize, string> = {
    md: "min-h-11 px-5 text-sm",
    lg: "min-h-12 px-7 text-base"
  };

  return [base, variants[variant], sizes[size], className]
    .filter(Boolean)
    .join(" ");
}

export function Button({
  children,
  className,
  disabled,
  isLoading = false,
  size,
  type = "button",
  variant,
  ...props
}: ButtonProps) {
  return (
    <button
      className={buttonStyles({ variant, size, className })}
      disabled={disabled || isLoading}
      type={type}
      {...props}
    >
      {isLoading ? "Working..." : children}
    </button>
  );
}

