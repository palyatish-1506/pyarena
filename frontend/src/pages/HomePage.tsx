import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api, type StudentQuestion } from "../api";
import { useAuth } from "../auth/AuthContext";

const difficultyColor: Record<string, string> = {
  easy: "bg-success-500/10 text-success-500",
  medium: "bg-accent-400/30 text-surface-900",
  hard: "bg-error-500/10 text-error-500",
};

function QuestionCard({ q }: { q: StudentQuestion }) {
  return (
    <Link
      to={`/questions/${q.id}`}
      className="block rounded-xl border border-surface-100 bg-white p-4 shadow-sm transition hover:border-primary-300"
    >
      <div className="flex items-center justify-between gap-2">
        <span className="text-xs font-medium text-surface-800/60">{q.topic.name}</span>
        <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${difficultyColor[q.difficulty]}`}>
          {q.difficulty} · {q.base_points} pts
        </span>
      </div>
      <h3 className="mt-2 font-semibold">{q.title}</h3>
      <p className="mt-1 line-clamp-2 text-sm text-surface-800/70">{q.body_markdown}</p>
    </Link>
  );
}

export function HomePage() {
  const { user } = useAuth();
  const { data: health } = useQuery({ queryKey: ["health"], queryFn: api.health });
  const { data: questions, isLoading } = useQuery({
    queryKey: ["today-questions"],
    queryFn: api.todayQuestions,
    enabled: !!user, // students only — anonymous sees the health card
  });

  return (
    <section className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">
          {user ? `Welcome back, ${user.full_name || user.email}` : "Welcome to PyArena"}
        </h1>
        <p className="mt-2 text-surface-800/70">
          Practice Python with quizzes, earn XP, and climb the leaderboard.
        </p>
      </div>

      {user && (
        <div className="flex gap-3 text-sm">
          <span className="rounded-full bg-primary-50 px-3 py-1 font-medium text-primary-700">
            ⚡ {user.xp} XP
          </span>
          <span className="rounded-full bg-surface-100 px-3 py-1 font-medium">
            Level {user.level}
          </span>
          <span className="rounded-full bg-accent-400/30 px-3 py-1 font-medium">
            🔥 {user.current_streak}-day streak
          </span>
        </div>
      )}

      {user && (
        <div>
          <h2 className="mb-3 text-lg font-semibold">Today's Challenge</h2>
          {isLoading && <p className="text-sm text-surface-800/60">Loading questions…</p>}
          {questions?.length === 0 && (
            <p className="rounded-xl border border-dashed border-surface-200 bg-white p-6 text-center text-sm text-surface-800/60">
              No challenges yet today — check back soon!
            </p>
          )}
          <div className="grid gap-3 sm:grid-cols-2">
            {questions?.map((q) => <QuestionCard key={q.id} q={q} />)}
          </div>
        </div>
      )}

      <div className="rounded-xl border border-surface-100 bg-white p-5 shadow-sm">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-surface-800/60">
          Backend status
        </h2>
        {health && (
          <p className="mt-2 text-sm font-medium text-success-500" role="status">
            Backend connected {health.db === "ok" ? "✓" : "(db error)"}
          </p>
        )}
      </div>
    </section>
  );
}
