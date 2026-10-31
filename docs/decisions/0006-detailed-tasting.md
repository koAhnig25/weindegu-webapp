# Kurz- und Detail-Degustation

Date: 2026-10-31

## Status

Accepted

## Context

Die Degustation soll sowohl eine schnelle Bewertung als auch eine strukturierte
Erfassung nach den vorgegebenen Merkmalen für Aussehen, Nase, Gaumen und
Gesamteindruck ermöglichen. Die Detail-Degu darf leer bleiben. Pro Merkmal ist
eine Auswahl möglich; bei Aromatik sind Mehrfachauswahlen sinnvoll.

## Options Considered

 * Nur die bestehende Kurz-Degu beibehalten: einfache Eingabe, aber keine
   strukturierte Erfassung einzelner sensorischer Merkmale.
 * Kurz- und Detail-Degu parallel erfassen: schnelle Bewertung bleibt erhalten
   und kann bei Bedarf durch Merkmale ergänzt werden.
 * Kurz- und Detail-Degu als gegenseitig ausschliessende Varianten anbieten:
   vermeidet Doppeleingaben, benötigt aber eine zusätzliche Auswahl und
   bedingte Formularlogik.

## Decision

Die bestehende Kurz-Degu mit Bewertung und Notizen bleibt oben im Formular.
Darunter wird die optionale Detail-Degu mit den vorgegebenen Merkmalen
angezeigt. Einzelne Merkmale sind Einfachauswahlen, Aromatik ist mehrfach
wählbar. Säure und Tannin werden als separate Merkmale erfasst.

Die ausgewählten Detailwerte werden als JSON in einer optionalen
`detailed_tasting`-Spalte der Degustation gespeichert. Bestehende Datenbanken
erhalten die Spalte bei der Initialisierung; bestehende Einträge bleiben ohne
Detailwerte gültig.

## Reasons

Die Trennung hält die schnelle Bewertung übersichtlich und erlaubt eine
vertiefte Erfassung im selben Anlass. Die Auswahlregeln verhindern
widersprüchliche Mehrfachwerte bei Skalenmerkmalen, während sie für Aromatik
mehrere Eindrücke zulassen. Da keine Abfragen oder Auswertungen nach einzelnen
Detailmerkmalen gefordert sind, ist eine JSON-Spalte einfacher als zusätzliche
relationale Tabellen.

## Consequences

Die Detail-Degu kann pro Degustation leer oder teilweise ausgefüllt sein.
Validierung und Darstellung bleiben serverseitig kontrolliert. Für spätere
Filterung oder statistische Auswertung nach Merkmalen müsste die JSON-Struktur
in ein relationales Modell überführt oder gezielt erweitert werden.
