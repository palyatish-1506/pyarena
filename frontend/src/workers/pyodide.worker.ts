/// <reference lib="webworker" />
// Pyodide via CDN — avoids bundling ~10MB WASM into the app.
// Load once, reuse for all runs. Messages:
//   {type:'init'} -> {type:'ready'}
//   {type:'run', code, stdin} -> {type:'result'|'error', stdout, stderr}

declare const importScripts: (...urls: string[]) => void;

const PYODIDE_CDN = "https://cdn.jsdelivr.net/pyodide/v0.26.4/full/";
let pyodide: any = null;
let loading: Promise<any> | null = null;

async function getPyodide() {
  if (pyodide) return pyodide;
  if (!loading) {
    loading = (async () => {
      importScripts(`${PYODIDE_CDN}pyodide.js`);
      const load = (self as any).loadPyodide;
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
      py.globals.set("__stdin_data", msg.stdin ?? "");
      py.runPython(`
import sys, io
_data = __stdin_data.splitlines()
_idx = [0]
def _input(prompt=""):
    if _idx[0] < len(_data):
        line = _data[_idx[0]]; _idx[0] += 1
        return line.rstrip("\\n")
    raise EOFError
sys.stdin = type("S", (), {"readline": staticmethod(lambda *a: _input() + "\\n"), "read": staticmethod(lambda *a: "\\n".join(_data))})()
`);
      let stdout = "", stderr = "", error = "";
      try {
        await py.runPythonAsync(msg.code);
      } catch (err: any) {
        error = String(err?.message ?? err);
      }
      stdout = py.globals.get("sys").stdout.getvalue();
      stderr = py.globals.get("sys").stderr.getvalue();
      if (error && !stderr) stderr = error;
      py.runPython(`import sys; sys.stdout, sys.stderr = sys.__stdout__, sys.__stderr__`);
      self.postMessage({ type: "result", stdout, stderr });
    }
  } catch (err: any) {
    self.postMessage({ type: "error", stderr: String(err?.message ?? err) });
  }
};
