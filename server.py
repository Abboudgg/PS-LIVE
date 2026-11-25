import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class Handler(BaseHTTPRequestHandler):
    def send_json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            return self.send_json(200, {"ok": True, "service": "ps-live-api"})
        if self.path == "/status":
            return self.send_json(200, {
                "service": "PS-LIVE",
                "stage": "foundation",
                "ps5_connected": False,
                "video_receiving": False,
                "audio_receiving": False,
                "streaming": False,
                "message": "واجهة الحالة جاهزة؛ محرك Remote Play والبث لم تتم إضافتهما بعد."
            })
        return self.send_json(404, {"error": "not_found"})

    def log_message(self, fmt, *args):
        print("%s - %s" % (self.address_string(), fmt % args))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"PS-LIVE status API listening on port {port}")
    server.serve_forever()
