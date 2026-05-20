"""Wizard de configuration OAuth TikTok — à lancer UNE SEULE FOIS.

TikTok n'accepte plus `localhost` comme Redirect URI (même en Sandbox).
On utilise donc le relais public Postman OAuth (`https://oauth.pstmn.io/v1/callback`)
qui affiche simplement le `code` reçu de TikTok à l'écran — tu le copies-colles
dans le terminal.

Pré-requis AVANT de lancer ce script :
- Une app TikTok Sandbox créée sur https://developers.tiktok.com/apps
- TIKTOK_CLIENT_KEY et TIKTOK_CLIENT_SECRET dans .env
- Dans Login Kit : Redirect URI = https://oauth.pstmn.io/v1/callback
- Scopes : user.info.basic + video.upload
- Ton compte TikTok ajouté comme « Target User » du Sandbox

Usage :
    python scripts/setup_tiktok.py
"""
import os
import secrets
import sys
import urllib.parse
import webbrowser
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

AUTH_URL = "https://www.tiktok.com/v2/auth/authorize/"
TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"
REDIRECT_URI = "https://oauth.pstmn.io/v1/callback"
SCOPES = "user.info.basic,video.upload"


def main() -> int:
    from dotenv import load_dotenv
    env_path = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(env_path, override=True)

    client_key = os.getenv("TIKTOK_CLIENT_KEY", "").strip()
    client_secret = os.getenv("TIKTOK_CLIENT_SECRET", "").strip()
    if not client_key or not client_secret:
        print("❌ TIKTOK_CLIENT_KEY et/ou TIKTOK_CLIENT_SECRET manquent dans .env")
        print("   Crée d'abord une app sur https://developers.tiktok.com/apps")
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

    print("┌─────────────────────────────────────────────────────────────")
    print("│ 🌐 Étape 1 : ouverture de TikTok pour autorisation")
    print("└─────────────────────────────────────────────────────────────")
    print(f"\n   {auth_url}\n")
    webbrowser.open(auth_url)

    print("┌─────────────────────────────────────────────────────────────")
    print("│ 📋 Étape 2 : autorise l'app sur TikTok")
    print("│    → Connecte-toi avec ton compte target user")
    print("│    → Clique « Autoriser »")
    print("│    → TikTok te redirige sur oauth.pstmn.io qui affiche")
    print("│      le `code` et le `state`")
    print("└─────────────────────────────────────────────────────────────")
    print()
    print(f"   state attendu : {state}")
    print()

    # On demande le code en stdin (l'utilisateur le copie depuis oauth.pstmn.io)
    code = input("📥 Colle ici le code reçu (champ `code`) : ").strip()
    if not code:
        print("❌ Code vide, annulation.")
        return 1
    returned_state = input("📥 Et le state (champ `state`) : ").strip()
    if returned_state and returned_state != state:
        print("❌ State CSRF différent de ce qu'on attendait — annulation.")
        print(f"   attendu : {state}")
        print(f"   reçu    : {returned_state}")
        return 1

    print("\n🔄 Échange du code contre les tokens TikTok...")
    r = requests.post(
        TOKEN_URL,
        data={
            "client_key": client_key,
            "client_secret": client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": REDIRECT_URI,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30,
    )
    if r.status_code != 200:
        print(f"❌ Échange token a échoué : HTTP {r.status_code}")
        print(r.text[:600])
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
    print()
    print("Active l'auto-publication en ajoutant cette ligne à .env :")
    print("    TIKTOK_AUTO_PUBLISH=true")
    print()
    print("La prochaine vidéo générée par le cron sera envoyée automatiquement")
    print("dans tes brouillons TikTok (tu valides en 1 clic dans l'app).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
