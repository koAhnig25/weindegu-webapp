# Automatische Demodaten mit gezieltem Löschen

Date: 2026-11-20

## Status

Accepted

## Context

Die öffentliche App läuft auf dem Gratis-Plan von Render. Dort ist das
Dateisystem nicht dauerhaft, die SQLite-Datenbank ist nach jedem Deploy oder
Neustart leer. Wer die App (z.B. Dozierende vor der Präsentation) aufruft,
würde eine leere Weinliste, Rangliste und Degustationsübersicht sehen.
Gleichzeitig sollen Nutzende mit einer sauberen Datenbank starten können.

## Options Considered

 * Keine Demodaten: einfach, aber die App wirkt nach jedem Neustart leer.
 * Demodaten per Button laden: volle Kontrolle, aber nach jedem Neustart ist
   die App zuerst leer, bis jemand den Button drückt.
 * Demodaten beim Start einfügen, wenn noch kein Wein vorhanden ist, und per
   Button wieder löschen: App ist nie leer, eigene Daten werden nie
   überschrieben.
 * Beim Löschen alle Daten entfernen: einfacher, aber jede Person mit der
   öffentlichen URL könnte alle selbst erfassten Daten löschen.

## Decision

Beim Start der App (`create_app`) wird geprüft, ob die Tabelle `wines` leer
ist. Nur dann werden drei Beispielweine mit Winzer und je einer Degustation
eingefügt. Diese Datensätze werden mit einer Spalte `is_demo = 1` markiert.
Der Button "Demodaten löschen" im Weinmodus (POST `/demo-data/delete`)
entfernt nur markierte Weine (Degustationen per `ON DELETE CASCADE`) und
markierte Winzer, die von keinem Wein mehr verwendet werden. Die Prüfung
läuft nur beim Start; gelöschte Demodaten bleiben bis zum nächsten Neustart
weg. Entschieden vom Team am 2026-11-20.

## Reasons

Die Markierung `is_demo` trennt Beispiel- und echte Daten eindeutig, ohne
neue Tabelle. Die Prüfung "nur wenn leer" stellt sicher, dass lokal
bestehende Daten nie verändert werden. In Tests ist die Funktion
standardmässig ausgeschaltet (`DEMO_DATA`-Konfiguration), damit Tests mit
einer leeren Datenbank starten.

## Consequences

 * Die App zeigt nach jedem Render-Neustart sofort Beispielinhalte.
 * Löscht jemand alle eigenen Weine und startet die App neu, erscheinen die
   Demodaten wieder.
 * Degustationen, die jemand zu einem Demowein erfasst, werden beim Löschen
   der Demodaten mitgelöscht.
 * Für Demoweine sind noch keine Wetterdaten gespeichert; sie können über den
   Aktualisierungs-Button nachgeladen werden. So macht der App-Start keine
   Netzwerkaufrufe.
 * Es gibt keine Benutzerverwaltung: Jede Person mit der URL kann die
   Demodaten löschen. Für dieses Projekt ist das akzeptiert.
