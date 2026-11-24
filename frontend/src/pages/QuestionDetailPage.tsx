import { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api";
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

  return (
    <article className="mx-auto max-w-2xl space-y-5">
      <div className="flex items-center justify-between text-sm text-surface-800/60">
        <span>{q.topic.name}</span>
        <span className="font-medium">
          {q.difficulty} · {q.base_points} pts
        </span>
      </div>
      <h1 className="text-2xl font-bold">{q.title}</h1>
      <Markdown text={q.body_markdown} />
      {q.code_snippet && <CodeBlock code={q.code_snippet} />}

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

      <button
        disabled={selected.length === 0}
        className="rounded-lg bg-primary-600 px-6 py-2.5 font-medium text-white hover:bg-primary-700 disabled:opacity-40"
      >
        Submit answer
      </button>
      <p className="text-xs text-surface-800/50">
        Submissions arrive in the next milestone — for now this is read-only.
      </p>
    </article>
  );
}
