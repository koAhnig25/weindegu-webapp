# Flask, SQLite und Render als technische Basis

Date: 2026-11-20

## Status

Accepted (rückwirkend dokumentiert; die Entscheide fielen im Oktober und
November 2026)

## Context

Die Aufgabenstellung verlangt ein Python-Backend (Flask, Django oder FastAPI),
eine Datenbank, die Anbindung eines externen Webservices und eine öffentlich
erreichbare, automatisch deploybare Webapplikation. Das Team besteht aus vier
Studierenden mit unterschiedlicher Programmiererfahrung. Die Applikation ist
klein (Weine, Winzer, Degustationen) und muss nur bis Ende der
Prüfungssession laufen.

## Options Considered

Backend-Framework:

 * Flask: klein, wenig "Magie", Routen und Templates sind direkt im Code
   nachvollziehbar. Vieles (z.B. Datenbankzugriff) muss man selbst lösen.
 * Django: bringt ORM, Admin und Migrationen mit, ist aber für eine kleine App
   viel Struktur und Lernaufwand.
 * FastAPI: stark für JSON-APIs, passt aber weniger zu serverseitig
   gerenderten HTML-Formularen.

Datenbank:

 * SQLite mit dem Standardmodul `sqlite3`: keine Installation, eine Datei,
   SQL bleibt sichtbar.
 * SQLite mit SQLAlchemy: komfortabler, aber eine zusätzliche Abstraktion.
 * PostgreSQL: dauerhaft und robust, braucht aber einen separaten Dienst.

Hosting:

 * Render (Gratis-Plan): direkte GitHub-Anbindung mit Auto-Deploy, ohne
   Kosten, schnell eingerichtet.
 * Azure App Service: im Template dokumentiert, aber mehr Einrichtungsaufwand
   (Ressourcengruppe, App Service Plan, GitHub-Actions-Workflow).
 * Eigener Server/VM: volle Kontrolle, aber Betrieb und Updates selbst nötig.

## Decision

Das Team verwendet Flask mit Jinja2-Templates, SQLite über das Python-Modul
`sqlite3` und hostet die App als Web Service auf Render. Render deployt jeden
Push auf `master` automatisch.

## Reasons

Flask ist der einfachste der erlaubten Wege und das Team kann jede Zeile des
Backends erklären. `sqlite3` aus der Standardbibliothek braucht keine weitere
Abhängigkeit und macht die SQL-Abfragen direkt sichtbar. Ein erster Versuch
mit SQLAlchemy (`models.py`, ein ORM, das Tabellen als Python-Klassen abbildet)
machte Probleme und war für das Team eine zusätzliche, unbekannte Schicht. Er
wurde deshalb nicht weiterverfolgt; die App arbeitet direkt mit SQL.

Render wurde gewählt, weil es einfach einzurichten ist: Der Dienst wird
direkt mit dem GitHub-Repository verknüpft und aktualisiert sich bei jedem
Push automatisch. Damit ist die Vorgabe "automatisch deploybar" ohne eigenen
CI/CD-Workflow erfüllt. Zudem ist Render kostenlos, und gegen Projektende war
die verbleibende Zeit knapp, sodass ein aufwendigeres Setup (z.B. Azure) nicht
mehr in Frage kam.

## Consequences

 * Das Datenbankschema und Migrationen werden von Hand in `init_db` gepflegt.
 * Auf dem Gratis-Plan von Render ist das Dateisystem nicht dauerhaft: Die
   SQLite-Datei ist nach jedem Deploy oder Neustart leer. Das wird mit
   automatischen Demodaten abgefedert (siehe
   [0009](0009-demo-data.md)). Für echte, dauerhafte Daten müsste auf eine
   Render-Disk oder PostgreSQL gewechselt werden.
 * Die App schläft bei Inaktivität ein; der erste Aufruf ist langsam.
 * Tests laufen nicht automatisch vor dem Deploy. Ein GitHub-Actions-Workflow
   mit `pytest` wäre ein möglicher nächster Schritt.
