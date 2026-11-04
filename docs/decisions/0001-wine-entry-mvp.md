# Erfassung von Weinen im ersten MVP

Date: 2026-10-31

## Status

Superseded by [0003-wine-tastings.md](./0003-wine-tastings.md)

## Context

Die Anwendung enthält eine bestehende SQLite-Tabelle `wines` mit Name,
Rebsorte, Jahrgang, Herkunftsort, Bewertung und optionalen Notizen. Der erste
Usecase soll weitere Weine über eine HTML-Seite erfassen.

## Options Considered

 * Einträge nur über ein Datenbankwerkzeug ergänzen: schnell, aber nicht über
   die Webanwendung bedienbar.
 * Ein HTML-Formular mit serverseitiger Validierung und SQLite-Speicherung:
   direkt verständlich und passend zum ersten Lernschritt.
 * Eine Anmeldung, Rollen und eine umfassende Weinverwaltung ergänzen: mehr
   Schutz und Funktionalität, aber zusätzlicher Umfang für den MVP.

## Decision

Der MVP erhält ein Formular zum Hinzufügen und eine Liste der vorhandenen
Weine. Er verwendet Flask für HTTP-Routen und die Python-Standardbibliothek
`sqlite3` für die vorhandene Datenbank. Die Bewertung ist eine Ganzzahl von 1
bis 5; Notizen bleiben optional. Es gibt vorerst keine Anmeldung und die
Anwendung ist nur für lokale Entwicklung oder vertrauenswürdige Nutzer
vorgesehen.

## Reasons

Flask ist bereits als Abhängigkeit vorhanden und bietet für Formular und
Ergebnisliste einen einfachen Python-Backend-Einstieg. `sqlite3` erlaubt den
direkten Umgang mit der vorhandenen SQLite-Datei ohne zusätzliche
Datenbankbibliothek.

## Consequences

Eingaben werden im Backend validiert und per parametrisiertem SQL gespeichert.
Neue Einträge sind nach dem Speichern in der Liste sichtbar. Ohne Anmeldung
darf die Anwendung nicht öffentlich bereitgestellt werden; vor einem solchen
Betrieb muss Zugriffsschutz ergänzt werden.
