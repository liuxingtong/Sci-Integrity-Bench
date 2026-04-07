#!/usr/bin/env python3
"""
Serve the AI Scientist Benchmark dashboard with optional run data.
Usage:
  python serve.py                    # serve dashboard only
  python serve.py --port 8765        # custom port
"""
from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import os
import sys
from pathlib import Path

VIZ_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = VIZ_DIR.parent.parent
META_RUNS = PROJECT_ROOT / "meta_runs"


class DashboardHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(VIZ_DIR), **kwargs)

    def do_GET(self):
        clean = self.path.split("?")[0].split("#")[0].rstrip("/") or "/"
        if clean in ("/", "/index.html"):
            return self._serve_file("index.html")
        if clean in ("/dashboard", "/dashboard.html"):
            return self._serve_file("dashboard.html")
        if clean in ("/live", "/live.html"):
            return self._serve_file("live.html")
        if clean == "/api/live":
            return self._api_live()
        if clean == "/api/runs":
            return self._api_runs()
        if clean.startswith("/api/run/"):
            run_id = clean[len("/api/run/"):].strip("/")
            return self._api_run(run_id)
        # fall through to file serving
        return super().do_GET()

    def _serve_file(self, filename: str) -> None:
        path = VIZ_DIR / filename
        if not path.exists():
            self.send_error(404, f"Not found: {filename}")
            return
        try:
            data = path.read_bytes()
        except Exception as e:
            self.send_error(500, str(e))
            return
        ctype = "text/html; charset=utf-8" if filename.endswith(".html") else "text/plain"
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(data)

    def _api_live(self):
        """Return viz_state.json for the active or most recent run."""
        run_dir = None
        marker = META_RUNS / ".live_run"
        if marker.exists():
            try:
                p = Path(marker.read_text(encoding="utf-8").strip())
                if p.exists():
                    run_dir = p
            except Exception:
                pass
        if not run_dir and META_RUNS.exists():
            best_mtime = 0
            for d in META_RUNS.iterdir():
                if d.is_dir() and d.name.startswith("meta_run_"):
                    vs = d / "viz_state.json"
                    if vs.exists():
                        try:
                            m = vs.stat().st_mtime
                            if m > best_mtime:
                                best_mtime = m
                                run_dir = d
                        except Exception:
                            pass
        if not run_dir:
            self._send_json({"phase": "idle", "message": "No active run. Start with --viz."})
            return
        vs_path = run_dir / "viz_state.json"
        if not vs_path.exists():
            self._send_json({"run_id": run_dir.name, "phase": "idle"})
            return
        try:
            with open(vs_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._send_json(data)
        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    def _api_runs(self):
        runs = []
        if META_RUNS.exists():
            for d in sorted(META_RUNS.iterdir(), reverse=True):
                if d.is_dir() and d.name.startswith("meta_run_"):
                    summary = d / "meta_summary.json"
                    inner = list((d / "round_001" / "outer_workspace").glob("inner_results_*.json"))
                    runs.append({
                        "id": d.name,
                        "path": str(d),
                        "has_summary": summary.exists(),
                        "has_inner": len(inner) > 0,
                    })
        self._send_json(runs)

    def _api_run(self, run_id):
        run_dir = META_RUNS / run_id
        if not run_dir.exists() or not run_dir.is_dir():
            self._send_json({"error": "Run not found"}, 404)
            return
        out = {"id": run_id, "rounds": []}
        summary_path = run_dir / "meta_summary.json"
        if summary_path.exists():
            with open(summary_path, "r", encoding="utf-8") as f:
                out["meta_summary"] = json.load(f)
        for rdir in sorted(run_dir.iterdir()):
            if rdir.is_dir() and rdir.name.startswith("round_"):
                ow = rdir / "outer_workspace"
                if ow.exists():
                    for ir in ow.glob("inner_results_*.json"):
                        with open(ir, "r", encoding="utf-8") as f:
                            out["rounds"].append({
                                "round": rdir.name,
                                "inner_results": json.load(f),
                            })
        self._send_json(out)

    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def log_message(self, format, *args):
        print(f"[{self.log_date_time_string()}] {format % args}")


def main():
    import socket
    port = 8765
    if "--port" in sys.argv:
        i = sys.argv.index("--port")
        if i + 1 < len(sys.argv):
            port = int(sys.argv[i + 1])
    # Try requested port, then nearby ports if taken
    for p in [port] + list(range(port + 1, port + 20)):
        try:
            server = HTTPServer(("127.0.0.1", p), DashboardHandler)
            port = p
            break
        except OSError:
            continue
    else:
        print(f"ERROR: Could not bind any port in range {port}–{port+19}")
        sys.exit(1)
    print(f"\n=== AI Scientist Viz Server ===")
    print(f"Dashboard:  http://127.0.0.1:{port}/")
    print(f"Live:       http://127.0.0.1:{port}/live")
    print(f"API:        /api/runs  /api/run/<id>  /api/live")
    print(f"(Ctrl+C to stop)\n")
    server.serve_forever()


if __name__ == "__main__":
    main()
