/// <reference lib="webworker" />
// Pyodide via CDN — avoids bundling ~10MB WASM into the app.
// Load once, reuse for all runs. Messages:
//   {type:'init'} -> {type:'ready'}
//   {type:'run', code, stdin} -> {type:'result'|'error', stdout, stderr}

declare const importScripts: (...urls: string[]) => void;

const PYODIDE_CDN = "https://cdn.jsdelivr.net/pyodide/v0.26.4/full/";
interface Pyodide {
  globals: { set(k: string, v: unknown): void; get(k: string): unknown };
  runPython(code: string): void;
  runPythonAsync(code: string): Promise<void>;
}
let pyodide: Pyodide | null = null;
let loading: Promise<Pyodide> | null = null;

async function getPyodide() {
  if (pyodide) return pyodide;
  if (!loading) {
    loading = (async () => {
      importScripts(`${PYODIDE_CDN}pyodide.js`);
      const load = (self as unknown as { loadPyodide: (o: { indexURL: string }) => Promise<Pyodide> }).loadPyodide;
      pyodide = await load({ indexURL: PYODIDE_CDN });
      return pyodide;
    })();
  }
  return loading;
}

self.onmessage = async (e: MessageEvent) => {
  const msg = e.data;
  try {
    if (msg.type === "init") {
      await getPyodide();
      self.postMessage({ type: "ready" });
      return;
    }
    if (msg.type === "run") {
      const py = await getPyodide();
      // Pyodide's input() uses setStdin, not sys.stdin — feed lines directly.
      const pyapi = py as unknown as {
        setStdin(o: { stdin: () => string | null }): void;
        setStdout(o: { batched: (s: string) => void }): void;
        setStderr(o: { batched: (s: string) => void }): void;
      };
      const lines = (msg.stdin ?? "").split("\n");
      let idx = 0;
      let stdout = "", stderr = "", error = "";
      pyapi.setStdin({ stdin: () => (idx < lines.length ? lines[idx++] : null) });
      pyapi.setStdout({ batched: (s) => (stdout += s) });
      pyapi.setStderr({ batched: (s) => (stderr += s) });
      try {
        await py.runPythonAsync(msg.code);
      } catch (err) {
        error = String((err as Error)?.message ?? err);
      }
      if (error && !stderr) stderr = error;
      self.postMessage({ type: "result", stdout, stderr });
    }
  } catch (err) {
    self.postMessage({ type: "error", stderr: String((err as Error)?.message ?? err) });
  }
};
