# Eigene Degustationsübersicht und Startablauf

Date: 2026-10-31

## Status

Accepted

## Context

Degustationen wurden bisher in der Weinübersicht zusammen mit den Weinen
angezeigt. Nutzer sollen Degustationen als eigenständige Einträge überblicken
und von dort aus neue Degustationen starten können.

## Options Considered

 * Degustationen weiterhin nur unter jedem Wein anzeigen: weniger Seiten, aber
   kein Gesamtüberblick über alle Degustationen.
 * Eine eigene Übersicht mit chronologisch sortierten Degustationen und
   Verknüpfung zum Wein: klare Trennung und direkte Aktionen pro Eintrag.
 * Wein und Degustation gleichzeitig in einem langen Formular neu erfassen:
   weniger Schritte, aber ein umfangreiches Formular mit zwei Datensatztypen.

## Decision

Die App erhält unter `/tastings` eine eigene Übersicht aller Degustationen,
standardmässig nach Datum absteigend sortiert. Von dort können Nutzer eine
Degustation starten und sie bearbeiten oder löschen.

Beim Start wird ein bestehender Wein ausgewählt. Falls der Wein noch nicht
existiert, wird er in einem separaten Schritt erfasst; danach öffnet sich
direkt das Formular für die zugehörige Degustation. Die bestehende Weinübersicht
bleibt separat verfügbar.

## Reasons

Die Übersicht unterstützt die eigenständige Betrachtung von Degustationen.
Der zweistufige Ablauf hält jedes Formular auf einen fachlichen Datensatz
beschränkt und führt nach der Wein-Neuanlage ohne erneute Auswahl zur
Degustation.

## Consequences

Es gibt getrennte Routen und Templates für die Übersicht, die Wein-Auswahl und
den neuen Wein im Degustationsablauf. Die Navigation verbindet Wein- und
Degustationsbereich; die bestehende Datenbankstruktur bleibt unverändert.
