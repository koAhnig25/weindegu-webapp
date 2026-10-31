# seed.py
from models import Wine, db

from app import app


def seed_database():
    # Wir brauchen den App-Kontext, um auf die Datenbank zuzugreifen
    with app.app_context():
        print("Lösche alte Tabellen (falls vorhanden)...")
        db.drop_all()

        print("Erstelle neue Tabellen...")
        db.create_all()

        print("Füge Testdatensätze ein...")
        weine = [
            Wine(
                name="Château Margaux",
                rebsorte="Cabernet Sauvignon",
                jahrgang=2015,
                herkunftsort="Bordeaux",  # Findet die Wetter-API!
                rating=5,
                notizen="Hervorragender Jahrgang, sehr komplex.",
            ),
            Wine(
                name="Maienfelder Pinot Noir",
                rebsorte="Pinot Noir",
                jahrgang=2021,
                herkunftsort="Maienfeld",  # Schweizer Testfall
                rating=4,
                notizen="Fruchtig, leicht, perfekt für den Sommer.",
            ),
            Wine(
                name="Chianti Classico",
                rebsorte="Sangiovese",
                jahrgang=2019,
                herkunftsort="Florenz",
                rating=3,
                notizen="Solider Alltagswein, gute Säurestruktur.",
            ),
        ]

        # Fügt alle Weine zur Session hinzu und speichert sie in der DB
        db.session.add_all(weine)
        db.session.commit()

        print("Erfolgreich! Datenbank 'wines.db' wurde erstellt und befüllt.")


if __name__ == "__main__":
    seed_database()
