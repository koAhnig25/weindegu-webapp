# Winzer als eigene Datenbankentität

Date: 2026-10-31

## Status

Accepted

## Context

Die Weinmaske soll bestehende Weine bearbeiten können und jedem Wein einen
Winzer zuordnen. Das Team hat sich bewusst für eine eigene Winzer-Tabelle statt
eines bloßen Textfelds in der Weintabelle entschieden.

## Options Considered

 * Winzername als Textfeld beim Wein: einfacher, aber dieselben Winzer können
   mehrfach und unterschiedlich geschrieben gespeichert werden.
 * Eigene Tabelle `wineries` mit Fremdschlüssel in `wines`: zusätzliche
   Verknüpfung, aber einheitliche Winzer und eine Grundlage für spätere
   Winzerangaben.

## Decision

Winzer werden in einer eigenen Tabelle gespeichert. Beim Erfassen oder
Bearbeiten eines Weins kann ein existierender Winzer ausgewählt oder ein neuer
Name direkt im Formular angegeben werden. Ein Wein muss genau einem Winzer
zugeordnet sein.

Die vorhandenen Weine erhalten bei der Migration zunächst den Winzer
„Unbekannt“. Die Nutzer können die Zuordnung beim Bearbeiten eines Weins
ersetzen.

## Reasons

Die separate Entität wurde bewusst gewählt, damit mehrere Weine denselben
Winzer referenzieren und spätere Winzerinformationen zentral ergänzt werden
können. Die Inline-Erfassung hält den Arbeitsablauf für den MVP trotzdem
einfach.

## Consequences

Die Datenbankmigration legt die Winzertabelle an, ergänzt den Fremdschlüssel
und erhält IDs sowie bestehende Weindaten. Der Platzhalter „Unbekannt“ ist eine
Übergangslösung und kann später durch echte Zuordnungen ersetzt werden.
