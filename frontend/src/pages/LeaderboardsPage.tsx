import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../api/client";
import { useAuth } from "../auth/AuthContext";

const SCOPES = [
  { key: "weekly", label: "Weekly" },
  { key: "division", label: "My Division" },
  { key: "division_battle", label: "Division Battle" },
  { key: "improved", label: "Most Improved" },
  { key: "beginner", label: "Beginner League" },
  { key: "season", label: "Season" },
] as const;

interface Row {
  rank: number;
  score: number;
  user_id: number;
  full_name: string;
  avatar_seed: string;
  level: number;
  division?: string;
  total_points?: number;
  active_members?: number;
  avg_per_member?: number;
  this_week?: number;
  last_week?: number;
}
interface Me {
  rank: number | null;
  score: number;
  gap_to_next: number | null;
}

function Avatar({ seed, name }: { seed: string; name: string }) {
  const initials = name.slice(0, 2).toUpperCase();
  return seed ? (
    <img
      src={`https://api.dicebear.com/9.x/bottts/svg?seed=${encodeURIComponent(seed)}`}
      alt={name}
      className="h-9 w-9 rounded-full bg-surface-100"
      loading="lazy"
    />
  ) : (
    <div className="flex h-9 w-9 items-center justify-center rounded-full bg-primary-100 text-xs font-bold text-primary-700">
      {initials}
    </div>
  );
}

export function LeaderboardsPage() {
  const { user } = useAuth();
  const [scope, setScope] = useState<string>("weekly");
  const [division, setDivision] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["leaderboard", scope, division],
    queryFn: async () => {
      const params: Record<string, string> = { scope };
      if (scope === "division" && division) params.division = division;
      const { data } = await apiClient.get("/api/v1/leaderboard/", { params });
      return data as { rows: Row[]; me: Me | null };
    },
  });

  const isBattle = scope === "division_battle";

  return (
    <section className="mx-auto max-w-2xl space-y-4">
      <h1 className="text-2xl font-bold">Leaderboards</h1>

      <div className="flex flex-wrap gap-2">
        {SCOPES.map((s) => (
          <button
            key={s.key}
            onClick={() => setScope(s.key)}
            className={`rounded-full px-3 py-1.5 text-sm font-medium ${
              scope === s.key ? "bg-primary-600 text-white" : "bg-surface-100 hover:bg-surface-200"
            }`}
          >
            {s.label}
          </button>
        ))}
      </div>

      {scope === "division" && (
        <div className="flex gap-2">
          {["", "A", "B", "C", "D"].map((d) => (
            <button
              key={d || "all"}
              onClick={() => setDivision(d)}
              className={`rounded-lg px-3 py-1 text-sm ${division === d ? "bg-primary-600 text-white" : "bg-surface-100"}`}
            >
              {d || "All"}
            </button>
          ))}
        </div>
      )}

      {/* Sticky "your rank" bar */}
      {data?.me && (
        <div className="sticky top-16 z-10 rounded-xl border border-primary-200 bg-primary-50 px-4 py-3 text-sm">
          {data.me.rank ? (
            <>
              Your rank: <strong>#{data.me.rank}</strong> · {data.me.score} pts
              {data.me.gap_to_next ? ` · ${data.me.gap_to_next} behind next` : " · top spot!"}
            </>
          ) : (
            <>Answer a question this week to get on the board.</>
          )}
        </div>
      )}

      {isLoading && <p className="text-sm text-surface-800/60">Loading…</p>}

      {data && data.rows.length === 0 && (
        <p className="rounded-xl border border-dashed border-surface-200 p-6 text-center text-sm text-surface-800/60">
          No scores yet — be the first!
        </p>
      )}

      <ol className="space-y-2">
        {data?.rows.map((r) => {
          const isMe = user?.id === r.user_id;
          return (
            <li
              key={r.user_id ?? r.division ?? r.rank}
              className={`flex items-center gap-3 rounded-xl border p-3 ${
                isMe ? "border-primary-400 bg-primary-50" : "border-surface-100 bg-white"
              }`}
            >
              <span className="w-8 text-center font-bold text-surface-800/60">#{r.rank}</span>
              {isBattle ? (
                <>
                  <div className="flex-1">
                    <p className="font-medium">Division {r.division}</p>
                    <p className="text-xs text-surface-800/60">
                      {r.active_members} active · avg {r.avg_per_member} pts
                    </p>
                  </div>
                  <span className="font-semibold">{r.total_points} pts</span>
                </>
              ) : (
                <>
                  <Avatar seed={r.avatar_seed} name={r.full_name} />
                  <div className="flex-1">
                    <p className="font-medium">
                      {r.full_name || r.user_id}
                      {isMe && <span className="ml-2 text-xs text-primary-600">(you)</span>}
                    </p>
                    <p className="text-xs text-surface-800/60">
                      Lv {r.level} · Div {r.division}
                      {r.this_week !== undefined && ` · ${r.this_week - (r.last_week ?? 0) >= 0 ? "+" : ""}${(r.this_week ?? 0) - (r.last_week ?? 0)}`}
                    </p>
                  </div>
                  <span className="font-semibold">{r.score} pts</span>
                </>
              )}
            </li>
          );
        })}
      </ol>
    </section>
  );
}
