import sqlite3

from app import create_app, init_db


def seed_database() -> None:
    app = create_app()
    database_path = app.config["DATABASE"]

    init_db(app)
    with sqlite3.connect(database_path) as db:
        db.execute("PRAGMA foreign_keys = ON")
        db.execute("DELETE FROM tastings")
        db.execute("DELETE FROM wines")
        db.execute("DELETE FROM wineries")

        wineries = (
            ("Unbekannt",),
            ("Chateau Margaux",),
            ("Maienfelder Weinbau",),
            ("Chianti Classico",),
        )
        db.executemany("INSERT INTO wineries (name) VALUES (?)", wineries)

        winery_ids = {
            row[1]: row[0]
            for row in db.execute("SELECT id, name FROM wineries")
        }
        wines = (
            (
                "Chateau Margaux",
                "Cabernet Sauvignon",
                2015,
                "Bordeaux",
                winery_ids["Chateau Margaux"],
            ),
            (
                "Maienfelder Pinot Noir",
                "Pinot Noir",
                2021,
                "Maienfeld",
                winery_ids["Maienfelder Weinbau"],
            ),
            (
                "Chianti Classico",
                "Sangiovese",
                2019,
                "Florenz",
                winery_ids["Chianti Classico"],
            ),
        )
        db.executemany(
            """
            INSERT INTO wines
                (name, rebsorte, jahrgang, herkunftsort, winery_id)
            VALUES (?, ?, ?, ?, ?)
            """,
            wines,
        )

        wine_ids = {
            row[1]: row[0]
            for row in db.execute("SELECT id, name FROM wines")
        }
        tastings = (
            (
                wine_ids["Chateau Margaux"],
                "2026-10-31",
                "Bordeaux",
                5,
                "Hervorragender Jahrgang, sehr komplex.",
                None,
            ),
            (
                wine_ids["Maienfelder Pinot Noir"],
                "2026-10-31",
                "Maienfeld",
                4,
                "Fruchtig, leicht, perfekt fuer den Sommer.",
                None,
            ),
            (
                wine_ids["Chianti Classico"],
                "2026-10-31",
                "Florenz",
                3,
                "Solider Alltagswein, gute Saeurestruktur.",
                None,
            ),
        )
        db.executemany(
            """
            INSERT INTO tastings
                (wine_id, tasting_date, location, rating, notes, detailed_tasting)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            tastings,
        )

    print("Datenbank wurde mit 3 Beispielweinen und 3 Degustationen gefuellt.")


if __name__ == "__main__":
    seed_database()
