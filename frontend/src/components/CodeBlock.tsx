import { useEffect, useRef } from "react";
import Prism from "prismjs";
import "prismjs/components/prism-python";

/** Renders a Python code snippet with Prism syntax highlighting. */
export function CodeBlock({ code, className = "" }: { code: string; className?: string }) {
  const ref = useRef<HTMLElement>(null);

  useEffect(() => {
    if (ref.current) {
      Prism.highlightElement(ref.current);
    }
  }, [code]);

  return (
    <pre
      className={`overflow-x-auto rounded-lg bg-surface-900 p-4 font-mono text-sm text-surface-50 ${className}`}
    >
      <code ref={ref} className="language-python">
        {code}
      </code>
    </pre>
  );
}
