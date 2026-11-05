#!/usr/bin/env python3
"""
War Room spectator dashboard.

Serves a live scoreboard at http://127.0.0.1:8099 that watches the real
match: the 5 locks flip from red to green as Blue's patches are verified,
with the Red vs Blue score and a live event feed.

It reads two sources of truth, so it can never lie about the match:
  - referee/check.py          the real exploit + feature checks (are the bugs fixed?)
  - referee/scoreboard.json   the Referee's score and event log

Run it alongside the arena:
  python3 dashboard/serve.py
Then open http://127.0.0.1:8099

Standard library only.
"""

import importlib.util
import json
import os
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DASH = os.path.join(ROOT, "dashboard")
SCOREBOARD = os.path.join(ROOT, "referee", "scoreboard.json")
ARENA = os.environ.get("ARENA_URL", "http://127.0.0.1:5050")
PORT = int(os.environ.get("DASHBOARD_PORT", "8099"))
ORDER = ["sqli", "auth", "idor", "traversal", "debug"]

# Import the referee's check module so the board uses the exact same verdicts.
_spec = importlib.util.spec_from_file_location(
    "wr_check", os.path.join(ROOT, "referee", "check.py")
)
check = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(check)

_cache = {"t": 0.0, "data": None}


def vuln_report():
    now = time.time()
    if _cache["data"] is not None and now - _cache["t"] < 2.0:
        return _cache["data"]
    report = check.run(ARENA)
    _cache["t"], _cache["data"] = now, report
    return report


def scoreboard():
    try:
        with open(SCOREBOARD, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {"round": 0, "red": 0, "blue": 0, "log": []}


def state():
    rep = vuln_report()
    board = scoreboard()
    vulns = []
    if rep.get("online"):
        res = rep["results"]
        for key in ORDER:
            if key in res:
                vulns.append({"key": key, "verdict": res[key]["verdict"]})
    return {
        "online": bool(rep.get("online")),
        "vulns": vulns,
        "round": board.get("round", 0),
        "red": board.get("red", 0),
        "blue": board.get("blue", 0),
        "log": board.get("log", [])[-8:],
    }


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.startswith("/state"):
            self._send(200, json.dumps(state()).encode(), "application/json")
            return
        try:
            with open(os.path.join(DASH, "index.html"), "rb") as fh:
                self._send(200, fh.read(), "text/html; charset=utf-8")
        except OSError:
            self._send(404, b"not found", "text/plain")


if __name__ == "__main__":
    try:
        server = HTTPServer(("127.0.0.1", PORT), Handler)
    except OSError:
        print(f"Port {PORT} is already used by another app on this machine.")
        print("Pick another one, e.g.:  DASHBOARD_PORT=9000 ./scripts/dashboard.sh")
        raise SystemExit(1)
    print(f"War Room dashboard on http://127.0.0.1:{PORT}  (arena: {ARENA})")
    print("Keep this window open. Ctrl+C stops the dashboard.")
    server.serve_forever()
