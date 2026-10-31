import sqlite3
from collections.abc import Mapping
from contextlib import closing
from pathlib import Path
from typing import Any

from flask import Flask, current_app, g, redirect, render_template, request, url_for


def create_app(test_config: dict[str, Any] | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_mapping(
        DATABASE=Path(__file__).resolve().parents[2] / "instance" / "wines.db"
    )
    if test_config is not None:
        app.config.update(test_config)

    init_db(app)

    @app.teardown_appcontext
    def close_db(_error: BaseException | None = None) -> None:
        db = g.pop("db", None)
        if db is not None:
            db.close()

    @app.route("/", methods=["GET", "POST"])
    def index():
        errors: list[str] = []
        values = request.form if request.method == "POST" else {}

        if request.method == "POST":
            name = request.form.get("name", "").strip()
            grape_variety = request.form.get("rebsorte", "").strip()
            vintage_text = request.form.get("jahrgang", "").strip()
            origin = request.form.get("herkunftsort", "").strip()
            rating_text = request.form.get("rating", "").strip()
            notes = request.form.get("notizen", "").strip() or None

            for label, value in (
                ("Name", name),
                ("Rebsorte", grape_variety),
                ("Herkunftsort", origin),
            ):
                if not value:
                    errors.append(f"{label} ist erforderlich.")
                elif len(value) > 100:
                    errors.append(f"{label} darf höchstens 100 Zeichen enthalten.")

            try:
                vintage = int(vintage_text)
            except ValueError:
                errors.append("Der Jahrgang muss eine Ganzzahl sein.")
                vintage = 0

            try:
                rating = int(rating_text)
            except ValueError:
                errors.append("Die Bewertung muss eine Ganzzahl von 1 bis 5 sein.")
                rating = 0
            else:
                if not 1 <= rating <= 5:
                    errors.append("Die Bewertung muss zwischen 1 und 5 liegen.")

            if not errors:
                try:
                    db = get_db()
                    db.execute(
                        """
                        INSERT INTO wines
                            (name, rebsorte, jahrgang, herkunftsort, rating, notizen)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (name, grape_variety, vintage, origin, rating, notes),
                    )
                    db.commit()
                except sqlite3.Error:
                    if "db" in g:
                        g.db.rollback()
                    current_app.logger.exception("Could not save wine")
                    return (
                        render_template(
                            "index.html",
                            wines=[],
                            values=values,
                            errors=[],
                            created=False,
                            database_error=(
                                "Der Wein konnte wegen eines Datenbankfehlers nicht "
                                "gespeichert werden."
                            ),
                        ),
                        500,
                    )
                return redirect(url_for("index", created="1"), code=303)

            return render_wine_page(values, errors), 400

        return render_wine_page(values, errors)

    return app


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        db = sqlite3.connect(current_app.config["DATABASE"])
        db.row_factory = sqlite3.Row
        g.db = db
    return g.db


def init_db(app: Flask) -> None:
    database_path = Path(app.config["DATABASE"])
    database_path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(database_path)) as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS wines (
                id INTEGER PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                rebsorte VARCHAR(100) NOT NULL,
                jahrgang INTEGER NOT NULL,
                herkunftsort VARCHAR(100) NOT NULL,
                rating INTEGER NOT NULL,
                notizen TEXT
            )
            """)


def render_wine_page(values: Mapping[str, str], errors: list[str]):
    wines = (
        get_db()
        .execute(
            "SELECT id, name, rebsorte, jahrgang, herkunftsort, rating, notizen "
            "FROM wines ORDER BY id DESC"
        )
        .fetchall()
    )
    return render_template(
        "index.html",
        wines=wines,
        values=values,
        errors=errors,
        created=request.args.get("created") == "1",
        database_error=None,
    )


app = create_app()
