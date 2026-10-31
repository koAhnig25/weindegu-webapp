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


def test_home_page_shows_empty_state_and_form(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"Noch sind keine Weine erfasst." in response.data
    assert b'name="name"' in response.data


def test_post_saves_wine_and_shows_it_in_the_list(client, tmp_path):
    response = client.post(
        "/",
        data={
            "name": "Pinot Noir",
            "rebsorte": "Blauburgunder",
            "jahrgang": "2022",
            "herkunftsort": "Zuerich",
            "rating": "4",
            "notizen": "Fruchtig",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Der Wein wurde gespeichert." in response.data
    assert b"Pinot Noir" in response.data
    with closing(sqlite3.connect(tmp_path / "wines.db")) as db:
        saved = db.execute(
            "SELECT name, rebsorte, jahrgang, herkunftsort, rating, notizen "
            "FROM wines"
        ).fetchone()
    assert saved == (
        "Pinot Noir",
        "Blauburgunder",
        2022,
        "Zuerich",
        4,
        "Fruchtig",
    )


def test_post_rejects_rating_outside_allowed_range(client, tmp_path):
    response = client.post(
        "/",
        data={
            "name": "Pinot Noir",
            "rebsorte": "Blauburgunder",
            "jahrgang": "2022",
            "herkunftsort": "Zuerich",
            "rating": "6",
        },
    )

    assert response.status_code == 400
    assert "zwischen 1 und 5".encode() in response.data
    with closing(sqlite3.connect(tmp_path / "wines.db")) as db:
        count = db.execute("SELECT COUNT(*) FROM wines").fetchone()[0]
    assert count == 0


def test_post_requires_name(client):
    response = client.post(
        "/",
        data={
            "name": " ",
            "rebsorte": "Blauburgunder",
            "jahrgang": "2022",
            "herkunftsort": "Zuerich",
            "rating": "4",
        },
    )

    assert response.status_code == 400
    assert "Name ist erforderlich.".encode() in response.data


def test_post_shows_database_error_when_wines_table_is_incompatible(tmp_path):
    database_path = tmp_path / "wines.db"
    with closing(sqlite3.connect(database_path)) as db:
        db.execute("CREATE TABLE wines (name TEXT)")

    app = create_app(
        {
            "TESTING": True,
            "DATABASE": database_path,
        }
    )
    response = app.test_client().post(
        "/",
        data={
            "name": "Pinot Noir",
            "rebsorte": "Blauburgunder",
            "jahrgang": "2022",
            "herkunftsort": "Zuerich",
            "rating": "4",
        },
    )

    assert response.status_code == 500
    assert "Datenbankfehler".encode() in response.data
