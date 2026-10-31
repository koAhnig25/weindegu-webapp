# Weine und Degustationen trennen

Date: 2026-10-31

## Status

Accepted

## Context

Ein Wein kann mehrfach degustiert werden. Weininformationen wie Name,
Rebsorte, Jahrgang, Herkunft und Winzer ändern sich nicht bei jeder
Degustation. Datum, Ort, Bewertung und Notizen gehören dagegen zu einem
einzelnen Anlass.

## Options Considered

 * Wein- und Degustationsdaten in einer Tabelle belassen: einfacher, kann aber
   mehrere Bewertungen desselben Weins nicht sauber abbilden.
 * Zwei Tabellen in derselben SQLite-Datei verwenden: ermöglicht eine normale
   Fremdschlüsselbeziehung und atomare Schreibvorgänge.
 * Separate SQLite-Dateien verwenden: trennt die Dateien, verhindert aber
   normale dateiübergreifende Fremdschlüssel und erschwert gemeinsame
   Transaktionen.

## Decision

Weine und Degustationen werden in derselben SQLite-Datei in getrennten Tabellen
gespeichert. Jede Degustation referenziert genau einen Wein; ein Wein kann
beliebig viele Degustationen haben.

Die Wein-Tabelle speichert Name, Rebsorte, Jahrgang, Herkunftsort und Winzer.
Die Degustation speichert Datum, Ort, Bewertung von 1 bis 5 und optionale
Notizen. Beim Erfassen einer neuen Degustation sind Datum, Ort und Bewertung
erforderlich. Degustationsdaten dürfen nicht in der Zukunft liegen; der
Jahrgang eines Weins darf höchstens das aktuelle Kalenderjahr sein.

Die bisherigen Bewertungen und Notizen werden als erste Degustation jedes
Weins übernommen. Für diese historischen Einträge gilt das bestätigte Datum
31.10.2026; der unbekannte Ort bleibt leer.

## Reasons

Die getrennten Tabellen bilden die Eins-zu-viele-Beziehung im relationalen
Datenmodell ab und halten veranstaltungsbezogene Bewertungen beim jeweiligen
Degustationsanlass. Eine SQLite-Datei erhält die Möglichkeit, die Beziehung
mit einem Fremdschlüssel abzusichern.

## Consequences

Die bestehende SQLite-Datei wird beim Start erweitert und migriert. Die
Weinliste zeigt die Degustationen pro Wein; weitere Degustationen können
hinzugefügt werden, ohne den Weineintrag zu duplizieren. Historische
Degustationen haben kein bekanntes Ortsfeld. Das Löschen eines Weins entfernt
seine Degustationen kaskadierend; eine einzelne Degustation kann unabhängig
gelöscht werden. Die Grenzen für Datum und Jahrgang werden serverseitig
validiert und zusätzlich in den HTML-Formularen angezeigt.
