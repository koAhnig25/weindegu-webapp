# Summer Weather API

Date: 2026-11-17

## Status

Accepted

## Context

The application should show historical summer weather for a wine based on its
vintage year and origin location. The first version needs only a short summary
covering the three summer months, June through August north of the equator and
February through April south of the equator. It should remain understandable
and avoid a costly or complex weather integration.

## Options Considered

 * Use a weather API with Open-Meteo Geocoding and Open-Meteo Archive.
 * Use a provider that requires API keys and account setup.
 * Ask users to enter weather values manually.

## Decision

The application uses the public Open-Meteo Geocoding API and Open-Meteo Archive
API. It stores the resulting summer summary once on the wine record. The period
is June through August north of the equator and February through April south
of the equator.
The summary is refreshed only if the year or origin changes or no result was
stored yet.
The weather summary also receives a short, conservative assessment based only
on average summer temperature and total precipitation.
Existing wines can refresh both values through a dedicated POST action in the
wine list. This is useful for records created before weather support existed.

## Reasons

Open-Meteo provides both geocoding and historical data without an API key. The
summary is simple enough for the project and the integration can use Python's
standard library. A database cache avoids unnecessary repeated API calls.

## Consequences

The application can show average summer temperature and total precipitation,
but location matching depends on geocoding quality. API and network errors are
visible to the user and do not prevent a wine from being saved. Full weather
details, forecasts, and provider-level monitoring are left for a future version.
