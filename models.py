# models.py
from flask_sqlalchemy import SQLAlchemy

# Initialisiere das SQLAlchemy-Objekt (noch ohne App-Anbindung)
db = SQLAlchemy()


class Wine(db.Model):
    __tablename__ = "wines"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    rebsorte = db.Column(db.String(100), nullable=False)
    jahrgang = db.Column(db.Integer, nullable=False)
    # Sehr wichtig für eure Wetter-API: Ein realer Ortsname!
    herkunftsort = db.Column(db.String(100), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1 bis 5 Sterne
    notizen = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f"<Wine {self.name} ({self.jahrgang})>"
