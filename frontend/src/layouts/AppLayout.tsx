import { Link, NavLink } from "react-router-dom";
import type { ReactNode } from "react";

interface AppLayoutProps {
  children: ReactNode;
}

export function AppLayout({ children }: AppLayoutProps) {
  return (
    <div className="min-h-screen text-research-ink">
      <header className="sticky top-0 z-40 border-b border-white/70 bg-white/78 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-4 sm:px-8">
          <Link
            className="flex items-center gap-3 font-semibold tracking-tight text-research-ink"
            to="/"
          >
            <span className="flex h-9 w-9 items-center justify-center rounded-full bg-ocean-600 text-sm text-white">
              BT
            </span>
            <span>BlueTrace AI</span>
          </Link>
          <nav aria-label="Primary navigation" className="flex items-center gap-2">
            <NavLink
              className={({ isActive }) =>
                [
                  "rounded-full px-4 py-2 text-sm font-medium transition",
                  isActive
                    ? "bg-ocean-50 text-ocean-700"
                    : "text-research-muted hover:bg-white hover:text-research-ink"
                ].join(" ")
              }
              to="/analysis"
            >
              Analysis
            </NavLink>
          </nav>
        </div>
      </header>

      <main>{children}</main>

      <footer className="border-t border-research-line bg-white/70">
        <div className="mx-auto flex max-w-7xl flex-col gap-2 px-5 py-6 text-sm text-research-muted sm:flex-row sm:items-center sm:justify-between sm:px-8">
          <p>BlueTrace AI research foundation.</p>
          <p>Milestone 1 intake workflow.</p>
        </div>
      </footer>
    </div>
  );
}
