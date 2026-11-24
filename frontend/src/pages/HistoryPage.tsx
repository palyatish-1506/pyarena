import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api";

export function HistoryPage() {
  const [page, setPage] = useState(1);
  const { data, isLoading } = useQuery({
    queryKey: ["history", page],
    queryFn: () => api.myHistory(page),
  });

  return (
    <section className="mx-auto max-w-2xl space-y-4">
      <h1 className="text-2xl font-bold">Your history</h1>
      {isLoading && <p className="text-sm text-surface-800/60">Loading…</p>}
      {data && data.results.length === 0 && (
        <p className="rounded-xl border border-dashed border-surface-200 p-6 text-center text-sm text-surface-800/60">
          No submissions yet — answer a question to see it here.
        </p>
      )}
      <ul className="space-y-2">
        {data?.results.map((h) => (
          <li key={h.id} className="flex items-center justify-between rounded-xl border border-surface-100 bg-white p-4">
            <div>
              <Link to={`/questions/${h.question}`} className="font-medium hover:underline">
                {h.question_title}
              </Link>
              <p className="text-xs text-surface-800/60">
                {h.topic_name} · {h.difficulty}
                {h.is_late && " · practice"}
              </p>
            </div>
            <div className="text-right text-sm">
              <p className={h.is_correct ? "font-semibold text-success-500" : "font-semibold text-error-500"}>
                {h.is_correct ? "✓ Correct" : "✗ Wrong"}
              </p>
              <p className="text-xs text-surface-800/60">+{h.points} pts</p>
            </div>
          </li>
        ))}
      </ul>
      {data && (data.next || data.previous) && (
        <div className="flex gap-2">
          <button
            disabled={!data.previous}
            onClick={() => setPage((p) => p - 1)}
            className="rounded-lg border border-surface-200 px-4 py-2 text-sm disabled:opacity-40"
          >
            ← Newer
          </button>
          <button
            disabled={!data.next}
            onClick={() => setPage((p) => p + 1)}
            className="rounded-lg border border-surface-200 px-4 py-2 text-sm disabled:opacity-40"
          >
            Older →
          </button>
        </div>
      )}
    </section>
  );
}
