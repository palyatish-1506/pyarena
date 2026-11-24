import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api, type Comment } from "../api";
import { useAuth } from "../auth/AuthContext";

/** Comments thread — only rendered after the user submitted the question. */
export function CommentsSection({ questionId }: { questionId: number }) {
  const { user } = useAuth();
  const qc = useQueryClient();
  const [body, setBody] = useState("");
  const [replyTo, setReplyTo] = useState<number | null>(null);
  const [error, setError] = useState("");

  const { data, isLoading, isError } = useQuery({
    queryKey: ["comments", questionId],
    queryFn: () => api.comments(questionId),
  });

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!body.trim()) return;
    setError("");
    try {
      await api.postComment(questionId, body.trim(), replyTo ?? undefined);
      setBody("");
      setReplyTo(null);
      qc.invalidateQueries({ queryKey: ["comments", questionId] });
    } catch {
      setError("Couldn't post — try again.");
    }
  }

  async function upvote(id: number) {
    await api.upvoteComment(id);
    qc.invalidateQueries({ queryKey: ["comments", questionId] });
  }

  if (isLoading) return <p className="text-sm text-surface-800/60">Loading discussion…</p>;
  if (isError) return null; // 403 before submit — parent decides whether to show

  const comments = data?.results ?? [];

  return (
    <section className="space-y-4 rounded-xl border border-surface-100 bg-white p-5">
      <h2 className="font-semibold">Discussion ({comments.length})</h2>

      <form onSubmit={submit} className="space-y-2">
        {replyTo && (
          <p className="text-xs text-surface-800/60">
            Replying to comment #{replyTo}{" "}
            <button type="button" onClick={() => setReplyTo(null)} className="underline">cancel</button>
          </p>
        )}
        <textarea
          value={body}
          onChange={(e) => setBody(e.target.value)}
          rows={2}
          placeholder="Ask a doubt or explain your reasoning…"
          className="w-full rounded-lg border border-surface-200 px-3 py-2 text-sm"
        />
        {error && <p className="text-sm text-error-500">{error}</p>}
        <button className="rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700">
          Post comment
        </button>
      </form>

      <ul className="space-y-3">
        {comments.map((c) => (
          <CommentItem key={c.id} c={c} depth={0} onReply={setReplyTo} onUpvote={upvote} currentUserId={user?.id} />
        ))}
      </ul>
      {comments.length === 0 && <p className="text-sm text-surface-800/60">No comments yet.</p>}
    </section>
  );
}

function CommentItem({
  c, depth, onReply, onUpvote, currentUserId,
}: {
  c: Comment; depth: number; onReply: (id: number) => void;
  onUpvote: (id: number) => void; currentUserId?: number;
}) {
  return (
    <li className={depth > 0 ? "ml-6 border-l-2 border-surface-100 pl-3" : ""}>
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="text-sm font-medium">
            {c.author}
            {c.is_senior && <span className="ml-1 rounded bg-primary-100 px-1.5 text-xs text-primary-700">senior</span>}
            {c.is_accepted && <span className="ml-1 rounded bg-success-500/20 px-1.5 text-xs text-success-600">✓ accepted</span>}
          </p>
          <p className="text-sm text-surface-800/80">{c.body}</p>
        </div>
        <div className="flex shrink-0 items-center gap-2 text-xs">
          <button onClick={() => onUpvote(c.id)} className="rounded bg-surface-100 px-2 py-1 hover:bg-surface-200">
            ▲ {c.upvotes}
          </button>
          {depth === 0 && (
            <button onClick={() => onReply(c.id)} className="text-primary-600 hover:underline">
              Reply
            </button>
          )}
        </div>
      </div>
      {c.replies?.map((r) => (
        <CommentItem key={r.id} c={r} depth={depth + 1} onReply={onReply} onUpvote={onUpvote} currentUserId={currentUserId} />
      ))}
    </li>
  );
}
