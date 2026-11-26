import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api";

export function ProblemsPage() {
  const { data: problems } = useQuery({ queryKey: ["code-problems"], queryFn: api.codeProblems });
  return (
    <div className="mx-auto max-w-3xl space-y-4 p-4">
      <h1 className="text-2xl font-bold">💻 Code Problems</h1>
      <p className="text-sm text-surface-800/60">Solve problems in the browser — practice free, earn points on server-graded submissions.</p>
      <div className="space-y-2">
        {(problems ?? []).map((p) => (
          <Link key={p.id} to={`/problems/${p.slug}`} className="block rounded-xl border border-surface-100 bg-white p-4 shadow-sm hover:border-primary-300">
            <div className="flex items-center justify-between">
              <h2 className="font-semibold">{p.title}</h2>
              <span className="text-sm font-bold text-primary-600">{p.points} pts</span>
            </div>
            <p className="mt-1 text-xs text-surface-800/60 capitalize">{p.difficulty} · {p.hidden_test_count} hidden tests</p>
          </Link>
        ))}
        {problems?.length === 0 && <p className="text-sm text-surface-800/60">No problems published yet.</p>}
      </div>
    </div>
  );
}
