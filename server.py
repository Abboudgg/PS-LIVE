import hmac
import json
import os
import shutil
import subprocess
import threading
import time
from urllib.parse import urlsplit
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

STATE = {"process": None, "started_at": None, "last_error": None}
LOCK = threading.Lock()


def current_process():
    process = STATE["process"]
    if process is not None and process.poll() is not None:
        STATE["last_error"] = f"FFmpeg exited with code {process.returncode}"
        STATE["process"] = None
        STATE["started_at"] = None
    return STATE["process"]


class Handler(BaseHTTPRequestHandler):
    def route_path(self):
        return urlsplit(self.path).path.rstrip("/") or "/"

    def send_json(self, status, payload, head_only=False):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if not head_only:
            self.wfile.write(body)

    def authorized(self):
        expected = os.environ.get("PS_LIVE_CONTROL_TOKEN", "")
        supplied = self.headers.get("Authorization", "")
        if not expected:
            self.send_json(503, {
                "error": "control_not_configured",
                "message": "Set PS_LIVE_CONTROL_TOKEN in the service environment."
            })
            return False
        if not hmac.compare_digest(supplied, f"Bearer {expected}"):
            self.send_json(401, {"error": "unauthorized"})
            return False
        return True

    def status_payload(self):
        with LOCK:
            process = current_process()
            return {
                "service": "PS-LIVE",
                "stage": "stream-bridge-foundation",
                "ps5_connected": False,
                "video_receiving": False,
                "audio_receiving": False,
                "streaming": process is not None,
                "ffmpeg_running": process is not None,
                "started_at": STATE["started_at"],
                "last_error": STATE["last_error"],
                "message": "محرك Remote Play لم يُدمج بعد؛ لا يوجد مصدر PS5 متصل حاليًا."
            }

    def get_payload(self):
        path = self.route_path()
        if path == "/":
            return 200, {
                "ok": True,
                "service": "PS-LIVE API",
                "message": "الخادم يعمل.",
                "endpoints": ["/health", "/status"]
            }
        if path == "/health":
            return 200, {"ok": True, "service": "ps-live-api"}
        if path == "/status":
            return 200, self.status_payload()
        return 404, {"error": "not_found"}

    def do_GET(self):
        status, payload = self.get_payload()
        self.send_json(status, payload)

    def do_HEAD(self):
        status, payload = self.get_payload()
        self.send_json(status, payload, head_only=True)

    def do_POST(self):
        path = self.route_path()
        if path not in ("/api/stream/start", "/api/stream/stop"):
            return self.send_json(404, {"error": "not_found"})
        if not self.authorized():
            return
        if path == "/api/stream/start":
            return self.start_stream()
        return self.stop_stream()

    def start_stream(self):
        input_url = os.environ.get("PS_LIVE_INPUT_URL", "").strip()
        output_url = os.environ.get("RESTREAM_RTMP_URL", "").strip()
        ffmpeg = shutil.which("ffmpeg")
        if not input_url:
            return self.send_json(409, {
                "error": "source_not_configured",
                "message": "PS_LIVE_INPUT_URL is not set. A working Remote Play capture source is required first."
            })
        if not output_url:
            return self.send_json(409, {
                "error": "destination_not_configured",
                "message": "Set RESTREAM_RTMP_URL as a protected service environment variable."
            })
        if not ffmpeg:
            return self.send_json(503, {"error": "ffmpeg_unavailable"})

        command = [
            ffmpeg, "-nostdin", "-hide_banner", "-loglevel", "warning",
            "-i", input_url,
            "-c:v", "libx264", "-preset", "veryfast", "-tune", "zerolatency",
            "-b:v", "2500k", "-maxrate", "2500k", "-bufsize", "5000k",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
            "-f", "flv", output_url
        ]
        with LOCK:
            if current_process() is not None:
                return self.send_json(409, {"error": "already_running"})
            try:
                process = subprocess.Popen(
                    command,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    close_fds=True
                )
            except OSError:
                STATE["last_error"] = "Could not start FFmpeg."
                return self.send_json(500, {"error": "ffmpeg_start_failed"})
            STATE["process"] = process
            STATE["started_at"] = int(time.time())
            STATE["last_error"] = None
        return self.send_json(202, {
            "ok": True,
            "message": "FFmpeg started. This does not confirm that a PS5 source is connected or that the platform accepted the stream."
        })

    def stop_stream(self):
        with LOCK:
            process = current_process()
            if process is None:
                return self.send_json(200, {"ok": True, "streaming": False})
            process.terminate()
            try:
                process.wait(timeout=8)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=3)
            STATE["process"] = None
            STATE["started_at"] = None
        return self.send_json(200, {"ok": True, "streaming": False})

    def log_message(self, fmt, *args):
        print("%s - %s" % (self.address_string(), fmt % args))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"PS-LIVE API listening on port {port}")
    server.serve_forever()
