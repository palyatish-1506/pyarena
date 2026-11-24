import { useQuery } from "@tanstack/react-query";
import { api } from "../api";
import { useAuth } from "../auth/AuthContext";

/** Profile page — stats + per-topic accuracy bars. */
export function ProfilePage() {
  const { user } = useAuth();
  const { data: topics } = useQuery({ queryKey: ["my-topics"], queryFn: api.myTopics });
  if (!user) return null;

  return (
    <section className="mx-auto max-w-md space-y-6">
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
        <div className="flex justify-between">
          <dt className="text-surface-800/60">Streak</dt>
          <dd>
            🔥 {user.current_streak} day{user.current_streak === 1 ? "" : "s"} (best {user.longest_streak}) · {user.streak_freezes} freeze{user.streak_freezes === 1 ? "" : "s"}
          </dd>
        </div>
        {user.division && (
          <div className="flex justify-between">
            <dt className="text-surface-800/60">Division</dt>
            <dd>{user.division}</dd>
          </div>
        )}
      </dl>

      {topics && topics.length > 0 && (
        <div className="rounded-xl border border-surface-100 bg-white p-5">
          <h2 className="mb-3 text-sm font-semibold">Topic progress</h2>
          <div className="space-y-3">
            {topics.map((t) => (
              <div key={t.topic}>
                <div className="mb-1 flex justify-between text-xs">
                  <span>{t.topic}</span>
                  <span className="text-surface-800/60">
                    {t.correct}/{t.attempts} · {t.accuracy}%
                  </span>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-surface-100">
                  <div
                    className={`h-full rounded-full ${t.accuracy >= 60 ? "bg-success-500" : "bg-accent-400"}`}
                    style={{ width: `${t.accuracy}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}
