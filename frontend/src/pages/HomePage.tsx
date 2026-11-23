import { useQuery } from "@tanstack/react-query";
import { api } from "../api";

export function HomePage() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["health"],
    queryFn: api.health,
  });

  return (
    <section className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Welcome to PyArena</h1>
        <p className="mt-2 text-surface-800/70">
          Practice Python with quizzes, earn XP, and climb the leaderboard.
        </p>
      </div>

      <div className="rounded-xl border border-surface-100 bg-white p-5 shadow-sm">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-surface-800/60">
          Backend status
        </h2>
        {isLoading && <p className="mt-2 text-sm">Checking…</p>}
        {isError && (
          <p className="mt-2 text-sm text-error-500">
            Backend unreachable — is <code>manage.py runserver</code> running?
          </p>
        )}
        {data && (
          <p className="mt-2 text-sm font-medium text-success-500" role="status">
            Backend connected {data.db === "ok" ? "✓" : "(db error)"}
          </p>
        )}
      </div>
    </section>
  );
}
