"""HTTP service for tool episodes, so any RL trainer can run european-rl environments as remote, stateful tools.

Standard library only (ThreadingHTTPServer). One server per training node on 127.0.0.1, like the offline search;
episodes live in memory, keyed by a session id, and expire after `ttl` seconds without activity.

  POST /reset   {"env": id, "seed": int, "split": "train", "language": "deu"}
                -> {"session": id, "instruction": str, "tools": [OpenAI schemas], "max_steps": int}
  POST /step    {"session": id, "tool": name, "arguments": {...}}
                -> {"observation": {...}, "done": bool, "reward": float|null}
  POST /finish  {"session": id, "final": str}      -> {"reward": float, "info": {...}}
  GET  /health  -> {"ok": true, "sessions": n, "environments": [...]}

`python -m eurl.serve --port 18091`
"""
from __future__ import annotations

import argparse
import json
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict

from eurl.core import load, manifests


class Sessions:
    def __init__(self, ttl: float = 1800.0) -> None:
        self.ttl, self._lock, self._items = ttl, threading.Lock(), {}
        self.tool_envs = sorted(m["id"] for m in manifests() if m["interaction"] == "tool_episode")

    def reset(self, req: Dict[str, Any]) -> Dict[str, Any]:
        if req.get("env") not in self.tool_envs:
            raise ValueError(f"unknown tool environment {req.get('env')!r}; available: {self.tool_envs}")
        env = load(req["env"])
        obs = env.reset(int(req.get("seed", 0)), req.get("split", "train"), req.get("language"))
        session = uuid.uuid4().hex
        with self._lock:
            self._expire()
            self._items[session] = [env, time.time()]
        return {"session": session, **obs}

    def _get(self, session: str):
        with self._lock:
            item = self._items.get(session)
            if item is None:
                raise KeyError(f"unknown or expired session {session}")
            item[1] = time.time()
            return item[0]

    def _drop(self, session: str) -> None:
        with self._lock:
            self._items.pop(session, None)

    def _expire(self) -> None:
        now = time.time()
        for key in [k for k, (_, t) in self._items.items() if now - t > self.ttl]:
            del self._items[key]

    def step(self, req: Dict[str, Any]) -> Dict[str, Any]:
        env = self._get(req["session"])
        result = env.step({"tool": req.get("tool"), "arguments": req.get("arguments", {})})
        done = result["terminated"] or result["truncated"]
        if done:
            self._drop(req["session"])
        return {"observation": result["observation"], "done": done, "reward": result["reward"] if done else None,
                "info": _jsonable(result["info"]) if done else None}

    def finish(self, req: Dict[str, Any]) -> Dict[str, Any]:
        env = self._get(req["session"])
        result = env.step({"final": str(req.get("final", ""))})
        self._drop(req["session"])
        return {"reward": result["reward"], "info": _jsonable(result["info"])}

    def health(self) -> Dict[str, Any]:
        with self._lock:
            return {"ok": True, "sessions": len(self._items), "environments": self.tool_envs}


def _jsonable(value):
    return json.loads(json.dumps(value, default=str))


def make_handler(sessions: Sessions):
    class Handler(BaseHTTPRequestHandler):
        def _send(self, code: int, payload: Dict[str, Any]) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):  # noqa: N802
            if self.path == "/health":
                self._send(200, sessions.health())
            else:
                self._send(404, {"error": "not found"})

        def do_POST(self):  # noqa: N802
            routes = {"/reset": sessions.reset, "/step": sessions.step, "/finish": sessions.finish}
            if self.path not in routes:
                return self._send(404, {"error": "not found"})
            try:
                length = int(self.headers.get("Content-Length", 0))
                req = json.loads(self.rfile.read(length) or b"{}")
                self._send(200, routes[self.path](req))
            except (KeyError, ValueError, TypeError) as error:
                self._send(400, {"error": str(error)})

        def log_message(self, *args):  # quiet
            pass

    return Handler


def serve(host: str = "127.0.0.1", port: int = 18091, ttl: float = 1800.0) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer((host, port), make_handler(Sessions(ttl)))
    server.daemon_threads = True
    return server


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=18091)
    ap.add_argument("--ttl", type=float, default=1800.0)
    a = ap.parse_args()
    server = serve(a.host, a.port, a.ttl)
    print(f"eurl tool service on {a.host}:{a.port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
