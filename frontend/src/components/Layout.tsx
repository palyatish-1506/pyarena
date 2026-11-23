import { NavLink, Outlet } from "react-router-dom";

const navLinkClass = ({ isActive }: { isActive: boolean }) =>
  `rounded-md px-3 py-2 text-sm font-medium transition-colors ${
    isActive
      ? "bg-primary-100 text-primary-700"
      : "text-surface-800 hover:bg-surface-100"
  }`;

export function Layout() {
  return (
    <div className="flex min-h-screen flex-col bg-surface-50 font-sans text-surface-900">
      <header className="border-b border-surface-100 bg-white">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
          <NavLink to="/" className="text-lg font-bold text-primary-600">
            PyArena
          </NavLink>
          <nav className="flex items-center gap-1">
            <NavLink to="/" end className={navLinkClass}>
              Home
            </NavLink>
            <NavLink to="/leaderboard" className={navLinkClass}>
              Leaderboard
            </NavLink>
          </nav>
        </div>
      </header>
      <main className="mx-auto w-full max-w-5xl flex-1 px-4 py-8">
        <Outlet />
      </main>
      <footer className="border-t border-surface-100 bg-white py-4 text-center text-xs text-surface-800/60">
        PyArena — learn Python by competing
      </footer>
    </div>
  );
}
