"""Mini serveur HTTP local : galerie web + accès aux vidéos.

Usage :
    python serve.py            # http://localhost:8000
    python serve.py --port 9000
"""
import argparse
import http.server
import json
import socketserver
import sys
import threading
import webbrowser
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "output"


def build_video_list() -> list[dict]:
    items: list[dict] = []
    if not OUTPUT_DIR.exists():
        return items
    for meta_file in OUTPUT_DIR.glob("*.json"):
        try:
            data = json.loads(meta_file.read_text(encoding="utf-8"))
            video_file = data.get("video_file") or meta_file.with_suffix(".mp4").name
            if (OUTPUT_DIR / video_file).exists():
                data["video_file"] = video_file
                items.append(data)
        except Exception as e:
            print(f"⚠️  Métadata invalide {meta_file.name} : {e}")
    items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return items


class GalleryHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.path = "/web/index.html"
        if self.path.startswith("/api/videos"):
            payload = json.dumps(build_video_list(), ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(payload)
            return
        return super().do_GET()

    def log_message(self, format, *args):
        return  # silencieux


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--no-open", action="store_true", help="Ne pas ouvrir le navigateur")
    args = parser.parse_args()

    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", args.port), GalleryHandler) as httpd:
        url = f"http://localhost:{args.port}/"
        print(f"🌐 Galerie disponible sur {url}")
        print("   Ctrl+C pour arrêter\n")
        if not args.no_open:
            threading.Timer(0.8, lambda: webbrowser.open(url)).start()
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 Arrêt du serveur")
    return 0


if __name__ == "__main__":
    sys.exit(main())
