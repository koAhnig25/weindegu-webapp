# Weindegustation-WebApp

Eine kleine Flask-Webanwendung zum Erfassen von Weinen und Degustationen.
Die Anwendung speichert die Daten in einer lokalen SQLite-Datenbank und zeigt
zusätzlich historische Sommerwetterdaten zum Jahrgang und Herkunftsort an.

## Voraussetzungen

- Python
- [uv](https://docs.astral.sh/uv/) als Python-Abhängigkeitsmanager

## App lokal starten

Öffne ein Terminal im Projektordner `weindegu-webapp` und installiere zuerst
die Abhängigkeiten:

```powershell
uv sync
```

Starte die Anwendung unter Windows mit Waitress:

```powershell
$env:PYTHONPATH="$PWD\src"
uv run waitress-serve --listen=127.0.0.1:8080 app:app
```

Die Anwendung läuft danach unter:

```text
http://127.0.0.1:8080/
```

Der Terminalprozess muss während der Nutzung weiterlaufen. Zum Beenden drücke
`Strg+C`.

Für einen anderen Port ändere nur die Adresse:

```powershell
$env:PYTHONPATH="$PWD\src"
uv run waitress-serve --listen=127.0.0.1:8081 app:app
```

Die Anwendung ist dann unter `http://127.0.0.1:8081/` erreichbar.

Die Linux-Alternative ist Gunicorn:

```bash
PYTHONPATH=src uv run gunicorn --bind 0.0.0.0:8000 app:app
```

## Hauptfunktionen

### Weinmodus

Im Weinmodus können Namen, Rebsorten, Jahrgänge, Herkunftsorte und Winzer
erfasst, bearbeitet oder gelöscht werden.

Beim Speichern oder Aktualisieren eines Weins wird anhand des Herkunftsorts
eine Geoposition ermittelt. Danach werden historische Daten für die
Sommermonate geladen:

- Nördliche Hemisphäre: Juni bis August
- Südliche Hemisphäre: Februar bis April

Die Anzeige enthält die mittlere Tagestemperatur und die gesamte
Niederschlagsmenge. Zusätzlich zeigt die Anwendung eine konservative,
grobe Einschätzung von Wärme-, Trockenheits- und Niederschlagsrisiken.

Für bereits vorhandene Weine kann das Wetter in der Weinliste über den
Aktualisierungssymbol-Button erneut abgefragt werden.

### Degustationsmodus

Der **Degustationsmodus** ist über einen deutlich sichtbaren Umschalt-Button
mit Glas-Icon erreichbar. Dort können Degustationen mit Datum, Ort, Bewertung,
Notizen und detaillierten Tasting-Angaben verwaltet werden.

Die Umschaltung ist auf allen Wein- und Degustationsseiten als beschrifteter
**Weinmodus**- und **Degustationsmodus**-Button mit passendem Icon sichtbar.
Der aktive Modus wird blau hervorgehoben.

## Beispieldaten laden

Das optionale Seed-Skript löscht bestehende Weine, Winzer und
Degustationen und ersetzt sie durch Beispieldaten:

```powershell
$env:PYTHONPATH="$PWD\src"
uv run seed.py
```

## Wetter-API

Die Anwendung verwendet:

- Open-Meteo Geocoding API zur Ortsauflösung
- Open-Meteo Archive API für historische Wetterdaten

Die Daten werden einmalig beim Speichern beziehungsweise durch den
Aktualisierungssymbol-Button abgefragt und in SQLite gespeichert. Ein API-
oder Ortsfehler verhindert nicht das Speichern eines Weins.

## Tests

Die Testsuite ausführen:

```powershell
uv run pytest
```

## Docker

Mit installiertem Docker kann die Anwendung auch als Container gestartet
werden:

```powershell
docker build . -t webapp
docker run -p 8000:8000 webapp
```

Danach ist die Anwendung unter `http://localhost:8000` erreichbar.
