import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api";

/** Senior-only live quiz creator — pick questions, get a room code. */
export function LiveQuizCreator() {
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [title, setTitle] = useState("Live Quiz");
  const [timeLimit, setTimeLimit] = useState(20);
  const [code, setCode] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const { data: questions } = useQuery({
    queryKey: ["senior-questions-all"],
    queryFn: () => api.seniorQuestions(),
  });

  const list = Array.isArray(questions) ? questions : (questions as { results?: unknown[] })?.results ?? [];

  function toggle(id: number) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  }

  async function create() {
    if (selected.size === 0) return;
    setBusy(true);
    setError("");
    try {
      const res = await api.createLiveQuiz(title, [...selected], timeLimit);
      setCode(res.code);
    } catch {
      setError("Couldn't create the quiz — make sure you're an approved senior.");
    } finally {
      setBusy(false);
    }
  }

  if (code) {
    return (
      <div className="rounded-xl border border-success-500/40 bg-success-500/10 p-5 text-center">
        <p className="text-sm text-surface-800/70">Room code — share with players:</p>
        <p className="my-2 text-4xl font-bold tracking-[0.3em]">{code}</p>
        <div className="flex justify-center gap-3">
          <Link to={`/live/${code}`} className="rounded-lg bg-primary-600 px-5 py-2 font-medium text-white">
            Open host screen
          </Link>
          <button onClick={() => { setCode(null); setSelected(new Set()); }} className="text-sm underline">
            Create another
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-3 rounded-xl border border-surface-100 bg-white p-5">
      <h2 className="font-semibold">🎮 Create Live Quiz</h2>
      <div className="flex gap-2">
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Quiz title"
          className="flex-1 rounded-lg border border-surface-200 px-3 py-2 text-sm"
        />
        <select
          value={timeLimit}
          onChange={(e) => setTimeLimit(Number(e.target.value))}
          className="rounded-lg border border-surface-200 px-2 py-2 text-sm"
        >
          {[10, 15, 20, 30, 45, 60].map((t) => (
            <option key={t} value={t}>{t}s</option>
          ))}
        </select>
      </div>

      <div className="max-h-56 space-y-1 overflow-y-auto">
        {(list as { id: number; title: string; status: string }[]).map((q) => (
          <label key={q.id} className="flex cursor-pointer items-center gap-2 rounded-lg px-2 py-1.5 text-sm hover:bg-surface-50">
            <input type="checkbox" checked={selected.has(q.id)} onChange={() => toggle(q.id)} />
            <span className="flex-1 truncate">{q.title}</span>
            <span className="text-xs text-surface-800/50">{q.status}</span>
          </label>
        ))}
        {(list as unknown[]).length === 0 && (
          <p className="text-sm text-surface-800/60">No questions yet — create some first.</p>
        )}
      </div>

      {error && <p className="text-sm text-error-500">{error}</p>}
      <button
        onClick={create}
        disabled={selected.size === 0 || busy}
        className="rounded-lg bg-primary-600 px-5 py-2 font-medium text-white hover:bg-primary-700 disabled:opacity-40"
      >
        {busy ? "Creating…" : `Create room (${selected.size} questions)`}
      </button>
    </div>
  );
}
