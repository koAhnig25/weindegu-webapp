"""Setzt die lokale Datenbank auf die Demodaten zurück.

Achtung: Löscht alle Weine, Winzer und Degustationen.
Aufruf (aus dem Projektordner): uv run python seed.py
"""

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from app import create_app, insert_demo_data  # noqa: E402


def seed_database() -> None:
    app = create_app({"DEMO_DATA": False})

    with sqlite3.connect(app.config["DATABASE"]) as db:
        db.execute("PRAGMA foreign_keys = ON")
        db.execute("DELETE FROM tastings")
        db.execute("DELETE FROM wines")
        db.execute("DELETE FROM wineries WHERE name != 'Unbekannt'")
        insert_demo_data(db)

    print("Datenbank wurde mit Demodaten gefüllt.")


if __name__ == "__main__":
    seed_database()
