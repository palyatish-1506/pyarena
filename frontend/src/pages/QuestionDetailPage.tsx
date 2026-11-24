import { useEffect, useRef, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import confetti from "canvas-confetti";
import { api, type SubmitResult } from "../api";
import { CodeBlock } from "../components/CodeBlock";
import { Markdown } from "../components/Markdown";

export function QuestionDetailPage() {
  const { id } = useParams();
  const questionId = Number(id);
  const { data: q, isLoading, isError } = useQuery({
    queryKey: ["question", questionId],
    queryFn: () => api.question(questionId),
    enabled: Number.isFinite(questionId),
  });
  const [selected, setSelected] = useState<number[]>([]);
  const [result, setResult] = useState<SubmitResult | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState("");
  const startRef = useRef(Date.now());
  const [elapsed, setElapsed] = useState(0);

  // Timer ticks every second while unanswered.
  useEffect(() => {
    if (result) return;
    const t = setInterval(() => setElapsed(Math.floor((Date.now() - startRef.current) / 1000)), 1000);
    return () => clearInterval(t);
  }, [result]);

  // Confetti on correct answer.
  useEffect(() => {
    if (result?.is_correct) {
      confetti({ particleCount: 120, spread: 70, origin: { y: 0.6 } });
    }
  }, [result]);

  if (isLoading) return <p className="text-sm text-surface-800/60">Loading…</p>;
  if (isError || !q)
    return (
      <p className="text-sm text-error-500">
        Question not found. <Link to="/" className="underline">Back home</Link>
      </p>
    );

  const multi = q.type === "mcq_multi";

  function toggle(optId: number) {
    setSelected((prev) =>
      multi
        ? prev.includes(optId)
          ? prev.filter((x) => x !== optId)
          : [...prev, optId]
        : [optId],
    );
  }

  async function onSubmit() {
    setSubmitting(true);
    setSubmitError("");
    try {
      const res = await api.submitAnswer(questionId, selected, Date.now() - startRef.current);
      setResult(res);
    } catch (e) {
      const msg = (e as { response?: { status?: number } }).response?.status;
      setSubmitError(msg === 409 ? "You already answered this one." : "Submit failed — try again.");
    } finally {
      setSubmitting(false);
    }
  }

  const mm = String(Math.floor(elapsed / 60)).padStart(2, "0");
  const ss = String(elapsed % 60).padStart(2, "0");

  return (
    <article className="mx-auto max-w-2xl space-y-5">
      <div className="flex items-center justify-between text-sm text-surface-800/60">
        <span>{q.topic.name}</span>
        <span className="flex items-center gap-3 font-medium">
          <span className="tabular-nums">{mm}:{ss}</span>
          {q.difficulty} · {q.base_points} pts
        </span>
      </div>
      <h1 className="text-2xl font-bold">{q.title}</h1>
      <Markdown text={q.body_markdown} />
      {q.code_snippet && <CodeBlock code={q.code_snippet} />}

      {result ? (
        <ResultPanel result={result} />
      ) : (
        <>
          <div className="space-y-2">
            {q.options.map((opt) => (
              <button
                key={opt.id}
                onClick={() => toggle(opt.id)}
                className={`block w-full rounded-lg border px-4 py-3 text-left text-sm transition ${
                  selected.includes(opt.id)
                    ? "border-primary-500 bg-primary-50"
                    : "border-surface-200 bg-white hover:border-primary-300"
                }`}
              >
                {opt.text}
              </button>
            ))}
          </div>
          {submitError && <p className="text-sm text-error-500">{submitError}</p>}
          <button
            onClick={onSubmit}
            disabled={selected.length === 0 || submitting}
            className="rounded-lg bg-primary-600 px-6 py-2.5 font-medium text-white hover:bg-primary-700 disabled:opacity-40"
          >
            {submitting ? "Submitting…" : "Submit answer"}
          </button>
        </>
      )}
    </article>
  );
}

function ResultPanel({ result }: { result: SubmitResult }) {
  return (
    <div className="space-y-4 rounded-xl border border-surface-100 bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between">
        <p className={`text-lg font-bold ${result.is_correct ? "text-success-500" : "text-error-500"}`}>
          {result.is_correct ? "Correct!" : result.is_late ? "Practice answer" : "Not quite"}
        </p>
        <p className="text-sm text-surface-800/60">
          +{result.points_awarded} pts · XP {result.new_xp} · L{result.new_level} {result.level_name}
        </p>
      </div>
      {result.is_late && (
        <p className="rounded-lg bg-accent-400/20 px-3 py-2 text-sm">
          This question's window closed — it counted as practice (no points).
        </p>
      )}
      {result.streak > 0 && (
        <p className="text-sm text-surface-800/70">🔥 {result.streak}-day streak</p>
      )}
      {result.badges_earned.length > 0 && (
        <p className="text-sm font-medium text-accent-500">
          🏅 Badge earned: {result.badges_earned.join(", ")}
        </p>
      )}
      {result.explanation && (
        <div>
          <h3 className="mb-1 text-sm font-semibold">Explanation</h3>
          <Markdown text={result.explanation} />
        </div>
      )}
      <Link to="/" className="inline-block text-sm text-primary-600 underline">
        Back to today's challenges
      </Link>
    </div>
  );
}
