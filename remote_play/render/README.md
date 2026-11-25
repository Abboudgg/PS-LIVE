# PS-LIVE Remote Play runtime on Render

## Status

This directory documents the Linux runtime integration boundary. It is not a
working Remote Play engine and it does not start a PS5 session.

The existing GitHub Actions check proves that the pinned `chiaki-ng-core`
source can be configured and that the current `MediaBridge` translation unit
compiles. It does not prove that a complete frontend can be linked, that PSN
sign-in works, or that Render can carry a Remote Play session.

## Required frontend pieces

A real headless frontend must own and keep alive all of the following:

1. A `PlatformFactory` with working Linux network, threading, secure random,
   crypto, HTTP, WebSocket and DTLS providers. The stock
   `DefaultPlatformFactory` intentionally supplies absent implementations
   for several optional services, so constructing it alone is insufficient
   for PSN-backed play.
2. A `ChiakiNg`/core wiring layer, `KnownConsoles`, a persistent
   `ConsoleStore`, signed-in user/credential storage, and the `Play`
   coordinator.
3. A `PsUser` created through the supported sign-in flow. PSN credentials,
   NPSSO values, refresh tokens and pairing keys must never be committed to
   this repository or exposed by the HTTP control API.
4. A `SessionEvents` implementation and the existing `MediaBridge`.
   Callback data is valid only during the callback, so the media output must
   copy it into bounded queues and return quickly.
5. Video/audio handling for stream descriptions and format changes, followed
   by a tested FFmpeg input path and a protected RTMP destination.

## Render constraints to validate before deployment

- Remote Play requires UDP networking and a reachable route between the
  Render instance and the console. A normal public HTTP service does not by
  itself provide that route.
- Render instances may restart or be replaced. Console pairings and account
  credentials therefore need protected persistent storage; an ephemeral
  container filesystem is not an acceptable secret store.
- CPU, memory, process lifetime and outbound networking must be measured
  during a real stream. A successful compile is not a performance test.
- Do not expose a raw media input URL, PSN credentials, pairing keys or RTMP
  key through public status endpoints or browser JavaScript.

## Safe implementation order

1. Build and test the Linux provider composition and storage adapters locally
   or in CI, without real account credentials.
2. Add a headless runtime executable that can report provider readiness and
   shut down cleanly; keep Remote Play disabled until storage and sign-in are
   implemented.
3. Implement sign-in and pairing using the library's supported APIs, with
   secrets supplied only through protected runtime storage.
4. Start a local-network PS5 session and verify video and audio callbacks.
5. Connect bounded media queues to FFmpeg and test a private RTMP destination.
6. Only then assess whether the same runtime can operate reliably on Render.

## Upstream pin and licensing

The compatibility check currently pins
`chiaki-ng-core` at
`083f6e36deda83396e443ed48387844d660bcaee`.
Review the upstream AGPL-3.0 license and its obligations before distributing
or offering the integrated service over a network.
