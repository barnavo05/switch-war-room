"""
ChaiCart: a tiny, deliberately vulnerable shop API for the Switch War Room.

!!! DO NOT DEPLOY THIS ANYWHERE. It is insecure on purpose. !!!
It only exists so the Red agent can attack it and the Blue agent can fix it,
on your own laptop, bound to 127.0.0.1.

There are 5 planted vulnerabilities. Each one guards a FLAG{...}.
The Referee knows where they are. Red has to find them. Blue has to fix them
without breaking the shop.
"""

import base64
import os
import sqlite3

from flask import Flask, g, jsonify, request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "chaicart.db")
INVOICE_DIR = os.path.join(BASE_DIR, "invoices")

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Config. (Yes, the internal key is sitting right here. That is the point.)
# ---------------------------------------------------------------------------
CONFIG = {
    "app_name": "ChaiCart",
    "version": "0.3.1",
    "environment": "development",
    "db_path": DB_PATH,
    "internal_api_key": "FLAG{debug_endpoints_leak_secrets}",
}


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    if os.path.exists(DB_PATH):
        return
    db = sqlite3.connect(DB_PATH)
    db.executescript(
        """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT
        );
        CREATE TABLE products (
            id INTEGER PRIMARY KEY,
            name TEXT,
            price INTEGER
        );
        CREATE TABLE orders (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            item TEXT,
            notes TEXT
        );
        CREATE TABLE secrets (
            id INTEGER PRIMARY KEY,
            flag TEXT
        );

        INSERT INTO users VALUES (1, 'alice', 'alice123', 'customer');
        INSERT INTO users VALUES (2, 'bob',   'bob123',   'customer');
        INSERT INTO users VALUES (3, 'admin', 'Adm1n-Ch41-2026!', 'admin');

        INSERT INTO products VALUES (1, 'Masala Chai 250g', 249);
        INSERT INTO products VALUES (2, 'Kulhad Set (6)', 399);
        INSERT INTO products VALUES (3, 'Ginger Elaichi Blend', 299);
        INSERT INTO products VALUES (4, 'Darjeeling First Flush', 549);
        INSERT INTO products VALUES (5, 'Chai Patti Gift Box', 899);

        INSERT INTO orders VALUES (1, 1, 'Masala Chai 250g', 'Deliver after 6pm');
        INSERT INTO orders VALUES (2, 2, 'Kulhad Set (6)', 'Gift wrap please');
        INSERT INTO orders VALUES (3, 3, 'Supplier contract',
            'Wholesale code: FLAG{idor_lets_you_read_anyones_orders}');

        INSERT INTO secrets VALUES (1, 'FLAG{sql_injection_in_product_search}');
        """
    )
    db.commit()
    db.close()


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------
def make_token(username, role):
    # VULN 4 (broken auth): the token is just base64 of "username:role".
    # Anyone can decode it, change role to admin, and encode it again.
    raw = f"{username}:{role}".encode()
    return base64.b64encode(raw).decode()


def read_token():
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return None
    try:
        raw = base64.b64decode(header[len("Bearer "):]).decode()
        username, role = raw.split(":", 1)
    except Exception:
        return None
    db = get_db()
    user = db.execute(
        "SELECT id, username FROM users WHERE username = ?", (username,)
    ).fetchone()
    if user is None:
        return None
    return {"id": user["id"], "username": user["username"], "role": role}


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/")
def home():
    return jsonify(
        {
            "app": "ChaiCart",
            "message": "Welcome to ChaiCart, the internet's chai-est shop.",
            "endpoints": [
                "GET  /api/products?q=<search>",
                "POST /api/login  {username, password}",
                "GET  /api/me                (auth)",
                "GET  /api/orders/<id>       (auth)",
                "GET  /api/invoice?file=<name> (auth)",
                "GET  /api/admin/users       (admin)",
            ],
        }
    )


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.get("/api/products")
def products():
    q = request.args.get("q", "")
    db = get_db()
    # VULN 1 (SQL injection): user input is pasted straight into the query.
    sql = f"SELECT id, name, price FROM products WHERE name LIKE '%{q}%'"
    try:
        rows = db.execute(sql).fetchall()
    except sqlite3.Error as exc:
        return jsonify({"error": str(exc), "query": sql}), 500
    return jsonify([dict(r) for r in rows])


@app.post("/api/login")
def login():
    body = request.get_json(silent=True) or {}
    username = body.get("username", "")
    password = body.get("password", "")
    db = get_db()
    user = db.execute(
        "SELECT username, role FROM users WHERE username = ? AND password = ?",
        (username, password),
    ).fetchone()
    if user is None:
        return jsonify({"error": "invalid credentials"}), 401
    return jsonify({"token": make_token(user["username"], user["role"])})


@app.get("/api/me")
def me():
    user = read_token()
    if user is None:
        return jsonify({"error": "unauthorized"}), 401
    return jsonify(user)


@app.get("/api/orders/<int:order_id>")
def get_order(order_id):
    user = read_token()
    if user is None:
        return jsonify({"error": "unauthorized"}), 401
    db = get_db()
    # VULN 3 (IDOR): any logged-in user can read any order. No owner check.
    order = db.execute(
        "SELECT id, user_id, item, notes FROM orders WHERE id = ?", (order_id,)
    ).fetchone()
    if order is None:
        return jsonify({"error": "not found"}), 404
    return jsonify(dict(order))


@app.get("/api/invoice")
def invoice():
    user = read_token()
    if user is None:
        return jsonify({"error": "unauthorized"}), 401
    name = request.args.get("file", "")
    # VULN 5 (path traversal): the file name is joined to the folder blindly.
    path = os.path.join(INVOICE_DIR, name)
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return jsonify({"file": name, "content": fh.read()})
    except OSError:
        return jsonify({"error": "invoice not found"}), 404


@app.get("/api/admin/users")
def admin_users():
    user = read_token()
    if user is None or user["role"] != "admin":
        return jsonify({"error": "admins only"}), 403
    db = get_db()
    rows = db.execute("SELECT id, username, role FROM users").fetchall()
    return jsonify(
        {
            "users": [dict(r) for r in rows],
            "admin_note": "FLAG{forged_tokens_make_you_admin}",
        }
    )


@app.get("/api/debug")
def debug():
    # VULN 2 (secret leak): a debug endpoint left on, dumping the config.
    return jsonify({"config": CONFIG, "env_keys": sorted(os.environ.keys())})


init_db()

if __name__ == "__main__":
    # Bound to 127.0.0.1 so nothing outside your laptop can reach it.
    app.run(host="127.0.0.1", port=5050, debug=True)
