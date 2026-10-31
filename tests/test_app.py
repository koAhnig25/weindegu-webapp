import sqlite3
from contextlib import closing
from datetime import date, timedelta

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


def insert_tasting(database_path, wine_id, tasting_date="2026-10-31"):
    with closing(sqlite3.connect(database_path)) as db:
        tasting_id = db.execute(
            """
            INSERT INTO tastings (wine_id, tasting_date, location, rating, notes)
            VALUES (?, ?, ?, ?, ?)
            """,
            (wine_id, tasting_date, "Bern", 4, "Fruchtig"),
        ).lastrowid
        db.commit()
    return tasting_id


def test_home_page_shows_empty_state_and_wine_form(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"Noch sind keine Weine erfasst." in response.data
    assert b'name="name"' in response.data
    assert b'name="rating"' not in response.data


def test_wine_year_form_sets_maximum_to_current_year(client):
    response = client.get("/")

    assert f'max="{date.today().year}"'.encode() in response.data


def test_bootstrap_is_served_locally_and_used_by_pages(client, tmp_path):
    stylesheet = client.get("/static/vendor/bootstrap/bootstrap.min.css")
    wine_id = insert_wine(tmp_path / "wines.db")
    wine_page = client.get("/")
    tasting_page = client.get(f"/wines/{wine_id}/tastings/new")

    assert stylesheet.status_code == 200
    assert b"Bootstrap  v5.3.8" in stylesheet.data[:300]
    assert b"cdn.jsdelivr.net" not in wine_page.data
    assert b"vendor/bootstrap/bootstrap.min.css" in wine_page.data
    assert b"row g-3" in wine_page.data
    assert b"table-responsive" in wine_page.data
    assert b"vendor/bootstrap/bootstrap.min.css" in tasting_page.data
    assert b"form-control" in tasting_page.data


def test_tastings_overview_lists_tastings_newest_first(client, tmp_path):
    database_path = tmp_path / "wines.db"
    first_wine_id = insert_wine(database_path, "Erster Wein")
    second_wine_id = insert_wine(database_path, "Zweiter Wein")
    insert_tasting(database_path, first_wine_id, "2026-10-30")
    insert_tasting(database_path, second_wine_id, "2026-10-31")

    response = client.get("/tastings")

    assert response.status_code == 200
    assert b"Degustationen" in response.data
    assert b"Neue Degustation" in response.data
    assert b"Erster Wein" in response.data
    assert b"Zweiter Wein" in response.data
    assert b"Degustation bearbeiten" in response.data
    assert b"Degustation l\xc3\xb6schen" in response.data
    assert response.data.index(b"2026-10-31") < response.data.index(b"2026-10-30")


def test_tastings_overview_shows_empty_state_and_navigation(client):
    response = client.get("/tastings")

    assert response.status_code == 200
    assert b"Noch sind keine Degustationen erfasst." in response.data
    assert b'href="/"' in response.data
    assert b'href="/tastings"' in response.data


def test_start_tasting_offers_existing_and_new_wine_options(client, tmp_path):
    insert_wine(tmp_path / "wines.db", "Pinot")

    response = client.get("/tastings/new")

    assert response.status_code == 200
    assert b"Pinot (2022)" in response.data
    assert b"Neuen Wein erfassen" in response.data


def test_start_tasting_redirects_selected_wine_to_tasting_form(client, tmp_path):
    wine_id = insert_wine(tmp_path / "wines.db", "Pinot")

    response = client.post("/tastings/new", data={"wine_id": str(wine_id)})

    assert response.status_code == 303
    assert response.headers["Location"] == f"/wines/{wine_id}/tastings/new"


def test_start_tasting_requires_an_existing_wine(client):
    response = client.post("/tastings/new", data={"wine_id": "999"})

    assert response.status_code == 400
    assert b"existiert nicht" in response.data


def test_start_tasting_with_new_wine_continues_to_tasting_form(client, tmp_path):
    response = client.post(
        "/wines/new-for-tasting",
        data={
            "name": "Neuer Pinot",
            "rebsorte": "Blauburgunder",
            "jahrgang": "2022",
            "herkunftsort": "Zuerich",
            "new_winery": "Weingut Neu",
        },
    )

    assert response.status_code == 303
    assert response.headers["Location"].startswith("/wines/")
    wine_id = int(response.headers["Location"].split("/")[2])
    assert response.headers["Location"] == f"/wines/{wine_id}/tastings/new"
    with closing(sqlite3.connect(tmp_path / "wines.db")) as db:
        wine = db.execute("SELECT name FROM wines WHERE id = ?", (wine_id,)).fetchone()
    assert wine == ("Neuer Pinot",)
    tasting_page = client.get(response.headers["Location"])
    assert tasting_page.status_code == 200
    assert b"Neuer Pinot" in tasting_page.data


def test_invalid_new_wine_form_keeps_tasting_workflow_action(client):
    response = client.post(
        "/wines/new-for-tasting",
        data={"name": "", "rebsorte": "", "jahrgang": "", "herkunftsort": ""},
    )

    assert response.status_code == 400
    assert b'action="/wines/new-for-tasting"' in response.data


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


def test_post_rejects_wine_year_in_future(client):
    response = client.post(
        "/",
        data={
            "name": "Pinot Noir",
            "rebsorte": "Blauburgunder",
            "jahrgang": str(date.today().year + 1),
            "herkunftsort": "Zuerich",
            "winery_id": "1",
        },
    )

    assert response.status_code == 400
    assert f"höchstens {date.today().year}".encode() in response.data


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
    assert b'aria-label="Degustation hinzuf\xc3\xbcgen"' in response.data
    assert b'<path d="M12 5v14M5 12h14"></path>' in response.data


def test_wine_list_shows_delete_icon_and_confirmation(client, tmp_path):
    wine_id = insert_wine(tmp_path / "wines.db")
    insert_tasting(tmp_path / "wines.db", wine_id)

    response = client.get("/")

    assert response.status_code == 200
    assert b'aria-label="Wein l\xc3\xb6schen"' in response.data
    assert b'aria-label="Degustation l\xc3\xb6schen"' in response.data
    assert (
        b"alle zugeh\xc3\xb6rigen Degustationen wirklich l\xc3\xb6schen"
        in response.data
    )
    assert b"diese Degustation wirklich l\xc3\xb6schen" in response.data


def test_edit_unknown_wine_returns_404(client):
    assert client.get("/wines/999/edit").status_code == 404


def test_deleting_wine_also_deletes_all_its_tastings(client, tmp_path):
    database_path = tmp_path / "wines.db"
    wine_id = insert_wine(database_path)
    insert_tasting(database_path, wine_id, "2026-10-30")
    insert_tasting(database_path, wine_id, "2026-10-31")

    response = client.post(
        f"/wines/{wine_id}/delete",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert "Der Wein und seine Degustationen wurden gelöscht.".encode() in response.data
    with closing(sqlite3.connect(database_path)) as db:
        assert (
            db.execute(
                "SELECT COUNT(*) FROM wines WHERE id = ?", (wine_id,)
            ).fetchone()[0]
            == 0
        )
        assert (
            db.execute(
                "SELECT COUNT(*) FROM tastings WHERE wine_id = ?", (wine_id,)
            ).fetchone()[0]
            == 0
        )


def test_deleting_tasting_keeps_wine_and_other_tastings(client, tmp_path):
    database_path = tmp_path / "wines.db"
    wine_id = insert_wine(database_path)
    deleted_tasting_id = insert_tasting(database_path, wine_id, "2026-10-30")
    remaining_tasting_id = insert_tasting(database_path, wine_id, "2026-10-31")

    response = client.post(
        f"/tastings/{deleted_tasting_id}/delete",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert "Die Degustation wurde gelöscht.".encode() in response.data
    with closing(sqlite3.connect(database_path)) as db:
        assert (
            db.execute(
                "SELECT COUNT(*) FROM wines WHERE id = ?", (wine_id,)
            ).fetchone()[0]
            == 1
        )
        assert (
            db.execute(
                "SELECT COUNT(*) FROM tastings WHERE wine_id = ?", (wine_id,)
            ).fetchone()[0]
            == 1
        )
        assert (
            db.execute(
                "SELECT COUNT(*) FROM tastings WHERE id = ?", (remaining_tasting_id,)
            ).fetchone()[0]
            == 1
        )


@pytest.mark.parametrize(
    "path",
    ["/wines/999/delete", "/tastings/999/delete"],
)
def test_deleting_unknown_record_returns_404(client, path):
    assert client.post(path).status_code == 404


def test_deletion_routes_do_not_accept_get_requests(client):
    assert client.get("/wines/1/delete").status_code == 405
    assert client.get("/tastings/1/delete").status_code == 405


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


def test_tasting_form_limits_date_to_today(client, tmp_path):
    wine_id = insert_wine(tmp_path / "wines.db")

    response = client.get(f"/wines/{wine_id}/tastings/new")

    assert response.status_code == 200
    assert f'max="{date.today().isoformat()}"'.encode() in response.data


def test_tasting_edit_page_prefills_values_and_has_pencil_action(client, tmp_path):
    database_path = tmp_path / "wines.db"
    wine_id = insert_wine(database_path, "Pinot")
    tasting_id = insert_tasting(database_path, wine_id)

    response = client.get(f"/tastings/{tasting_id}/edit")

    assert response.status_code == 200
    assert b"Degustation bearbeiten" in response.data
    assert b'value="2026-10-31"' in response.data
    assert b'value="Bern"' in response.data
    assert b'value="4"' in response.data
    assert b">Fruchtig</textarea>" in response.data


def test_edit_tasting_updates_all_fields_without_adding_another(client, tmp_path):
    database_path = tmp_path / "wines.db"
    wine_id = insert_wine(database_path)
    tasting_id = insert_tasting(database_path, wine_id)

    response = client.post(
        f"/tastings/{tasting_id}/edit",
        data={
            "tasting_date": (date.today() - timedelta(days=1)).isoformat(),
            "location": "Basel",
            "rating": "5",
            "notes": "Noch besser",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert "Die Degustation wurde aktualisiert.".encode() in response.data
    with closing(sqlite3.connect(database_path)) as db:
        tastings = db.execute(
            """
            SELECT wine_id, tasting_date, location, rating, notes
            FROM tastings WHERE id = ?
            """,
            (tasting_id,),
        ).fetchall()
    assert tastings == [
        (
            wine_id,
            (date.today() - timedelta(days=1)).isoformat(),
            "Basel",
            5,
            "Noch besser",
        )
    ]


def test_edit_tasting_rejects_invalid_values_without_saving(client, tmp_path):
    database_path = tmp_path / "wines.db"
    wine_id = insert_wine(database_path)
    tasting_id = insert_tasting(database_path, wine_id)

    response = client.post(
        f"/tastings/{tasting_id}/edit",
        data={
            "tasting_date": "invalid",
            "location": "",
            "rating": "9",
            "notes": "Änderung",
        },
    )

    assert response.status_code == 400
    with closing(sqlite3.connect(database_path)) as db:
        tasting = db.execute(
            """
            SELECT tasting_date, location, rating, notes
            FROM tastings WHERE id = ?
            """,
            (tasting_id,),
        ).fetchone()
    assert tasting == ("2026-10-31", "Bern", 4, "Fruchtig")


def test_edit_unknown_tasting_returns_404(client):
    assert client.get("/tastings/999/edit").status_code == 404


def test_edit_tasting_route_rejects_patch(client, tmp_path):
    tasting_id = insert_tasting(
        tmp_path / "wines.db", insert_wine(tmp_path / "wines.db")
    )
    assert client.patch(f"/tastings/{tasting_id}/edit").status_code == 405


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


def test_tasting_rejects_date_in_future(client, tmp_path):
    wine_id = insert_wine(tmp_path / "wines.db")

    response = client.post(
        f"/wines/{wine_id}/tastings/new",
        data={
            "tasting_date": (date.today() + timedelta(days=1)).isoformat(),
            "location": "Bern",
            "rating": "4",
        },
    )

    assert response.status_code == 400
    assert (
        "Degustationsdatum darf nicht in der Zukunft liegen".encode() in response.data
    )
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
