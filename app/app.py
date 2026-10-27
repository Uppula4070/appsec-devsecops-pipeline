"""Small notes API used as the target for the security pipeline.

The main branch is written securely; the `vulnerable-demo` branch adds
deliberate flaws so the pipeline has something to catch.
"""
import os
import sqlite3

from flask import Flask, g, jsonify, request

DATABASE = os.environ.get("NOTES_DB", "notes.db")

app = Flask(__name__)


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DATABASE)
    db.execute("CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY, title TEXT, body TEXT)")
    if db.execute("SELECT COUNT(*) FROM notes").fetchone()[0] == 0:
        db.executemany(
            "INSERT INTO notes (title, body) VALUES (?, ?)",
            [("welcome", "First note"), ("pipeline", "Scans run on every pull request")],
        )
    db.commit()
    db.close()


@app.after_request
def security_headers(response):
    # form-action and base-uri don't fall back to default-src, so set them explicitly.
    response.headers["Content-Security-Policy"] = (
        "default-src 'none'; frame-ancestors 'none'; form-action 'none'; base-uri 'none'"
    )
    # Hide the framework and Python version from the Server header.
    response.headers["Server"] = "notes-api"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
    response.headers["Cache-Control"] = "no-store"
    response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
    response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
    return response


@app.get("/")
@app.get("/health")
def health():
    return jsonify(status="ok")


@app.get("/notes")
def search_notes():
    query = request.args.get("q", "")[:100]
    # Parameterized query: user input is never concatenated into SQL.
    rows = get_db().execute(
        "SELECT id, title, body FROM notes WHERE title LIKE ?", (f"%{query}%",)
    ).fetchall()
    return jsonify([dict(row) for row in rows])


@app.get("/robots.txt")
def robots():
    return "User-agent: *\nDisallow: /\n", 200, {"Content-Type": "text/plain"}


if __name__ == "__main__":
    # Waitress instead of Flask's dev server, which adds its own version banner.
    from waitress import serve

    init_db()
    serve(app, host="127.0.0.1", port=int(os.environ.get("PORT", "5000")), ident="notes-api")
