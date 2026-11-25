"""PS-LIVE Remote Play engine interface placeholder.

This module deliberately does not connect to PSN or a PlayStation.
A real Chiaki/Chiaki-ng adapter must be implemented and tested before
this status can report an active Remote Play session.
"""

from typing import Any


def get_engine_status() -> dict[str, Any]:
    """Return an honest status until a real Remote Play backend is integrated."""
    return {
        "engine": "not_integrated",
        "backend": None,
        "ps5_connected": False,
        "video_receiving": False,
        "audio_receiving": False,
        "ready_for_ffmpeg": False,
        "message": (
            "Remote Play engine is a placeholder; "
            "no PS5 session or media stream is active."
        ),
    }


if __name__ == "__main__":
    import json

    print(json.dumps(get_engine_status(), ensure_ascii=False, indent=2))
