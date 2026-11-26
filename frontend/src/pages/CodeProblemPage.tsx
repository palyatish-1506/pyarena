import { useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { EditorView, basicSetup } from "codemirror";
import { EditorState } from "@codemirror/state";
import { python } from "@codemirror/lang-python";
import { oneDark } from "@codemirror/theme-one-dark";
import { api } from "../api";
import { Markdown } from "../components/Markdown";

const RUN_TIMEOUT_MS = 5000;

export function CodeProblemPage() {
  const { slug } = useParams();
  const { data: problem } = useQuery({
    queryKey: ["code-problem", slug],
    queryFn: () => api.codeProblem(slug!),
    enabled: !!slug,
  });

  const hostRef = useRef<HTMLDivElement>(null);
  const viewRef = useRef<EditorView | null>(null);
  const workerRef = useRef<Worker | null>(null);
  const [code, setCode] = useState("");
  const [stdout, setStdout] = useState("");
  const [stderr, setStderr] = useState("");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<{
    status: string; score: number; points_possible: number;
    error_hint: string; flagged_similar: boolean; message: string;
  } | null>(null);
  const [testResults, setTestResults] = useState<{ input: string; expected: string; actual: string; passed: boolean }[]>([]);

  // Lazy-init worker + editor once problem loads.
  useEffect(() => {
    if (!problem || !hostRef.current || viewRef.current) return;
    setCode(problem.starter_code);
    const worker = new Worker(new URL("../workers/pyodide.worker.ts", import.meta.url), );
    workerRef.current = worker;
    worker.onmessage = (e) => {
      if (e.data.type === "result") {
        setStdout(e.data.stdout);
        setStderr(e.data.stderr);
        setBusy(false);
      } else if (e.data.type === "error") {
        setStderr(e.data.stderr);
        setBusy(false);
      }
    };
    worker.postMessage({ type: "init" });
    const view = new EditorView({
      state: EditorState.create({
        doc: problem.starter_code,
        extensions: [basicSetup, python(), oneDark, EditorView.updateListener.of((u: { docChanged: boolean; state: EditorState }) => {
          if (u.docChanged) setCode(u.state.doc.toString());
        })],
      }),
      parent: hostRef.current,
    });
    viewRef.current = view;
    return () => { view.destroy(); worker.terminate(); };
  }, [problem]);

  function runWithTimeout(stdin: string): Promise<{ stdout: string; stderr: string }> {
    return new Promise((resolve) => {
      const w = workerRef.current!;
      const timer = setTimeout(() => {
        // C1: kill runaway code — terminate worker, spin up a fresh one.
        w.terminate();
        const fresh = new Worker(new URL("../workers/pyodide.worker.ts", import.meta.url), );
        workerRef.current = fresh;
        fresh.onmessage = (e) => {
          if (e.data.type === "result") { setStdout(e.data.stdout); setStderr(e.data.stderr); setBusy(false); }
        };
        fresh.postMessage({ type: "init" });
        resolve({ stdout: "", stderr: "⏱ Time limit exceeded (5s) — infinite loop killed." });
      }, RUN_TIMEOUT_MS);
      const handler = (e: MessageEvent) => {
        if (e.data.type === "result" || e.data.type === "error") {
          clearTimeout(timer);
          w.removeEventListener("message", handler);
          resolve(e.data.type === "result" ? { stdout: e.data.stdout, stderr: e.data.stderr } : { stdout: "", stderr: e.data.stderr });
        }
      };
      w.addEventListener("message", handler);
      w.postMessage({ type: "run", code, stdin });
    });
  }

  async function runVisibleTests() {
    if (!problem) return;
    setBusy(true);
    setTestResults([]);
    const results: typeof testResults = [];
    for (const t of problem.visible_tests) {
      const r = await runWithTimeout(t.input);
      results.push({ input: t.input, expected: t.expected_output, actual: r.stdout.trim(), passed: r.stdout.trim() === t.expected_output.trim() && !r.stderr });
      setTestResults([...results]);
    }
    setBusy(false);
  }

  async function submitForGrade() {
    if (!slug) return;
    setBusy(true);
    try {
      const r = await api.submitCode(slug, code);
      setResult(r);
    } finally {
      setBusy(false);
    }
  }

  if (!problem) return <p className="p-6">Loading…</p>;

  return (
    <div className="mx-auto max-w-5xl space-y-4 p-4">
      <div>
        <h1 className="text-2xl font-bold">{problem.title}</h1>
        <p className="text-sm text-surface-800/60">{problem.difficulty} · {problem.points} pts · {problem.hidden_test_count} hidden test(s)</p>
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-xl border border-surface-100 bg-white p-4">
          <Markdown text={problem.description_markdown} />
          <h3 className="mt-4 text-sm font-semibold">Visible tests</h3>
          {problem.visible_tests.map((t) => (
            <div key={t.id} className="mt-2 rounded-lg bg-surface-50 p-3 text-xs">
              <p className="font-mono">input: {JSON.stringify(t.input)}</p>
              <p className="font-mono">expected: {JSON.stringify(t.expected_output)}</p>
            </div>
          ))}
        </div>
        <div className="space-y-3">
          <div ref={hostRef} className="overflow-hidden rounded-xl border border-surface-200" />
          <div className="flex gap-2">
            <button onClick={runVisibleTests} disabled={busy} className="rounded-lg bg-surface-700 px-4 py-2 text-sm font-medium text-white disabled:opacity-40">
              {busy ? "Running…" : "▶ Run visible tests"}
            </button>
            <button onClick={submitForGrade} disabled={busy} className="rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-40">
              Submit for points
            </button>
          </div>
          {(stdout || stderr) && (
            <div className="rounded-xl bg-surface-900 p-3 font-mono text-xs text-white">
              {stderr && <pre className="text-error-400">{stderr}</pre>}
              <pre>{stdout}</pre>
            </div>
          )}
          {testResults.length > 0 && (
            <div className="space-y-1 text-xs">
              {testResults.map((t, i) => (
                <p key={i} className={t.passed ? "text-success-500" : "text-error-500"}>
                  Test {i + 1}: {t.passed ? "✓" : `✗ got ${JSON.stringify(t.actual)}`}
                </p>
              ))}
            </div>
          )}
          {result && (
            <div className={`rounded-xl border p-4 text-sm ${result.status === "accepted" ? "border-success-500/40 bg-success-500/10" : "border-error-500/40 bg-error-500/10"}`}>
              <p className="font-bold">{result.status === "accepted" ? `✅ +${result.score} points!` : `❌ ${result.status.replace(/_/g, " ")}`}</p>
              {result.error_hint && <p className="mt-1 text-surface-800/80">💡 {result.error_hint}</p>}
              {result.message && <p className="mt-1 text-amber-600">⚠️ {result.message}</p>}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
