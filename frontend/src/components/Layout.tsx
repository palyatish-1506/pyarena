import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

const navLinkClass = ({ isActive }: { isActive: boolean }) =>
  `rounded-md px-3 py-2 text-sm font-medium transition-colors ${
    isActive ? "bg-primary-100 text-primary-700" : "text-surface-800 hover:bg-surface-100"
  }`;

export function Layout() {
  const { user, loading, logout } = useAuth();

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
            {!loading &&
              (user ? (
                <>
                  {(user.role === "senior" || user.role === "admin") && (
                    <NavLink to="/senior" className={navLinkClass}>
                      Senior
                    </NavLink>
                  )}
                  <NavLink to="/profile" className={navLinkClass}>
                    {user.full_name || user.email}
                  </NavLink>
                  <button
                    onClick={() => void logout()}
                    className="rounded-md px-3 py-2 text-sm font-medium text-surface-800 hover:bg-surface-100"
                  >
                    Log out
                  </button>
                </>
              ) : (
                <>
                  <NavLink to="/login" className={navLinkClass}>
                    Log in
                  </NavLink>
                  <NavLink
                    to="/register"
                    className="rounded-md bg-primary-600 px-3 py-2 text-sm font-medium text-white hover:bg-primary-700"
                  >
                    Sign up
                  </NavLink>
                </>
              ))}
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
