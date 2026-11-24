/**
 * Timezone helpers. Spec: users think in IST (Asia/Kolkata, UTC+5:30);
 * the API stores UTC.
 *
 * datetime-local inputs give "YYYY-MM-DDTHH:mm" with NO timezone — we
 * interpret that wall-clock time as IST and convert to a UTC ISO string.
 */

/** "2026-11-24T14:30" (IST wall clock) -> "2026-11-24T09:00:00.000Z" (UTC ISO) */
export function istLocalToUtcIso(local: string): string | null {
  if (!local) return null;
  // Append the IST offset so Date parses it as an absolute instant.
  const withOffset = `${local}:00+05:30`;
  const d = new Date(withOffset);
  return Number.isNaN(d.getTime()) ? null : d.toISOString();
}

/** UTC ISO -> "YYYY-MM-DDTHH:mm" in IST, for prefilling datetime-local inputs. */
export function utcIsoToIstLocal(iso: string | null): string {
  if (!iso) return "";
  const d = new Date(iso);
  // Shift by +5:30 then read UTC fields — classic tz trick.
  const ist = new Date(d.getTime() + 5.5 * 60 * 60 * 1000);
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${ist.getUTCFullYear()}-${pad(ist.getUTCMonth() + 1)}-${pad(ist.getUTCDate())}T${pad(ist.getUTCHours())}:${pad(ist.getUTCMinutes())}`;
}
