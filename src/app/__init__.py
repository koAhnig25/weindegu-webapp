import json
import sqlite3
from collections.abc import Mapping
from contextlib import closing
from datetime import date
from pathlib import Path
from typing import Any

from flask import (
    Flask,
    abort,
    current_app,
    g,
    redirect,
    render_template,
    request,
    url_for,
)
from werkzeug.datastructures import MultiDict

WINE_FIELDS = (
    ("name", "Name"),
    ("rebsorte", "Rebsorte"),
    ("herkunftsort", "Herkunftsort"),
)

TASTING_DETAIL_GROUPS = (
    {
        "key": "appearance_intensity",
        "section": "1. Farbe & Aussehen",
        "label": "Intensität",
        "multiple": False,
        "options": (("pale", "blass"), ("medium", "mittel"), ("deep", "tieffarbig")),
    },
    {
        "key": "appearance_color",
        "section": "1. Farbe & Aussehen",
        "label": "Farbe",
        "multiple": False,
        "options": (
            ("lemon_yellow", "zitronengelb"),
            ("gold_yellow", "goldgelb"),
            ("purple_red", "purpurrot"),
            ("ruby_red", "rubinrot"),
            ("garnet_red", "granatrot"),
        ),
    },
    {
        "key": "nose_intensity",
        "section": "2. Geruch / Nase",
        "label": "Intensität",
        "multiple": False,
        "options": (
            ("neutral", "neutral"),
            ("medium", "mittel"),
            ("aromatic", "aromatisch"),
        ),
    },
    {
        "key": "nose_aromas",
        "section": "2. Geruch / Nase",
        "label": "Aromatik",
        "multiple": True,
        "options": (
            ("herbal", "pflanzlich"),
            ("floral", "blumig"),
            ("fruity", "fruchtig"),
            ("overripe", "überreif"),
            ("buttery", "buttrig"),
            ("woody", "holzig"),
            ("spicy", "würzig"),
            ("earthy", "erdig"),
        ),
    },
    {
        "key": "taste_sweetness",
        "section": "3. Geschmack / Gaumen",
        "label": "Süsse",
        "multiple": False,
        "options": (
            ("dry", "trocken"),
            ("slightly_sweet", "leicht süss"),
            ("sweet", "süss"),
        ),
    },
    {
        "key": "taste_acidity",
        "section": "3. Geschmack / Gaumen",
        "label": "Säure",
        "multiple": False,
        "options": (("slightly_sour", "etwas sauer"), ("very_sour", "sehr sauer")),
    },
    {
        "key": "taste_tannin",
        "section": "3. Geschmack / Gaumen",
        "label": "Tannin",
        "multiple": False,
        "options": (
            ("slightly_astringent", "etwas pelzig"),
            ("very_astringent", "sehr pelzig"),
        ),
    },
    {
        "key": "taste_body",
        "section": "3. Geschmack / Gaumen",
        "label": "Körper",
        "multiple": False,
        "options": (("light", "leicht"), ("medium", "mittel"), ("heavy", "schwer")),
    },
    {
        "key": "taste_balance",
        "section": "3. Geschmack / Gaumen",
        "label": "Balance",
        "multiple": False,
        "options": (
            ("hard", "hart"),
            ("lively", "lebhaft"),
            ("balanced", "ausgewogen"),
            ("mild", "mild"),
            ("clumsy", "plump"),
        ),
    },
    {
        "key": "taste_aromas",
        "section": "3. Geschmack / Gaumen",
        "label": "Aromatik",
        "multiple": True,
        "options": (
            ("herbal", "pflanzlich"),
            ("floral", "blumig"),
            ("fruity", "fruchtig"),
            ("overripe", "überreif"),
            ("buttery", "buttrig"),
            ("woody", "holzig"),
            ("spicy", "würzig"),
            ("earthy", "erdig"),
        ),
    },
    {
        "key": "finish_length",
        "section": "4. Abgang & Gesamteindruck",
        "label": "Abgang",
        "multiple": False,
        "options": (("short", "kurz"), ("medium", "mittel"), ("long", "lang")),
    },
    {
        "key": "overall_impression",
        "section": "4. Abgang & Gesamteindruck",
        "label": "Gesamteindruck",
        "multiple": False,
        "options": (
            ("excellent", "hervorragend"),
            ("very_good", "sehr gut"),
            ("good", "gut"),
            ("average", "durchschnittlich"),
            ("weak", "schwach"),
        ),
    },
)


def empty_detailed_tasting() -> dict[str, list[str]]:
    return {group["key"]: [] for group in TASTING_DETAIL_GROUPS}


def load_detailed_tasting(serialized: str | None) -> dict[str, list[str]]:
    details = empty_detailed_tasting()
    if not serialized:
        return details

    try:
        saved_details = json.loads(serialized)
    except json.JSONDecodeError:
        current_app.logger.error("Stored detailed tasting is not valid JSON")
        abort(500)
    if not isinstance(saved_details, dict):
        current_app.logger.error("Stored detailed tasting has an invalid shape")
        abort(500)

    for group in TASTING_DETAIL_GROUPS:
        selected = saved_details.get(group["key"], [])
        allowed_values = {value for value, _label in group["options"]}
        if (
            not isinstance(selected, list)
            or any(value not in allowed_values for value in selected)
            or (not group["multiple"] and len(selected) > 1)
        ):
            current_app.logger.error(
                "Stored detailed tasting has invalid values for %s", group["key"]
            )
            abort(500)
        details[group["key"]] = selected
    return details


def dump_detailed_tasting(details: dict[str, list[str]]) -> str | None:
    if not any(details.values()):
        return None
    return json.dumps(details, ensure_ascii=False)


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
        if request.method == "POST":
            values, errors, database_error, _created_wine_id = save_wine(request.form)
            if database_error:
                return (
                    render_wine_page(
                        values,
                        [],
                        database_error=database_error,
                    ),
                    500,
                )
            if errors:
                return render_wine_page(values, errors), 400
            return redirect(url_for("index", created="1"), code=303)

        return render_wine_page({})

    @app.route("/wines/new-for-tasting", methods=["GET", "POST"])
    def new_wine_for_tasting():
        if request.method == "POST":
            values, errors, database_error, wine_id = save_wine(request.form)
            if database_error:
                return (
                    render_wine_page(
                        values,
                        [],
                        database_error=database_error,
                        form_only=True,
                    ),
                    500,
                )
            if errors:
                return (
                    render_wine_page(values, errors, form_only=True),
                    400,
                )
            if wine_id is None:
                current_app.logger.error("Wine creation succeeded without an ID")
                abort(500)
            return redirect(url_for("new_tasting", wine_id=wine_id), code=303)

        return render_wine_page({}, form_only=True)

    @app.route("/wines/<int:wine_id>/edit", methods=["GET", "POST"])
    def edit_wine(wine_id: int):
        wine = get_wine(wine_id)
        if wine is None:
            abort(404)

        if request.method == "POST":
            values, errors, database_error, _created_wine_id = save_wine(
                request.form, wine_id
            )
            if database_error:
                return (
                    render_wine_page(
                        values,
                        errors=[],
                        editing_wine=wine,
                        database_error=database_error,
                    ),
                    500,
                )
            if errors:
                return (
                    render_wine_page(values, errors, editing_wine=wine),
                    400,
                )
            return redirect(url_for("index", updated="1"), code=303)

        values = {field: wine[field] for field, _label in WINE_FIELDS}
        values.update(
            jahrgang=str(wine["jahrgang"]),
            winery_id=str(wine["winery_id"]),
            new_winery="",
        )
        return render_wine_page(values, editing_wine=wine)

    @app.route("/wines/<int:wine_id>/tastings/new", methods=["GET", "POST"])
    def new_tasting(wine_id: int):
        wine = get_wine(wine_id)
        if wine is None:
            abort(404)

        if request.method == "POST":
            values, errors, database_error = save_tasting(request.form, wine_id)
            if database_error:
                return (
                    render_tasting_form(
                        wine, values, [], database_error=database_error
                    ),
                    500,
                )
            if errors:
                return render_tasting_form(wine, values, errors), 400
            return redirect(url_for("tastings", tasting_created="1"), code=303)

        return render_tasting_form(
            wine,
            {
                "tasting_date": date.today().isoformat(),
                "location": "",
                "rating": "",
                "notes": "",
                "detailed_tasting": empty_detailed_tasting(),
            },
        )

    @app.route("/tastings/<int:tasting_id>/edit", methods=["GET", "POST"])
    def edit_tasting(tasting_id: int):
        tasting = get_tasting(tasting_id)
        if tasting is None:
            abort(404)
        wine = get_wine(tasting["wine_id"])
        if wine is None:
            abort(404)

        if request.method == "POST":
            values, errors, database_error = save_tasting(
                request.form, tasting["wine_id"], tasting_id=tasting_id
            )
            if database_error:
                return (
                    render_tasting_form(
                        wine,
                        values,
                        [],
                        editing_tasting=tasting,
                        database_error=database_error,
                    ),
                    500,
                )
            if errors:
                return (
                    render_tasting_form(wine, values, errors, editing_tasting=tasting),
                    400,
                )
            return redirect(url_for("tastings", tasting_updated="1"), code=303)

        return render_tasting_form(
            wine,
            {
                "tasting_date": tasting["tasting_date"] or "",
                "location": tasting["location"] or "",
                "rating": str(tasting["rating"]),
                "notes": tasting["notes"] or "",
                "detailed_tasting": load_detailed_tasting(tasting["detailed_tasting"]),
            },
            editing_tasting=tasting,
        )

    @app.route("/tastings", methods=["GET"])
    def tastings():
        return render_tastings_page()

    @app.route("/tastings/new", methods=["GET", "POST"])
    def start_tasting():
        wines = (
            get_db()
            .execute("SELECT id, name, jahrgang FROM wines ORDER BY name")
            .fetchall()
        )
        errors: list[str] = []
        selected_wine_id = ""

        if request.method == "POST":
            selected_wine_id = request.form.get("wine_id", "").strip()
            try:
                wine_id = int(selected_wine_id)
            except ValueError:
                errors.append("Bitte wähle einen Wein aus.")
            else:
                wine = (
                    get_db()
                    .execute("SELECT id FROM wines WHERE id = ?", (wine_id,))
                    .fetchone()
                )
                if wine is None:
                    errors.append("Der ausgewählte Wein existiert nicht.")
                else:
                    return redirect(url_for("new_tasting", wine_id=wine_id), code=303)

        return render_template(
            "tasting_start.html",
            wines=wines,
            errors=errors,
            selected_wine_id=selected_wine_id,
        ), (400 if errors else 200)

    @app.post("/wines/<int:wine_id>/delete")
    def delete_wine(wine_id: int):
        db = get_db()
        try:
            cursor = db.execute("DELETE FROM wines WHERE id = ?", (wine_id,))
            if cursor.rowcount == 0:
                abort(404)
            db.commit()
        except sqlite3.Error:
            db.rollback()
            current_app.logger.exception("Could not delete wine")
            return (
                render_wine_page(
                    {},
                    [],
                    database_error=(
                        "Der Wein konnte wegen eines Datenbankfehlers nicht "
                        "gelöscht werden."
                    ),
                ),
                500,
            )
        return redirect(url_for("index", wine_deleted="1"), code=303)

    @app.post("/tastings/<int:tasting_id>/delete")
    def delete_tasting(tasting_id: int):
        db = get_db()
        try:
            cursor = db.execute("DELETE FROM tastings WHERE id = ?", (tasting_id,))
            if cursor.rowcount == 0:
                abort(404)
            db.commit()
        except sqlite3.Error:
            db.rollback()
            current_app.logger.exception("Could not delete tasting")
            return (
                render_tastings_page(
                    database_error=(
                        "Die Degustation konnte wegen eines Datenbankfehlers "
                        "nicht gelöscht werden."
                    ),
                ),
                500,
            )
        return redirect(url_for("tastings", tasting_deleted="1"), code=303)

    return app


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        db = sqlite3.connect(current_app.config["DATABASE"])
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys = ON")
        g.db = db
    return g.db


def init_db(app: Flask) -> None:
    database_path = Path(app.config["DATABASE"])
    database_path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(database_path)) as db:
        db.execute("PRAGMA foreign_keys = ON")
        db.execute("""
            CREATE TABLE IF NOT EXISTS wineries (
                id INTEGER PRIMARY KEY,
                name VARCHAR(100) NOT NULL COLLATE NOCASE UNIQUE
            )
            """)
        db.execute(
            "INSERT OR IGNORE INTO wineries (name) VALUES (?)",
            ("Unbekannt",),
        )
        unknown_winery_id = db.execute(
            "SELECT id FROM wineries WHERE name = ? COLLATE NOCASE",
            ("Unbekannt",),
        ).fetchone()[0]

        existing_tables = {
            row[0]
            for row in db.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        }
        if "wines" not in existing_tables:
            create_wines_table(db)
        else:
            wine_columns = {row[1] for row in db.execute("PRAGMA table_info(wines)")}
            if "winery_id" not in wine_columns:
                db.execute("ALTER TABLE wines RENAME TO wines_before_winery")
                create_wines_table(db)
                legacy_columns = {
                    row[1]
                    for row in db.execute("PRAGMA table_info(wines_before_winery)")
                }
                legacy_rating = "rating" in legacy_columns
                legacy_notes = "notizen" in legacy_columns
                select_columns = [
                    "id",
                    "name",
                    "rebsorte",
                    "jahrgang",
                    "herkunftsort",
                ]
                select_columns.append("?")
                select_columns.append("rating" if legacy_rating else "NULL")
                select_columns.append("notizen" if legacy_notes else "NULL")
                db.execute(
                    f"""
                    INSERT INTO wines
                        (id, name, rebsorte, jahrgang, herkunftsort, winery_id,
                         legacy_rating, legacy_notes)
                    SELECT {", ".join(select_columns)}
                    FROM wines_before_winery
                    """,
                    (unknown_winery_id,),
                )
                db.execute("DROP TABLE wines_before_winery")
                wine_columns = {
                    row[1] for row in db.execute("PRAGMA table_info(wines)")
                }

        db.execute("""
            CREATE TABLE IF NOT EXISTS tastings (
                id INTEGER PRIMARY KEY,
                wine_id INTEGER NOT NULL REFERENCES wines(id) ON DELETE CASCADE,
                tasting_date TEXT,
                location VARCHAR(100),
                rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
                notes TEXT,
                detailed_tasting TEXT
            )
            """)
        tasting_columns = {row[1] for row in db.execute("PRAGMA table_info(tastings)")}
        if "detailed_tasting" not in tasting_columns:
            db.execute("ALTER TABLE tastings ADD COLUMN detailed_tasting TEXT")

        wine_columns = {row[1] for row in db.execute("PRAGMA table_info(wines)")}
        if "legacy_rating" in wine_columns:
            db.execute("""
                INSERT INTO tastings (wine_id, tasting_date, location, rating, notes)
                SELECT id, '2026-10-31', NULL, legacy_rating, legacy_notes
                FROM wines
                WHERE legacy_rating IS NOT NULL
                """)
            db.execute("ALTER TABLE wines DROP COLUMN legacy_rating")
            db.execute("ALTER TABLE wines DROP COLUMN legacy_notes")
        elif "rating" in wine_columns:
            db.execute("""
                INSERT INTO tastings (wine_id, tasting_date, location, rating, notes)
                SELECT id, '2026-10-31', NULL, rating, notizen
                FROM wines
                """)
            db.execute("ALTER TABLE wines DROP COLUMN rating")
            db.execute("ALTER TABLE wines DROP COLUMN notizen")

        db.commit()


def create_wines_table(db: sqlite3.Connection) -> None:
    db.execute("""
        CREATE TABLE wines (
            id INTEGER PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            rebsorte VARCHAR(100) NOT NULL,
            jahrgang INTEGER NOT NULL,
            herkunftsort VARCHAR(100) NOT NULL,
            winery_id INTEGER NOT NULL REFERENCES wineries(id),
            legacy_rating INTEGER,
            legacy_notes TEXT
        )
        """)


def get_wine(wine_id: int) -> sqlite3.Row | None:
    return (
        get_db()
        .execute(
            """
        SELECT wines.id, wines.name, wines.rebsorte, wines.jahrgang,
               wines.herkunftsort, wines.winery_id, wineries.name AS winery_name
        FROM wines
        JOIN wineries ON wineries.id = wines.winery_id
        WHERE wines.id = ?
        """,
            (wine_id,),
        )
        .fetchone()
    )


def validate_wine_form(form: Mapping[str, str]) -> tuple[dict[str, str], list[str]]:
    values = {
        "name": form.get("name", "").strip(),
        "rebsorte": form.get("rebsorte", "").strip(),
        "jahrgang": form.get("jahrgang", "").strip(),
        "herkunftsort": form.get("herkunftsort", "").strip(),
        "winery_id": form.get("winery_id", "").strip(),
        "new_winery": form.get("new_winery", "").strip(),
    }
    errors = []

    for field, label in WINE_FIELDS:
        value = values[field]
        if not value:
            errors.append(f"{label} ist erforderlich.")
        elif len(value) > 100:
            errors.append(f"{label} darf höchstens 100 Zeichen enthalten.")

    try:
        vintage = int(values["jahrgang"])
    except ValueError:
        errors.append("Der Jahrgang muss eine Ganzzahl sein.")
    else:
        if vintage > date.today().year:
            errors.append(f"Der Jahrgang darf höchstens {date.today().year} sein.")

    if values["new_winery"] and values["winery_id"]:
        errors.append("Bitte wähle einen Winzer oder gib einen neuen Namen ein.")
    elif not values["new_winery"] and not values["winery_id"]:
        errors.append("Ein Winzer ist erforderlich.")
    elif values["new_winery"] and len(values["new_winery"]) > 100:
        errors.append("Der Winzername darf höchstens 100 Zeichen enthalten.")
    elif values["winery_id"]:
        try:
            int(values["winery_id"])
        except ValueError:
            errors.append("Bitte wähle einen gültigen Winzer aus.")

    return values, errors


def save_wine(
    form: Mapping[str, str], wine_id: int | None = None
) -> tuple[dict[str, str], list[str], str | None, int | None]:
    values, errors = validate_wine_form(form)
    if errors:
        return values, errors, None, None

    db = get_db()
    created_wine_id = None
    try:
        if values["new_winery"]:
            winery = db.execute(
                "SELECT id FROM wineries WHERE name = ? COLLATE NOCASE",
                (values["new_winery"],),
            ).fetchone()
            if winery is None:
                cursor = db.execute(
                    "INSERT INTO wineries (name) VALUES (?)",
                    (values["new_winery"],),
                )
                winery_id = cursor.lastrowid
            else:
                winery_id = winery["id"]
        else:
            winery_id = int(values["winery_id"])
            winery = db.execute(
                "SELECT id FROM wineries WHERE id = ?",
                (winery_id,),
            ).fetchone()
            if winery is None:
                return (
                    values,
                    ["Der ausgewählte Winzer existiert nicht."],
                    None,
                    None,
                )

        wine_values = (
            values["name"],
            values["rebsorte"],
            int(values["jahrgang"]),
            values["herkunftsort"],
            winery_id,
        )
        if wine_id is None:
            cursor = db.execute(
                """
                INSERT INTO wines
                    (name, rebsorte, jahrgang, herkunftsort, winery_id)
                VALUES (?, ?, ?, ?, ?)
                """,
                wine_values,
            )
            created_wine_id = cursor.lastrowid
        else:
            cursor = db.execute(
                """
                UPDATE wines
                SET name = ?, rebsorte = ?, jahrgang = ?, herkunftsort = ?,
                    winery_id = ?
                WHERE id = ?
                """,
                (*wine_values, wine_id),
            )
            if cursor.rowcount == 0:
                db.rollback()
                abort(404)
        db.commit()
    except sqlite3.Error:
        db.rollback()
        current_app.logger.exception("Could not save wine")
        return (
            values,
            [],
            "Der Wein konnte wegen eines Datenbankfehlers nicht gespeichert werden.",
            None,
        )

    return values, [], None, created_wine_id


def validate_tasting_form(
    form: MultiDict[str, str],
) -> tuple[dict[str, Any], list[str]]:
    values = {
        "tasting_date": form.get("tasting_date", "").strip(),
        "location": form.get("location", "").strip(),
        "rating": form.get("rating", "").strip(),
        "notes": form.get("notes", "").strip(),
    }
    errors = []
    detailed_tasting = {}
    for group in TASTING_DETAIL_GROUPS:
        selected = form.getlist(f"detail_{group['key']}")
        allowed_values = {value for value, _label in group["options"]}
        if any(value not in allowed_values for value in selected):
            errors.append(f"Ungültige Auswahl bei „{group['label']}“.")
        elif not group["multiple"] and len(selected) > 1:
            errors.append(f"Bitte wähle bei „{group['label']}“ höchstens eine Option.")
        detailed_tasting[group["key"]] = selected
    values["detailed_tasting"] = detailed_tasting

    try:
        parsed_date = date.fromisoformat(values["tasting_date"])
        if parsed_date.isoformat() != values["tasting_date"]:
            raise ValueError
    except ValueError:
        errors.append("Bitte gib ein gültiges Degustationsdatum an.")
    else:
        if parsed_date > date.today():
            errors.append("Das Degustationsdatum darf nicht in der Zukunft liegen.")

    if not values["location"]:
        errors.append("Der Ort ist erforderlich.")
    elif len(values["location"]) > 100:
        errors.append("Der Ort darf höchstens 100 Zeichen enthalten.")

    try:
        rating = int(values["rating"])
    except ValueError:
        errors.append("Die Bewertung muss eine Ganzzahl von 1 bis 5 sein.")
    else:
        if not 1 <= rating <= 5:
            errors.append("Die Bewertung muss zwischen 1 und 5 liegen.")

    return values, errors


def get_tasting(tasting_id: int) -> sqlite3.Row | None:
    return (
        get_db()
        .execute(
            """
        SELECT id, wine_id, tasting_date, location, rating, notes, detailed_tasting
        FROM tastings
        WHERE id = ?
        """,
            (tasting_id,),
        )
        .fetchone()
    )


def save_tasting(
    form: MultiDict[str, str],
    wine_id: int,
    *,
    tasting_id: int | None = None,
) -> tuple[dict[str, Any], list[str], str | None]:
    values, errors = validate_tasting_form(form)
    if errors:
        return values, errors, None

    db = get_db()
    try:
        if tasting_id is None:
            db.execute(
                """
                INSERT INTO tastings
                    (wine_id, tasting_date, location, rating, notes, detailed_tasting)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    wine_id,
                    values["tasting_date"],
                    values["location"],
                    int(values["rating"]),
                    values["notes"] or None,
                    dump_detailed_tasting(values["detailed_tasting"]),
                ),
            )
        else:
            cursor = db.execute(
                """
                UPDATE tastings
                SET tasting_date = ?, location = ?, rating = ?, notes = ?,
                    detailed_tasting = ?
                WHERE id = ? AND wine_id = ?
                """,
                (
                    values["tasting_date"],
                    values["location"],
                    int(values["rating"]),
                    values["notes"] or None,
                    dump_detailed_tasting(values["detailed_tasting"]),
                    tasting_id,
                    wine_id,
                ),
            )
            if cursor.rowcount == 0:
                db.rollback()
                abort(404)
        db.commit()
    except sqlite3.Error:
        db.rollback()
        current_app.logger.exception("Could not save tasting")
        return (
            values,
            [],
            "Die Degustation konnte wegen eines Datenbankfehlers nicht "
            "gespeichert werden.",
        )

    return values, [], None


def render_tasting_form(
    wine: sqlite3.Row,
    values: Mapping[str, Any],
    errors: list[str] | None = None,
    *,
    editing_tasting: sqlite3.Row | None = None,
    database_error: str | None = None,
):
    return render_template(
        "tasting_form.html",
        wine=wine,
        values=values,
        errors=errors or [],
        database_error=database_error,
        editing_tasting=editing_tasting,
        today=date.today().isoformat(),
        tasting_detail_groups=TASTING_DETAIL_GROUPS,
    )


def render_tastings_page(database_error: str | None = None):
    tastings = []
    if database_error is None:
        tastings = (
            get_db()
            .execute("""
            SELECT tastings.id, tastings.tasting_date, tastings.location,
                   tastings.rating, tastings.notes, wines.id AS wine_id,
                   wines.name AS wine_name, wines.jahrgang,
                   wineries.name AS winery_name
            FROM tastings
            JOIN wines ON wines.id = tastings.wine_id
            JOIN wineries ON wineries.id = wines.winery_id
            ORDER BY tastings.tasting_date DESC, tastings.id DESC
            """)
            .fetchall()
        )
    return render_template(
        "tastings.html",
        tastings=tastings,
        database_error=database_error,
        tasting_created=request.args.get("tasting_created") == "1",
        tasting_updated=request.args.get("tasting_updated") == "1",
        tasting_deleted=request.args.get("tasting_deleted") == "1",
    )


def render_wine_page(
    values: Mapping[str, Any],
    errors: list[str] | None = None,
    *,
    editing_wine: sqlite3.Row | None = None,
    database_error: str | None = None,
    form_only: bool = False,
):
    db = get_db()
    selected_winery_id = values.get(
        "winery_id",
        str(editing_wine["winery_id"]) if editing_wine is not None else "",
    )
    wineries = []
    wines = []
    if database_error is None:
        wineries = db.execute("SELECT id, name FROM wineries ORDER BY name").fetchall()
        if editing_wine is None:
            wine_rows = db.execute("""
                SELECT wines.id, wines.name, wines.rebsorte, wines.jahrgang,
                       wines.herkunftsort, wineries.name AS winery_name
                FROM wines
                JOIN wineries ON wineries.id = wines.winery_id
                ORDER BY wines.id DESC
                """).fetchall()
            wines = [dict(wine) | {"tastings": []} for wine in wine_rows]
            tastings = db.execute("""
                SELECT id, wine_id, tasting_date, location, rating, notes
                FROM tastings
                ORDER BY tasting_date DESC, id DESC
                """).fetchall()
            wine_by_id = {wine["id"]: wine for wine in wines}
            for tasting in tastings:
                wine_by_id[tasting["wine_id"]]["tastings"].append(tasting)

    return render_template(
        "index.html",
        wines=wines,
        values=values,
        errors=errors or [],
        created=request.args.get("created") == "1",
        updated=request.args.get("updated") == "1",
        tasting_created=request.args.get("tasting_created") == "1",
        tasting_updated=request.args.get("tasting_updated") == "1",
        wine_deleted=request.args.get("wine_deleted") == "1",
        tasting_deleted=request.args.get("tasting_deleted") == "1",
        database_error=database_error,
        editing_wine=editing_wine,
        selected_winery_id=str(selected_winery_id),
        wineries=wineries,
        current_year=date.today().year,
        form_only=form_only,
    )


app = create_app()
