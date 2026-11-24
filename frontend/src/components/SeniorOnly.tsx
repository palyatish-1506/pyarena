import type { ReactElement } from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

/** Gate for senior/admin-only pages. Students get bounced home. */
export function SeniorOnly({ children }: { children: ReactElement }) {
  const { user } = useAuth();
  if (!user || (user.role !== "senior" && user.role !== "admin")) {
    return <Navigate to="/" replace />;
  }
  return children;
}
