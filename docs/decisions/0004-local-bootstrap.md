# Bootstrap lokal in die Weboberfläche integrieren

Date: 2026-10-31

## Status

Accepted

## Context

Die Wein- und Degustationsseiten sollen auf Handy, Tablet und Desktop gut
nutzbar sein. Das Projekt verwendet serverseitig gerenderte HTML-Templates und
benötigt keinen Frontend-Build-Schritt.

## Options Considered

 * Bootstrap über ein CDN laden: kein lokales Asset, aber der Browser braucht
   eine Internetverbindung und die Seite hängt von einem externen Anbieter ab.
 * Die Bootstrap-CSS-Datei lokal ausliefern: funktioniert ohne CDN-Verbindung,
   benötigt aber eine versionierte Drittanbieterdatei im Projekt.
 * Das vorhandene eigene CSS erweitern: keine zusätzliche Bibliothek, aber
   Layout und Formulare müssen selbst konsistent responsiv gestaltet werden.

## Decision

Bootstrap 5.3.8 wird lokal als CSS-Datei ausgeliefert. Die Templates der
Weinliste und der Degustationsmaske verwenden Bootstrap-Container, Raster,
Formular-, Tabellen-, Button- und Alert-Klassen. Für die Weinliste ist die
Tabelle auf kleinen Bildschirmen horizontal scrollbar.

## Reasons

Die lokale Einbindung benötigt weder eine Browserverbindung zu einem CDN noch
einen Frontend-Build-Schritt. Bootstrap bietet gemeinsame responsive Bausteine
für die vorhandenen HTML-Formulare und Tabellen.

## Consequences

Die gebündelte CSS-Datei und die MIT-Lizenz liegen im lokalen Static-Verzeichnis.
Ein Update muss die versionierte Datei und die Lizenz gemeinsam aktualisieren.
Die responsive Oberfläche macht den Webserver selbst nicht automatisch aus dem
Internet oder von anderen Geräten erreichbar; dafür ist eine passende
Serveradresse und Netzwerkkonfiguration nötig.
