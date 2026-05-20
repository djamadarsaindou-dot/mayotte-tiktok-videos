"""Wizard pour configurer les notifications Telegram.

Étape 1 (à faire MANUELLEMENT avant de lancer ce script) :
- Sur Telegram, parler à @BotFather
- Envoyer /newbot
- Choisir un nom (ex : « Mayotte TikTok Bot »)
- Choisir un username unique (ex : « mayotte_tiktok_djam_bot »)
- BotFather te donne un TOKEN du genre `123456:ABC-DEF1234ghIkl...`

Étape 2 (à faire MANUELLEMENT) :
- Cliquer sur le lien `t.me/<username_du_bot>` que BotFather t'a donné
- Cliquer « Start » dans la conversation
- Envoyer n'importe quel message au bot (ex : « salut »)

Étape 3 : lancer ce script avec le token
- python scripts/setup_telegram.py <TOKEN>
- ou : python scripts/setup_telegram.py (il te demandera le token)

Le script récupère ton chat_id automatiquement et l'écrit dans .env.
"""
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def main() -> int:
    # Récupère le token
    if len(sys.argv) > 1:
        token = sys.argv[1].strip()
    else:
        print("┌─────────────────────────────────────────────────────────────")
        print("│ 🤖 Configuration Telegram pour notifications brouillon TikTok")
        print("└─────────────────────────────────────────────────────────────")
        print()
        print("Avant ce script tu dois avoir :")
        print("  1. Créé un bot via @BotFather sur Telegram")
        print("  2. Cliqué « Start » dans la conversation avec ton bot")
        print("  3. Envoyé au moins un message au bot")
        print()
        token = input("📥 Colle ici le TOKEN du bot (de BotFather) : ").strip()

    if not token or ":" not in token:
        print("❌ Token invalide (devrait ressembler à `123456:ABC-DEF...`)")
        return 1

    print()
    print("🔍 Récupération des messages du bot...")
    try:
        r = requests.get(f"https://api.telegram.org/bot{token}/getUpdates", timeout=15)
    except Exception as e:
        print(f"❌ Connexion Telegram échouée : {e}")
        return 1

    if r.status_code != 200:
        print(f"❌ Telegram HTTP {r.status_code}: {r.text[:300]}")
        return 1

    data = r.json()
    if not data.get("ok"):
        print(f"❌ Réponse Telegram : {data}")
        return 1

    updates = data.get("result", [])
    if not updates:
        print()
        print("⚠️  Aucun message reçu par le bot.")
        print("    → Va sur Telegram, ouvre ton bot, clique « Start » et envoie")
        print("      n'importe quel message, puis relance ce script.")
        return 1

    # Prend le chat_id du dernier message
    last = updates[-1]
    msg = last.get("message") or last.get("edited_message") or {}
    chat = msg.get("chat", {})
    chat_id = chat.get("id")
    first_name = chat.get("first_name", "?")
    if not chat_id:
        print(f"❌ Impossible d'extraire chat_id : {last}")
        return 1

    print(f"✅ Trouvé : chat_id={chat_id} (utilisateur : {first_name})")

    # Test : envoie un message
    print()
    print("📲 Test : envoi d'un message de bienvenue...")
    test = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": "🎬 *Mayotte TikTok Bot activé !*\n\nTu recevras une notif ici à chaque vidéo prête à publier.",
            "parse_mode": "Markdown",
        },
        timeout=15,
    )
    if test.status_code != 200:
        print(f"⚠️  Envoi test échoué : HTTP {test.status_code}")
        print(f"    {test.text[:300]}")
        return 1

    # Sauvegarde dans .env
    from src.tiktok_publisher import update_env_vars
    update_env_vars({
        "TELEGRAM_BOT_TOKEN": token,
        "TELEGRAM_CHAT_ID": str(chat_id),
    })

    print()
    print("┌─────────────────────────────────────────────────────────────")
    print("│ ✅ Telegram configuré et testé !")
    print("│")
    print("│ Vérifie ton Telegram : tu devrais voir le message de bienvenue.")
    print("│")
    print("│ La prochaine vidéo générée déclenchera une notif Telegram")
    print("│ avec un bouton « Ouvrir TikTok » pour aller direct au brouillon.")
    print("└─────────────────────────────────────────────────────────────")
    return 0


if __name__ == "__main__":
    sys.exit(main())
