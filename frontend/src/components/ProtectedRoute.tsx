import type { ReactElement } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

/**
 * Wraps routes that require login. While the session check is in flight we
 * render nothing (avoids a flash of protected content); anonymous users are
 * redirected to /login with the intended destination preserved.
 */
export function ProtectedRoute({ children }: { children: ReactElement }) {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return <div className="py-12 text-center text-sm text-surface-800/60">Loading…</div>;
  }
  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }
  return children;
}
