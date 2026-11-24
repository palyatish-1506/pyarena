import { useAuth } from "../auth/AuthContext";

/** Minimal profile page — proves protected routes + /me data work. */
export function ProfilePage() {
  const { user } = useAuth();
  if (!user) return null;

  return (
    <section className="mx-auto max-w-md space-y-4">
      <h1 className="text-2xl font-bold">{user.full_name || user.email}</h1>
      <dl className="space-y-2 rounded-xl border border-surface-100 bg-white p-5 text-sm">
        <div className="flex justify-between">
          <dt className="text-surface-800/60">Email</dt>
          <dd>{user.email}</dd>
        </div>
        <div className="flex justify-between">
          <dt className="text-surface-800/60">Role</dt>
          <dd className="capitalize">{user.role}</dd>
        </div>
        <div className="flex justify-between">
          <dt className="text-surface-800/60">Level</dt>
          <dd>
            {user.level} · {user.xp} XP
          </dd>
        </div>
        {user.division && (
          <div className="flex justify-between">
            <dt className="text-surface-800/60">Division</dt>
            <dd>{user.division}</dd>
          </div>
        )}
      </dl>
    </section>
  );
}
