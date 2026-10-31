import sqlite3
from contextlib import closing

import pytest

from app import create_app


@pytest.fixture
def client(tmp_path):
    app = create_app(
        {
            "TESTING": True,
            "DATABASE": tmp_path / "wines.db",
        }
    )
    return app.test_client()


def insert_wine(database_path, name="Pinot Noir"):
    with closing(sqlite3.connect(database_path)) as db:
        winery_id = db.execute(
            "SELECT id FROM wineries WHERE name = 'Unbekannt'"
        ).fetchone()[0]
        wine_id = db.execute(
            """
            INSERT INTO wines
                (name, rebsorte, jahrgang, herkunftsort, winery_id)
            VALUES (?, ?, ?, ?, ?)
            """,
            (name, "Blauburgunder", 2022, "Zuerich", winery_id),
        ).lastrowid
        db.commit()
    return wine_id


def test_home_page_shows_empty_state_and_wine_form(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"Noch sind keine Weine erfasst." in response.data
    assert b'name="name"' in response.data
    assert b'name="rating"' not in response.data


def test_post_saves_wine_separately_from_tastings(client, tmp_path):
    response = client.post(
        "/",
        data={
            "name": "Pinot Noir",
            "rebsorte": "Blauburgunder",
            "jahrgang": "2022",
            "herkunftsort": "Zuerich",
            "new_winery": "Weingut Beispiel",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Der Wein wurde gespeichert." in response.data
    assert b"Pinot Noir" in response.data
    with closing(sqlite3.connect(tmp_path / "wines.db")) as db:
        saved = db.execute(
            "SELECT name, rebsorte, jahrgang, herkunftsort FROM wines"
        ).fetchone()
        winery = db.execute(
            "SELECT wineries.name FROM wines "
            "JOIN wineries ON wineries.id = wines.winery_id"
        ).fetchone()
        tasting_count = db.execute("SELECT COUNT(*) FROM tastings").fetchone()[0]
    assert saved == ("Pinot Noir", "Blauburgunder", 2022, "Zuerich")
    assert winery == ("Weingut Beispiel",)
    assert tasting_count == 0


def test_post_reuses_winery_without_creating_case_variant_duplicate(client, tmp_path):
    wine = {
        "rebsorte": "Pinot Noir",
        "jahrgang": "2022",
        "herkunftsort": "Zuerich",
    }
    client.post("/", data={"name": "Erster Wein", **wine, "new_winery": "Weingut Aare"})
    client.post(
        "/", data={"name": "Zweiter Wein", **wine, "new_winery": "weingut aare"}
    )

    with closing(sqlite3.connect(client.application.config["DATABASE"])) as db:
        wineries = db.execute(
            "SELECT COUNT(*) FROM wineries WHERE name = ? COLLATE NOCASE",
            ("Weingut Aare",),
        ).fetchone()[0]
    assert wineries == 1


def test_post_requires_wine_name(client):
    response = client.post(
        "/",
        data={
            "name": " ",
            "rebsorte": "Blauburgunder",
            "jahrgang": "2022",
            "herkunftsort": "Zuerich",
            "winery_id": "1",
        },
    )

    assert response.status_code == 400
    assert "Name ist erforderlich.".encode() in response.data


def test_post_shows_database_error_when_wine_cannot_be_saved(tmp_path):
    database_path = tmp_path / "wines.db"
    app = create_app({"TESTING": True, "DATABASE": database_path})
    with closing(sqlite3.connect(database_path)) as db:
        db.execute("""
            CREATE TRIGGER reject_wine_insert
            BEFORE INSERT ON wines
            BEGIN
                SELECT RAISE(ABORT, 'test database error');
            END
            """)
    response = app.test_client().post(
        "/",
        data={
            "name": "Pinot Noir",
            "rebsorte": "Blauburgunder",
            "jahrgang": "2022",
            "herkunftsort": "Zuerich",
            "winery_id": "1",
        },
    )

    assert response.status_code == 500
    assert "Datenbankfehler".encode() in response.data


def test_edit_updates_wine_without_changing_its_tastings(client, tmp_path):
    wine_id = insert_wine(tmp_path / "wines.db", "Pinot")
    with closing(sqlite3.connect(tmp_path / "wines.db")) as db:
        db.execute(
            """
            INSERT INTO tastings (wine_id, tasting_date, location, rating, notes)
            VALUES (?, ?, ?, ?, ?)
            """,
            (wine_id, "2026-10-31", "Bern", 4, "Fruchtig"),
        )
        winery_id = db.execute(
            "SELECT winery_id FROM wines WHERE id = ?", (wine_id,)
        ).fetchone()[0]
        db.commit()

    response = client.post(
        f"/wines/{wine_id}/edit",
        data={
            "name": "Pinot Noir",
            "rebsorte": "Blauburgunder",
            "jahrgang": "2023",
            "herkunftsort": "Zuerich",
            "winery_id": str(winery_id),
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert "Die Änderungen wurden gespeichert.".encode() in response.data
    with closing(sqlite3.connect(tmp_path / "wines.db")) as db:
        saved = db.execute(
            "SELECT name, jahrgang FROM wines WHERE id = ?", (wine_id,)
        ).fetchone()
        tasting_count = db.execute(
            "SELECT COUNT(*) FROM tastings WHERE wine_id = ?", (wine_id,)
        ).fetchone()[0]
    assert saved == ("Pinot Noir", 2023)
    assert tasting_count == 1


def test_edit_page_shows_current_wine_and_winery(client, tmp_path):
    wine_id = insert_wine(tmp_path / "wines.db")

    response = client.get(f"/wines/{wine_id}/edit")

    assert response.status_code == 200
    assert b"Unbekannt" in response.data
    assert "Änderungen speichern".encode() in response.data
    assert b'name="rating"' not in response.data


def test_wine_list_uses_accessible_pencil_edit_link(client, tmp_path):
    insert_wine(tmp_path / "wines.db")

    response = client.get("/")

    assert response.status_code == 200
    assert b'title="Bearbeiten"' in response.data
    assert b'aria-label="Bearbeiten"' in response.data
    assert b'<svg viewBox="0 0 24 24"' in response.data


def test_edit_unknown_wine_returns_404(client):
    assert client.get("/wines/999/edit").status_code == 404


def test_multiple_tastings_can_be_saved_for_the_same_wine(client, tmp_path):
    wine_id = insert_wine(tmp_path / "wines.db")
    tasting_one = {
        "tasting_date": "2026-10-30",
        "location": "Bern",
        "rating": "3",
        "notes": "Frisch",
    }
    tasting_two = {
        "tasting_date": "2026-10-31",
        "location": "Zuerich",
        "rating": "5",
        "notes": "Sehr komplex",
    }

    first = client.post(
        f"/wines/{wine_id}/tastings/new",
        data=tasting_one,
        follow_redirects=True,
    )
    second = client.post(
        f"/wines/{wine_id}/tastings/new",
        data=tasting_two,
        follow_redirects=True,
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert "Die Degustation wurde gespeichert.".encode() in second.data
    assert b"2026-10-30" in second.data
    assert b"2026-10-31" in second.data
    with closing(sqlite3.connect(tmp_path / "wines.db")) as db:
        tastings = db.execute(
            """
            SELECT tasting_date, location, rating, notes
            FROM tastings WHERE wine_id = ? ORDER BY tasting_date
            """,
            (wine_id,),
        ).fetchall()
    assert tastings == [
        ("2026-10-30", "Bern", 3, "Frisch"),
        ("2026-10-31", "Zuerich", 5, "Sehr komplex"),
    ]


def test_tasting_form_shows_selected_wine(client, tmp_path):
    wine_id = insert_wine(tmp_path / "wines.db", "Pinot")

    response = client.get(f"/wines/{wine_id}/tastings/new")

    assert response.status_code == 200
    assert b"Pinot" in response.data
    assert b'name="tasting_date"' in response.data
    assert b'name="location"' in response.data


def test_tasting_requires_valid_date_location_and_rating(client, tmp_path):
    wine_id = insert_wine(tmp_path / "wines.db")

    response = client.post(
        f"/wines/{wine_id}/tastings/new",
        data={
            "tasting_date": "not-a-date",
            "location": " ",
            "rating": "6",
        },
    )

    assert response.status_code == 400
    assert "gültiges Degustationsdatum".encode() in response.data
    assert "Ort ist erforderlich".encode() in response.data
    assert "zwischen 1 und 5".encode() in response.data
    with closing(sqlite3.connect(tmp_path / "wines.db")) as db:
        assert db.execute("SELECT COUNT(*) FROM tastings").fetchone()[0] == 0


def test_new_tasting_for_unknown_wine_returns_404(client):
    assert client.get("/wines/999/tastings/new").status_code == 404


def test_existing_wines_migrate_rating_and_notes_to_first_tasting(tmp_path):
    database_path = tmp_path / "legacy-wines.db"
    with closing(sqlite3.connect(database_path)) as db:
        db.execute("""
            CREATE TABLE wineries (
                id INTEGER PRIMARY KEY,
                name VARCHAR(100) NOT NULL COLLATE NOCASE UNIQUE
            )
            """)
        db.execute("INSERT INTO wineries (id, name) VALUES (9, 'Weingut Alt')")
        db.execute("""
            CREATE TABLE wines (
                id INTEGER PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                rebsorte VARCHAR(100) NOT NULL,
                jahrgang INTEGER NOT NULL,
                herkunftsort VARCHAR(100) NOT NULL,
                rating INTEGER NOT NULL,
                notizen TEXT,
                winery_id INTEGER NOT NULL REFERENCES wineries(id)
            )
            """)
        db.execute("""
            INSERT INTO wines
                (id, name, rebsorte, jahrgang, herkunftsort, rating, notizen,
                 winery_id)
            VALUES (17, 'Pinot', 'Blauburgunder', 2020, 'Basel', 3, 'Alt', 9)
            """)
        db.commit()

    create_app({"DATABASE": database_path})
    create_app({"DATABASE": database_path})

    with closing(sqlite3.connect(database_path)) as db:
        migrated = db.execute("""
            SELECT tastings.wine_id, tastings.tasting_date, tastings.location,
                   tastings.rating, tastings.notes, wineries.name
            FROM tastings
            JOIN wines ON wines.id = tastings.wine_id
            JOIN wineries ON wineries.id = wines.winery_id
            """).fetchall()
        wine_columns = {row[1] for row in db.execute("PRAGMA table_info(wines)")}
    assert migrated == [(17, "2026-10-31", None, 3, "Alt", "Weingut Alt")]
    assert "rating" not in wine_columns
    assert "notizen" not in wine_columns


def test_original_wines_without_winery_are_migrated(tmp_path):
    database_path = tmp_path / "original-wines.db"
    with closing(sqlite3.connect(database_path)) as db:
        db.execute("""
            CREATE TABLE wines (
                id INTEGER PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                rebsorte VARCHAR(100) NOT NULL,
                jahrgang INTEGER NOT NULL,
                herkunftsort VARCHAR(100) NOT NULL,
                rating INTEGER NOT NULL,
                notizen TEXT
            )
            """)
        db.execute("""
            INSERT INTO wines
                (id, name, rebsorte, jahrgang, herkunftsort, rating, notizen)
            VALUES (7, 'Altwein', 'Riesling', 2019, 'Basel', 4, 'Gut')
            """)
        db.commit()

    create_app({"DATABASE": database_path})

    with closing(sqlite3.connect(database_path)) as db:
        saved = db.execute("""
            SELECT wines.id, wines.name, wineries.name, tastings.rating,
                   tastings.notes, tastings.tasting_date
            FROM wines
            JOIN wineries ON wineries.id = wines.winery_id
            JOIN tastings ON tastings.wine_id = wines.id
            """).fetchone()
    assert saved == (7, "Altwein", "Unbekannt", 4, "Gut", "2026-10-31")
