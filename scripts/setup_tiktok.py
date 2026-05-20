"""Wizard de configuration OAuth TikTok — à lancer UNE SEULE FOIS.

Étapes (automatique) :
1. Ouvre ton navigateur sur la page d'autorisation TikTok
2. Lance un mini-serveur HTTP local pour capter la redirection
3. Échange le code contre access_token + refresh_token
4. Sauve les tokens dans .env

Pré-requis AVANT de lancer ce script :
- Avoir une app TikTok créée sur https://developers.tiktok.com/apps
- Avoir mis dans .env :
    TIKTOK_CLIENT_KEY=...
    TIKTOK_CLIENT_SECRET=...
- L'app TikTok doit avoir comme Redirect URI : http://localhost:8765/tiktok-callback
- L'app doit demander les scopes : user.info.basic + video.upload

Usage :
    python scripts/setup_tiktok.py
"""
import http.server
import os
import secrets
import socketserver
import sys
import threading
import time
import urllib.parse
import webbrowser
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

AUTH_URL = "https://www.tiktok.com/v2/auth/authorize/"
TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"
REDIRECT_URI = "http://localhost:8765/tiktok-callback"
SCOPES = "user.info.basic,video.upload"
LISTEN_PORT = 8765


def main() -> int:
    from dotenv import load_dotenv
    env_path = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(env_path, override=True)

    client_key = os.getenv("TIKTOK_CLIENT_KEY", "").strip()
    client_secret = os.getenv("TIKTOK_CLIENT_SECRET", "").strip()
    if not client_key or not client_secret:
        print("❌ TIKTOK_CLIENT_KEY et/ou TIKTOK_CLIENT_SECRET manquent dans .env")
        print("   Crée d'abord une app sur https://developers.tiktok.com/apps")
        print("   puis ajoute les 2 valeurs dans .env, et relance ce script.")
        return 1

    state = secrets.token_urlsafe(16)
    params = urllib.parse.urlencode({
        "client_key": client_key,
        "scope": SCOPES,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "state": state,
    })
    auth_url = f"{AUTH_URL}?{params}"

    captured: dict = {}

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path.startswith("/tiktok-callback"):
                qs = urllib.parse.urlparse(self.path).query
                p = urllib.parse.parse_qs(qs)
                captured["code"] = (p.get("code") or [None])[0]
                captured["state"] = (p.get("state") or [None])[0]
                captured["error"] = (p.get("error") or [None])[0]
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                body = "<h1>✅ Autorisation reçue, tu peux fermer cet onglet.</h1>"
                self.wfile.write(body.encode("utf-8"))
            else:
                self.send_error(404)

        def log_message(self, *a, **kw):
            return  # silencieux

    socketserver.TCPServer.allow_reuse_address = True
    try:
        srv = socketserver.TCPServer(("127.0.0.1", LISTEN_PORT), Handler)
    except OSError as e:
        print(f"❌ Port {LISTEN_PORT} déjà pris : {e}")
        print("   Ferme le programme qui l'utilise (ou serve.py) et relance.")
        return 1

    threading.Thread(target=srv.serve_forever, daemon=True).start()

    print(f"🌐 Ouverture de TikTok pour autorisation...\n   {auth_url}\n")
    webbrowser.open(auth_url)
    print(f"⏳ En attente du retour OAuth sur localhost:{LISTEN_PORT}...")

    start = time.time()
    while not captured.get("code") and not captured.get("error") and time.time() - start < 300:
        time.sleep(0.5)

    srv.shutdown()

    if captured.get("error"):
        print(f"❌ TikTok a refusé : {captured['error']}")
        return 1
    if not captured.get("code"):
        print("❌ Timeout : pas d'autorisation reçue après 5 min.")
        return 1
    if captured.get("state") != state:
        print("❌ State CSRF invalide — annulation pour ta sécurité.")
        return 1

    print("🔄 Échange du code contre les tokens...")
    r = requests.post(
        TOKEN_URL,
        data={
            "client_key": client_key,
            "client_secret": client_secret,
            "code": captured["code"],
            "grant_type": "authorization_code",
            "redirect_uri": REDIRECT_URI,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30,
    )
    if r.status_code != 200:
        print(f"❌ Échange token a échoué : HTTP {r.status_code}")
        print(r.text[:500])
        return 1
    data = r.json()
    access_token = data.get("access_token")
    refresh_token = data.get("refresh_token")
    if not access_token or not refresh_token:
        print(f"❌ Réponse inattendue : {data}")
        return 1

    from src.tiktok_publisher import update_env_vars
    update_env_vars({
        "TIKTOK_ACCESS_TOKEN": access_token,
        "TIKTOK_REFRESH_TOKEN": refresh_token,
    })
    print()
    print("✅ Tokens TikTok sauvegardés dans .env.")
    print("   Tu peux maintenant activer l'auto-publication en ajoutant à .env :")
    print("     TIKTOK_AUTO_PUBLISH=true")
    print("   La prochaine vidéo générée sera envoyée automatiquement en brouillon TikTok.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
