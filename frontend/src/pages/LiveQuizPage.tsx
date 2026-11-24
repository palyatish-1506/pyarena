import { useEffect, useRef, useState } from "react";
import { useParams, useSearchParams } from "react-router-dom";
import { apiClient } from "../api/client";
import { getAccessToken } from "../api/client";
import { useAuth } from "../auth/AuthContext";

/** Live quiz player screen (phone) + host controls when is_host. */
interface QuizOption { id: number; text: string; order: number }
interface LeaderRow { rank: number; name: string; score: number; correct: number }
interface QuizQuestion {
  id: number; index: number; total: number; time_limit: number;
  title: string; body_markdown: string; code_snippet: string;
  options: QuizOption[];
}
interface QuizMessage {
  event: string;
  role?: string;
  quiz?: { code: string; title: string; status: string; current_index: number; question_count: number; time_limit: number };
  question?: QuizQuestion;
  index?: number; total?: number;
  correct_option_ids?: number[];
  explanation?: string;
  scores?: { user_id: number; points: number; correct: boolean }[];
  leaderboard?: LeaderRow[];
}
interface RoomInfo {
  code: string; title: string; status: string; host_name: string;
  player_count: number; players: LeaderRow[]; is_host: boolean;
}

export function LiveQuizPage() {
  const { code } = useParams();
  const [params] = useSearchParams();
  const joinCode = params.get("join") || code || "";
  const { user } = useAuth();
  const [msg, setMsg] = useState<QuizMessage | null>(null);
  const [selected, setSelected] = useState<number[]>([]);
  const [info, setInfo] = useState<RoomInfo | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const startRef = useRef(Date.now());

  useEffect(() => {
    if (!user || !joinCode) return;
    const token = getAccessToken() ?? "";
    connect(token);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user, joinCode]);

  function connect(token: string) {
    // WS base: VITE_WS_URL if set (prod), else dev backend on :8000.
    const base =
      import.meta.env.VITE_WS_URL ??
      `${location.protocol === "https:" ? "wss" : "ws"}://${location.hostname}:8000`;
    const ws = new WebSocket(`${base}/ws/quiz/${joinCode}/?token=${token}`);
    wsRef.current = ws;
    ws.onmessage = (e) => {
      const data = JSON.parse(e.data) as QuizMessage;
      setMsg(data);
      if (data.event === "question") {
        setSelected([]);
        startRef.current = Date.now();
      }
      if (data.event === "state" || data.event === "finished") {
        apiClient.get(`/api/v1/live/${joinCode}/`).then((r) => setInfo(r.data)).catch(() => {});
      }
    };
  }

  function send(action: string, extra: Record<string, unknown> = {}) {
    wsRef.current?.send(JSON.stringify({ action, ...extra }));
  }

  function answer() {
    send("answer", { option_ids: selected, time_taken_ms: Date.now() - startRef.current });
  }

  if (!user) return <p className="p-6">Log in to join a live quiz.</p>;

  const q = msg?.event === "question" ? msg.question : null;
  const reveal = msg?.event === "reveal" ? msg : null;
  const finished = msg?.event === "finished" ? msg : null;
  const state = msg?.event === "state" ? msg : null;
  const isHost = state?.role === "host" || info?.is_host;

  return (
    <div className="mx-auto max-w-2xl space-y-4 p-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">Room {joinCode}</h1>
        {info && <span className="text-sm text-surface-800/60">{info.player_count} players</span>}
      </div>

      {isHost && (
        <div className="flex gap-2 rounded-xl bg-surface-100 p-3">
          <button onClick={() => send("start")} className="rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white">Start</button>
          <button onClick={() => send("next")} className="rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white">Next</button>
          <button onClick={() => send("reveal")} className="rounded-lg bg-accent-400 px-4 py-2 text-sm font-medium">Reveal</button>
          <button onClick={() => send("end")} className="rounded-lg bg-error-500 px-4 py-2 text-sm font-medium text-white">End</button>
        </div>
      )}

      {finished && (
        <div className="rounded-xl border border-surface-100 bg-white p-5">
          <h2 className="mb-3 text-lg font-bold">🏆 Final podium</h2>
          <ol className="space-y-2">
            {finished.leaderboard?.map((p: LeaderRow, i: number) => (
              <li key={i} className="flex justify-between rounded-lg bg-surface-50 px-4 py-2">
                <span>#{p.rank} {p.name}</span>
                <span className="font-bold">{p.score} pts · {p.correct}✓</span>
              </li>
            ))}
          </ol>
        </div>
      )}

      {reveal && !finished && (
        <div className="rounded-xl border border-success-500/30 bg-success-500/10 p-5">
          <p className="font-semibold">Answer: {[...reveal.correct_option_ids].join(", ")}</p>
          {reveal.explanation && <p className="mt-2 text-sm">{reveal.explanation}</p>}
        </div>
      )}

      {q && !reveal && !finished && (
        <div className="space-y-3 rounded-xl border border-surface-100 bg-white p-5">
          <p className="text-xs text-surface-800/60">Question {q.index + 1}/{q.total} · {q.time_limit}s</p>
          <h2 className="text-lg font-semibold">{q.title}</h2>
          <pre className="whitespace-pre-wrap text-sm">{q.body_markdown}</pre>
          {q.code_snippet && <pre className="rounded-lg bg-surface-900 p-3 text-sm text-white">{q.code_snippet}</pre>}
          <div className="space-y-2">
            {q.options.map((o: QuizOption) => (
              <button
                key={o.id}
                onClick={() => setSelected([o.id])}
                className={`block w-full rounded-lg border px-4 py-3 text-left text-sm ${
                  selected.includes(o.id) ? "border-primary-500 bg-primary-50" : "border-surface-200"
                }`}
              >
                {o.text}
              </button>
            ))}
          </div>
          <button onClick={answer} disabled={selected.length === 0} className="rounded-lg bg-primary-600 px-6 py-2 font-medium text-white disabled:opacity-40">
            Lock answer
          </button>
        </div>
      )}

      {!q && !finished && (
        <p className="rounded-xl border border-dashed border-surface-200 p-6 text-center text-sm text-surface-800/60">
          Waiting for the host to start…
        </p>
      )}

      {state?.leaderboard && state.leaderboard.length > 0 && (
        <div className="rounded-xl border border-surface-100 bg-white p-4 text-sm">
          <p className="mb-2 font-semibold">Top players</p>
          {state.leaderboard.slice(0, 5).map((p: LeaderRow) => (
            <p key={p.rank}>#{p.rank} {p.name} — {p.score}</p>
          ))}
        </div>
      )}
    </div>
  );
}
