# app.py
from flask import Flask
from models import db


def create_app():
    app = Flask(__name__)
    # Konfiguration der SQLite-Datenbank als 'wines.db'
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///wines.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Verbinde die App mit der Datenbank
    db.init_app(app)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
