/** Minimal safe markdown renderer — headings, bold, code, lists, paragraphs.
 *  No raw HTML passthrough (XSS-safe by construction). */
export function Markdown({ text }: { text: string }) {
  const blocks = text.split(/\n{2,}/).filter(Boolean);
  return (
    <div className="space-y-3 text-sm leading-relaxed">
      {blocks.map((block, i) => {
        const lines = block.split("\n");
        const first = lines[0];
        if (first.startsWith("### "))
          return <h3 key={i} className="text-base font-semibold">{inline(first.slice(4))}</h3>;
        if (first.startsWith("## "))
          return <h2 key={i} className="text-lg font-semibold">{inline(first.slice(3))}</h2>;
        if (first.startsWith("# "))
          return <h1 key={i} className="text-xl font-bold">{inline(first.slice(2))}</h1>;
        if (lines.every((l) => l.trim().startsWith("- ")))
          return (
            <ul key={i} className="list-disc space-y-1 pl-5">
              {lines.map((l, j) => (
                <li key={j}>{inline(l.trim().slice(2))}</li>
              ))}
            </ul>
          );
        return <p key={i}>{lines.map((l, j) => <span key={j}>{inline(l)}{j < lines.length - 1 ? <br /> : null}</span>)}</p>;
      })}
    </div>
  );
}

function inline(text: string) {
  // **bold** and `code` — applied in order, no HTML injection.
  const parts = text.split(/(\*\*[^*]+\*\*|`[^`]+`)/g);
  return parts.map((p, i) => {
    if (p.startsWith("**") && p.endsWith("**"))
      return <strong key={i}>{p.slice(2, -2)}</strong>;
    if (p.startsWith("`") && p.endsWith("`"))
      return <code key={i} className="rounded bg-surface-100 px-1 font-mono text-xs">{p.slice(1, -1)}</code>;
    return p;
  });
}
