import { useMemo, useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, type QuestionPayload, type SeniorQuestion, type Topic } from "../api";
import { istLocalToUtcIso, utcIsoToIstLocal } from "../lib/time";
import { CodeBlock } from "../components/CodeBlock";
import { Markdown } from "../components/Markdown";

const inputClass = "w-full rounded-lg border border-surface-200 px-3 py-2 text-sm";
const labelClass = "mb-1 block text-sm font-medium";

interface OptionDraft {
  text: string;
  is_correct: boolean;
}

const STATUS_TABS = ["all", "draft", "scheduled", "published", "archived"] as const;

export function SeniorDashboardPage() {
  const qc = useQueryClient();
  const [tab, setTab] = useState<(typeof STATUS_TABS)[number]>("all");
  const [editing, setEditing] = useState<SeniorQuestion | null>(null);
  const [previewId, setPreviewId] = useState<number | null>(null);

  const { data: topics = [] } = useQuery({ queryKey: ["topics"], queryFn: api.topics });
  const { data: questions = [] } = useQuery({
    queryKey: ["senior-questions", tab],
    queryFn: () => api.seniorQuestions(tab === "all" ? undefined : tab),
  });

  function refresh() {
    void qc.invalidateQueries({ queryKey: ["senior-questions"] });
  }

  return (
    <section className="space-y-6">
      <h1 className="text-2xl font-bold">Senior dashboard</h1>

      <QuestionBuilder
        key={editing?.id ?? "new"}
        topics={topics}
        editing={editing}
        onDone={() => {
          setEditing(null);
          refresh();
        }}
      />

      <div>
        <div className="mb-3 flex gap-2">
          {STATUS_TABS.map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`rounded-full px-3 py-1 text-xs font-medium capitalize ${
                tab === t ? "bg-primary-600 text-white" : "bg-surface-100 text-surface-800"
              }`}
            >
              {t}
            </button>
          ))}
        </div>
        <ul className="space-y-2">
          {questions.map((q) => (
            <li
              key={q.id}
              className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-surface-100 bg-white p-4"
            >
              <div>
                <p className="font-medium">{q.title}</p>
                <p className="text-xs text-surface-800/60">
                  {q.topic.name} · {q.difficulty} · {q.status}
                  {q.release_at && ` · live ${new Date(q.release_at).toLocaleString("en-IN", { timeZone: "Asia/Kolkata" })} IST`}
                </p>
              </div>
              <div className="flex gap-2 text-sm">
                <button onClick={() => setEditing(q)} className="text-primary-600 hover:underline">
                  Edit
                </button>
                <button onClick={() => setPreviewId(previewId === q.id ? null : q.id)} className="text-primary-600 hover:underline">
                  Preview
                </button>
                <DuplicateButton id={q.id} onDone={refresh} />
              </div>
            </li>
          ))}
          {questions.length === 0 && (
            <li className="rounded-xl border border-dashed border-surface-200 p-6 text-center text-sm text-surface-800/60">
              No questions in this view yet.
            </li>
          )}
        </ul>
        {previewId !== null && <StudentPreview questionId={previewId} />}
      </div>
    </section>
  );
}

function DuplicateButton({ id, onDone }: { id: number; onDone: () => void }) {
  const mut = useMutation({ mutationFn: () => api.duplicateQuestion(id), onSuccess: onDone });
  return (
    <button onClick={() => mut.mutate()} className="text-primary-600 hover:underline">
      Duplicate
    </button>
  );
}

function StudentPreview({ questionId }: { questionId: number }) {
  const { data: q, isLoading } = useQuery({
    queryKey: ["preview", questionId],
    queryFn: () => api.previewQuestion(questionId),
  });
  if (isLoading) return <p className="mt-4 text-sm">Loading preview…</p>;
  if (!q) return null;
  return (
    <div className="mt-4 rounded-xl border border-accent-400/50 bg-accent-400/10 p-5">
      <p className="mb-2 text-xs font-semibold uppercase text-surface-800/60">
        Student preview (answers hidden)
      </p>
      <h3 className="font-semibold">{q.title}</h3>
      <div className="mt-2"><Markdown text={q.body_markdown} /></div>
      {q.code_snippet && <div className="mt-3"><CodeBlock code={q.code_snippet} /></div>}
      <ul className="mt-3 space-y-1">
        {q.options.map((o) => (
          <li key={o.id} className="rounded border border-surface-200 bg-white px-3 py-2 text-sm">
            {o.text}
          </li>
        ))}
      </ul>
    </div>
  );
}

function QuestionBuilder({
  topics,
  editing,
  onDone,
}: {
  topics: Topic[];
  editing: SeniorQuestion | null;
  onDone: () => void;
}) {
  const [title, setTitle] = useState(editing?.title ?? "");
  const [topicId, setTopicId] = useState<number | "">(editing?.topic_id ?? "");
  const [type, setType] = useState(editing?.type ?? "mcq_single");
  const [difficulty, setDifficulty] = useState(editing?.difficulty ?? "easy");
  const [body, setBody] = useState(editing?.body_markdown ?? "");
  const [code, setCode] = useState(editing?.code_snippet ?? "");
  const [explanation, setExplanation] = useState(editing?.explanation_markdown ?? "");
  const [releaseAt, setReleaseAt] = useState(utcIsoToIstLocal(editing?.release_at ?? null));
  const [options, setOptions] = useState<OptionDraft[]>(
    editing?.options?.length
      ? editing.options.map((o) => ({ text: o.text, is_correct: o.is_correct }))
      : [
          { text: "", is_correct: true },
          { text: "", is_correct: false },
        ],
  );
  const [error, setError] = useState("");

  const payload = useMemo<QuestionPayload | null>(() => {
    if (!title.trim() || !body.trim() || !topicId || options.some((o) => !o.text.trim())) return null;
    return {
      topic_id: Number(topicId),
      type,
      title: title.trim(),
      body_markdown: body,
      code_snippet: code,
      difficulty,
      explanation_markdown: explanation,
      release_at: istLocalToUtcIso(releaseAt),
      options_input: options.map((o) => ({ text: o.text.trim(), is_correct: o.is_correct })),
    };
  }, [title, body, topicId, type, difficulty, code, explanation, releaseAt, options]);

  const save = useMutation({
    mutationFn: (p: QuestionPayload) =>
      editing ? api.updateQuestion(editing.id, p) : api.createQuestion(p),
    onSuccess: onDone,
    onError: (e) => setError(e instanceof Error ? e.message : "Save failed"),
  });

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    if (!payload) {
      setError("Fill title, topic, body and every option text.");
      return;
    }
    save.mutate(payload);
  }

  function setOpt(i: number, patch: Partial<OptionDraft>) {
    setOptions((opts) => opts.map((o, j) => (j === i ? { ...o, ...patch } : o)));
  }

  const correctCount = options.filter((o) => o.is_correct).length;

  return (
    <form onSubmit={onSubmit} className="rounded-xl border border-surface-100 bg-white p-5 shadow-sm">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="font-semibold">{editing ? `Edit: ${editing.title}` : "New question"}</h2>
        {editing && (
          <button type="button" onClick={onDone} className="text-sm text-surface-800/60 hover:underline">
            Cancel edit
          </button>
        )}
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <div className="sm:col-span-2">
          <label htmlFor="q-title" className={labelClass}>Title</label>
          <input id="q-title" value={title} onChange={(e) => setTitle(e.target.value)} className={inputClass} placeholder="e.g. What does range(5) produce?" />
        </div>
        <div>
          <label htmlFor="q-topic" className={labelClass}>Topic</label>
          <select id="q-topic" value={topicId} onChange={(e) => setTopicId(Number(e.target.value))} className={inputClass}>
            <option value="">Choose…</option>
            {topics.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
          </select>
        </div>
        <div>
          <label htmlFor="q-type" className={labelClass}>Type</label>
          <select id="q-type" value={type} onChange={(e) => setType(e.target.value as typeof type)} className={inputClass}>
            <option value="mcq_single">Single choice</option>
            <option value="mcq_multi">Multiple choice</option>
            <option value="output">Predict the output</option>
          </select>
        </div>
        <div>
          <label htmlFor="q-difficulty" className={labelClass}>Difficulty</label>
          <select id="q-difficulty" value={difficulty} onChange={(e) => setDifficulty(e.target.value as typeof difficulty)} className={inputClass}>
            <option value="easy">Easy (10 pts)</option>
            <option value="medium">Medium (20 pts)</option>
            <option value="hard">Hard (30 pts)</option>
          </select>
        </div>
        <div>
          <label htmlFor="q-release" className={labelClass}>Publish at (IST)</label>
          <input id="q-release" type="datetime-local" value={releaseAt} onChange={(e) => setReleaseAt(e.target.value)} className={inputClass} />
          <p className="mt-1 text-xs text-surface-800/50">Leave empty for draft. Times are Asia/Kolkata.</p>
        </div>
      </div>

      <div className="mt-4">
        <label htmlFor="q-body" className={labelClass}>Question (markdown)</label>
        <textarea id="q-body" value={body} onChange={(e) => setBody(e.target.value)} rows={3} className={inputClass} placeholder="What does this code print? **Think carefully.**" />
      </div>
      <div className="mt-3">
        <label htmlFor="q-code" className={labelClass}>Code snippet (optional)</label>
        <textarea id="q-code" value={code} onChange={(e) => setCode(e.target.value)} rows={4} className={`${inputClass} font-mono`} placeholder={"for i in range(5):\n    print(i)"} />
      </div>
      <div className="mt-3">
        <label htmlFor="q-expl" className={labelClass}>Explanation shown after submit (optional)</label>
        <textarea id="q-expl" value={explanation} onChange={(e) => setExplanation(e.target.value)} rows={2} className={inputClass} />
      </div>

      <div className="mt-4">
        <div className="mb-2 flex items-center justify-between">
          <label className={labelClass + " mb-0"}>
            Options {type === "mcq_single" ? "(pick exactly 1 correct)" : type === "mcq_multi" ? "(pick all correct)" : "(pick correct outputs)"}
          </label>
          <button
            type="button"
            onClick={() => setOptions((o) => [...o, { text: "", is_correct: false }])}
            className="text-sm text-primary-600 hover:underline"
          >
            + Add option
          </button>
        </div>
        <div className="space-y-2">
          {options.map((o, i) => (
            <div key={i} className="flex items-center gap-2">
              <input
                type={type === "mcq_multi" ? "checkbox" : "radio"}
                name="correct"
                checked={o.is_correct}
                onChange={() =>
                  setOptions((opts) =>
                    opts.map((x, j) => ({
                      ...x,
                      is_correct: type === "mcq_multi" ? (j === i ? !x.is_correct : x.is_correct) : j === i,
                    })),
                  )
                }
                className="h-4 w-4"
              />
              <input
                value={o.text}
                onChange={(e) => setOpt(i, { text: e.target.value })}
                className={inputClass}
                placeholder={`Option ${i + 1}`}
              />
              {options.length > 2 && (
                <button type="button" onClick={() => setOptions((opts) => opts.filter((_, j) => j !== i))} className="text-error-500">
                  ×
                </button>
              )}
            </div>
          ))}
        </div>
        {type === "mcq_single" && correctCount !== 1 && (
          <p className="mt-1 text-xs text-error-500">Single choice needs exactly 1 correct option.</p>
        )}
      </div>

      {error && <p className="mt-3 text-sm text-error-500">{error}</p>}
      <button
        type="submit"
        disabled={save.isPending || !payload}
        className="mt-4 rounded-lg bg-primary-600 px-6 py-2.5 font-medium text-white hover:bg-primary-700 disabled:opacity-40"
      >
        {save.isPending ? "Saving…" : editing ? "Save changes" : releaseAt ? "Schedule question" : "Save draft"}
      </button>
    </form>
  );
}
