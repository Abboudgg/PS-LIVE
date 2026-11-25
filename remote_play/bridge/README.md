# Media bridge contract

This folder defines the boundary between chiaki-ng-core and the future PS-LIVE
media pipeline. It is an interface scaffold only: it does not create a Play
session, pair a console, decode video, encode media, launch FFmpeg, or publish
RTMP.

## Data flow

1. A future session owner constructs a `MediaBridge` and keeps both it and its
   `MediaOutput` alive for the whole session.
2. chiaki-ng-core calls the `MediaSink` callbacks on its session thread.
3. The bridge forwards stream descriptions, encoded video units, audio units,
   gaps, and controller feedback to `MediaOutput`.
4. A future FFmpeg adapter must copy callback data into a bounded queue and
   return quickly. The `VideoUnit` and `AudioUnit` data are only valid during
   their callback.
5. A separate worker can consume queued media, handle timestamps/codec
   configuration, and feed a tested FFmpeg pipeline.

## Important media details

- Video units identify H.264 versus HEVC, dimensions, profile changes, and
  codec-header frames. Preserve profile headers and send them before frames
  that need them.
- Audio units may contain Opus packets or raw PCM, and can announce a format
  change. Use `libchiaking::media::AudioDecoder` when PCM is required; rebuild
  it when the announced format changes.
- Do not block, sleep, or wait for FFmpeg in a `MediaSink` callback. If the
  video queue is full, report a dropped frame so the session can recover.
- Audio and video need a deliberate timestamp/clock strategy before muxing.
  This header does not solve synchronization or RTMP publishing.

## Current limits

- No Chiaki-ng source is vendored or built here.
- No PSN credentials, account IDs, pairing PINs, or stream keys belong here.
- No API route or Render deployment is changed by adding this contract.
- The interface has not yet been compiled against a pinned chiaki-ng-core
  revision. Pin a reviewed commit and run a Linux build before integration.
- Check and satisfy the upstream AGPL-3.0 obligations before distributing a
  combined work or offering it as a network service.
