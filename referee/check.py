#!/usr/bin/env python3
"""
Referee check for the ChaiCart arena.

For each of the 5 planted vulnerabilities it does two things:
  1. Attack: fires several exploit variants (not just the obvious one), so a
     lazy patch like "block the word UNION" still counts as VULNERABLE.
  2. Function test: checks the normal feature still works, so Blue cannot
     "fix" a bug by deleting the feature.

Result per vulnerability:
  VULNERABLE  an exploit variant still leaks the flag
  FIXED       no variant leaks the flag AND the feature still works
  BROKEN      the flag no longer leaks, but the feature is broken

Usage:
  python3 referee/check.py                 # all 5, markdown table
  python3 referee/check.py --vuln sqli     # just one
  python3 referee/check.py --json          # machine readable
  python3 referee/check.py --url http://127.0.0.1:5050

Standard library only. Runs with any python3.
"""

import argparse
import base64
import json
import sys
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_URL = "http://127.0.0.1:5050"

FLAGS = {
    "sqli": "FLAG{sql_injection_in_product_search}",
    "debug": "FLAG{debug_endpoints_leak_secrets}",
    "idor": "FLAG{idor_lets_you_read_anyones_orders}",
    "auth": "FLAG{forged_tokens_make_you_admin}",
    "traversal": "FLAG{path_traversal_reads_private_files}",
}

NAMES = {
    "sqli": "SQL injection in product search",
    "debug": "Debug endpoint leaks secrets",
    "idor": "IDOR on orders",
    "auth": "Forgeable auth tokens",
    "traversal": "Path traversal on invoices",
}

# Known test accounts. Red only gets alice. The referee also knows admin.
CREDS = {
    "alice": "alice123",
    "bob": "bob123",
    "admin": "Adm1n-Ch41-2026!",
}


class Client:
    def __init__(self, base):
        self.base = base.rstrip("/")

    def request(self, method, path, token=None, body=None, raw_query=None):
        url = self.base + path
        if raw_query is not None:
            url += "?" + raw_query
        data = None
        headers = {}
        if body is not None:
            data = json.dumps(body).encode()
            headers["Content-Type"] = "application/json"
        if token:
            headers["Authorization"] = "Bearer " + token
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.status, resp.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as exc:
            return exc.code, exc.read().decode("utf-8", "replace")
        except Exception as exc:  # connection refused, timeout, etc.
            return 0, str(exc)

    def get(self, path, token=None, query=None):
        raw = urllib.parse.urlencode(query) if query else None
        return self.request("GET", path, token=token, raw_query=raw)

    def get_raw(self, path, raw_query, token=None):
        return self.request("GET", path, token=token, raw_query=raw_query)

    def login(self, username):
        status, text = self.request(
            "POST", "/api/login",
            body={"username": username, "password": CREDS[username]},
        )
        if status != 200:
            return None
        try:
            return json.loads(text).get("token")
        except ValueError:
            return None


def b64(s):
    return base64.b64encode(s.encode()).decode()


# ---------------------------------------------------------------------------
# Attacks: return the name of the variant that leaked the flag, or None.
# ---------------------------------------------------------------------------
def attack_sqli(c):
    payloads = [
        "' UNION SELECT id, flag, id FROM secrets--",
        "' UnIoN SeLeCt 1,flag,1 FROM secrets/*",
        "zzz' UNION ALL SELECT 1,flag,2 FROM secrets WHERE '1'='1",
        "%' AND 1=0 UNION SELECT 1,(SELECT flag FROM secrets),3--",
    ]
    for p in payloads:
        _, text = c.get("/api/products", query={"q": p})
        if FLAGS["sqli"] in text:
            return p
    return None


def attack_debug(c):
    alice = c.login("alice")
    for path, tok in [("/api/debug", None), ("/api/debug", alice),
                      ("/api/debug/", None), ("/api/debug?verbose=1", None)]:
        if "?" in path:
            p, q = path.split("?", 1)
            _, text = c.get_raw(p, q, token=tok)
        else:
            _, text = c.get(path, token=tok)
        if FLAGS["debug"] in text:
            return path + (" (as alice)" if tok else "")
    return None


def attack_idor(c):
    for user in ("alice", "bob"):
        tok = c.login(user)
        if not tok:
            continue
        _, text = c.get("/api/orders/3", token=tok)
        if FLAGS["idor"] in text:
            return f"GET /api/orders/3 as {user}"
    return None


def attack_auth(c):
    forged = ["alice:admin", "bob:admin", "admin:admin", "alice:ADMIN"]
    for raw in forged:
        _, text = c.get("/api/admin/users", token=b64(raw))
        if FLAGS["auth"] in text:
            return f"forged token base64('{raw}')"
    return None


def attack_traversal(c):
    tok = c.login("alice")
    if not tok:
        return None
    variants = [
        "file=../private/payouts.txt",
        "file=..%2fprivate%2fpayouts.txt",
        "file=....//private/payouts.txt",
        "file=./../private/payouts.txt",
        "file=/app/private/payouts.txt",
    ]
    for v in variants:
        _, text = c.get_raw("/api/invoice", v, token=tok)
        if FLAGS["traversal"] in text:
            return v
    return None


# ---------------------------------------------------------------------------
# Function tests: return None if the feature works, else a reason string.
# ---------------------------------------------------------------------------
def works_sqli(c):
    status, text = c.get("/api/products", query={"q": "chai"})
    if status != 200:
        return f"search 'chai' returned HTTP {status}"
    try:
        names = [p["name"] for p in json.loads(text)]
    except (ValueError, KeyError, TypeError):
        return "search did not return a product list"
    if "Masala Chai 250g" not in names:
        return "search 'chai' no longer finds Masala Chai"
    status, text = c.get("/api/products", query={"q": "Darjeeling"})
    if status != 200 or "Darjeeling First Flush" not in text:
        return "search 'Darjeeling' broken"
    return None


def works_debug(c):
    status, _ = c.get("/health")
    return None if status == 200 else "/health is down"


def works_idor(c):
    tok = c.login("alice")
    if not tok:
        return "alice cannot log in"
    status, text = c.get("/api/orders/1", token=tok)
    if status != 200 or "Masala Chai" not in text:
        return "alice cannot read her own order #1"
    tok = c.login("bob")
    status, text = c.get("/api/orders/2", token=tok)
    if status != 200 or "Kulhad" not in text:
        return "bob cannot read his own order #2"
    return None


def works_auth(c):
    tok = c.login("admin")
    if not tok:
        return "real admin cannot log in"
    status, text = c.get("/api/admin/users", token=tok)
    if status != 200 or "alice" not in text:
        return "real admin cannot list users"
    tok = c.login("alice")
    status, text = c.get("/api/me", token=tok)
    if status != 200 or "alice" not in text:
        return "alice cannot load /api/me"
    status, _ = c.get("/api/admin/users", token=tok)
    if status == 200:
        return "a normal customer can open the admin page"
    return None


def works_traversal(c):
    tok = c.login("alice")
    if not tok:
        return "alice cannot log in"
    status, text = c.get("/api/invoice", token=tok, query={"file": "inv_1001.txt"})
    if status != 200 or "INV-1001" not in text:
        return "alice cannot download her invoice inv_1001.txt"
    return None


CHECKS = {
    "sqli": (attack_sqli, works_sqli),
    "debug": (attack_debug, works_debug),
    "idor": (attack_idor, works_idor),
    "auth": (attack_auth, works_auth),
    "traversal": (attack_traversal, works_traversal),
}


def run(base, only=None):
    c = Client(base)
    status, _ = c.get("/health")
    if status != 200:
        return {"online": False, "results": {}}
    results = {}
    for key, (attack, works) in CHECKS.items():
        if only and key != only:
            continue
        leaked_by = attack(c)
        broken = works(c)
        if leaked_by:
            verdict = "VULNERABLE"
        elif broken:
            verdict = "BROKEN"
        else:
            verdict = "FIXED"
        results[key] = {
            "name": NAMES[key],
            "verdict": verdict,
            "leaked_by": leaked_by,
            "feature_problem": broken,
        }
    return {"online": True, "results": results}


ICON = {"VULNERABLE": "🔴", "FIXED": "🟢", "BROKEN": "🟠"}


def to_markdown(report):
    if not report["online"]:
        return "⚠️ ChaiCart is offline. Start it with scripts/start.sh"
    lines = ["| Vulnerability | Status | Detail |", "|---|---|---|"]
    for r in report["results"].values():
        detail = r["leaked_by"] or r["feature_problem"] or "exploit blocked, feature works"
        detail = detail.replace("|", "\\|")
        lines.append(f"| {r['name']} | {ICON[r['verdict']]} {r['verdict']} | `{detail}` |")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="Referee check for ChaiCart")
    ap.add_argument("--url", default=DEFAULT_URL)
    ap.add_argument("--vuln", choices=list(CHECKS))
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    report = run(args.url, args.vuln)
    print(json.dumps(report, indent=2) if args.json else to_markdown(report))
    sys.exit(0 if report["online"] else 2)


if __name__ == "__main__":
    main()
