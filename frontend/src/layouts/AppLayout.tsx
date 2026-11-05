import { useEffect, useState } from "react";
import { Link, NavLink } from "react-router-dom";
import type { ReactNode } from "react";

interface AppLayoutProps {
  children: ReactNode;
}

type Theme = "light" | "dark";

function initialTheme(): Theme {
  try {
    const stored = localStorage.getItem("bluetrace-theme");
    if (stored === "light" || stored === "dark") return stored;
  } catch {
    return "dark";
  }
  return "dark";
}

export function AppLayout({ children }: AppLayoutProps) {
  const [theme, setTheme] = useState<Theme>(initialTheme);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
    document.documentElement.style.colorScheme = theme;
    try {
      localStorage.setItem("bluetrace-theme", theme);
    } catch {
      // Browser storage may be unavailable; theme still works for this session.
    }
  }, [theme]);

  return (
    <div className="min-h-screen text-research-ink transition-colors duration-300 dark:text-slate-100">
      <header className="sticky top-0 z-40 border-b border-white/70 bg-white/78 backdrop-blur-xl dark:border-cyan-400/10 dark:bg-slate-950/80">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-3 px-5 py-4 sm:px-8">
          <Link className="group flex items-center gap-3 font-semibold tracking-tight text-research-ink dark:text-white" to="/">
            <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-gradient-to-br from-cyan-400 via-ocean-600 to-indigo-600 text-sm text-white shadow-lg shadow-cyan-500/20 transition-transform group-hover:rotate-6">BT</span>
            <span>BlueTrace <span className="text-ocean-600 dark:text-cyan-300">AI</span></span>
          </Link>
          <nav aria-label="Primary navigation" className="flex items-center gap-2">
            <NavLink className={({ isActive }) => [
                "rounded-full px-4 py-2 text-sm font-medium transition",
                isActive
                  ? "bg-ocean-50 text-ocean-700 dark:bg-cyan-400/15 dark:text-cyan-200"
                  : "text-research-muted hover:bg-white hover:text-research-ink dark:text-slate-300 dark:hover:bg-white/10 dark:hover:text-white"
              ].join(" ")} to="/analysis">
              Analysis
            </NavLink>
            <button
              aria-label={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
              aria-pressed={theme === "dark"}
              className="inline-flex h-10 items-center gap-2 rounded-full border border-research-line bg-white/80 px-3 text-sm font-medium text-research-ink transition hover:border-ocean-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-cyan-400 dark:border-white/15 dark:bg-white/5 dark:text-slate-100 dark:hover:bg-white/10"
              onClick={() => setTheme((current) => current === "dark" ? "light" : "dark")}
              type="button"
            >
              <span aria-hidden="true">{theme === "dark" ? "☀" : "☾"}</span>
              <span className="hidden sm:inline">{theme === "dark" ? "Light" : "Dark"}</span>
            </button>
          </nav>
        </div>
      </header>
      <main>{children}</main>
      <footer className="border-t border-research-line bg-white/70 dark:border-white/10 dark:bg-slate-950/60">
        <div className="mx-auto flex max-w-7xl flex-col gap-2 px-5 py-6 text-sm text-research-muted sm:flex-row sm:items-center sm:justify-between sm:px-8 dark:text-slate-400">
          <p>BlueTrace AI · California Coast</p>
          <p>Experimental marine debris research</p>
        </div>
      </footer>
    </div>
  );
}
