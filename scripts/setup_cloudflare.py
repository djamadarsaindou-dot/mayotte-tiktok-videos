"""Wizard de configuration Cloudflare Workers AI (génération d'images IA).

Cloudflare Workers AI remplace Pollinations (devenu payant en mai 2026).
Free tier : 10 000 neurons/jour (~130 images), sans carte bancaire.

Étapes À FAIRE AVANT ce script :
1. Compte gratuit sur https://dash.cloudflare.com/sign-up
2. Account ID : menu « Workers & Pages » → barre de droite (32 caractères hex)
3. API Token : https://dash.cloudflare.com/profile/api-tokens
   → Create Token → template « Workers AI » → Create Token → copier

Usage :
    python scripts/setup_cloudflare.py <ACCOUNT_ID> <API_TOKEN>
    ou : python scripts/setup_cloudflare.py     (mode interactif)

Le script teste les identifiants en générant une vraie image, puis les
enregistre dans .env si le test réussit.
"""
import base64
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

MODEL = "@cf/black-forest-labs/flux-1-schnell"


def main() -> int:
    if len(sys.argv) >= 3:
        account_id = sys.argv[1].strip()
        api_token = sys.argv[2].strip()
    else:
        print("┌─────────────────────────────────────────────────────────────")
        print("│ 🎨 Configuration Cloudflare Workers AI (images IA)")
        print("└─────────────────────────────────────────────────────────────")
        print()
        account_id = input("📥 Account ID Cloudflare : ").strip()
        api_token = input("📥 API Token Cloudflare  : ").strip()

    if not account_id or not api_token:
        print("❌ Account ID et API Token sont tous deux requis.")
        return 1

    print()
    print("🔍 Test : génération d'une image via FLUX-schnell...")
    url = (f"https://api.cloudflare.com/client/v4/accounts/"
           f"{account_id}/ai/run/{MODEL}")
    try:
        r = requests.post(
            url,
            json={"prompt": "a turquoise tropical lagoon in Mayotte, "
                            "aerial view, cinematic", "steps": 4},
            headers={"Authorization": f"Bearer {api_token}"},
            timeout=120,
        )
    except Exception as e:
        print(f"❌ Connexion à Cloudflare échouée : {e}")
        return 1

    if r.status_code in (401, 403):
        print(f"❌ Token rejeté (HTTP {r.status_code}).")
        print("   Vérifie que le token a bien la permission « Workers AI ».")
        print(f"   {r.text[:300]}")
        return 1
    if r.status_code != 200:
        print(f"❌ Erreur HTTP {r.status_code} :")
        print(f"   {r.text[:400]}")
        return 1

    try:
        data = r.json()
    except Exception:
        print(f"❌ Réponse non-JSON : {r.text[:300]}")
        return 1

    b64 = data.get("result", {}).get("image")
    if not b64:
        print(f"❌ Réponse sans image : {data}")
        return 1

    # Sauvegarde l'image de test pour inspection visuelle
    test_img = Path(__file__).resolve().parent.parent / "output" / "cloudflare_test.jpg"
    test_img.parent.mkdir(parents=True, exist_ok=True)
    test_img.write_bytes(base64.b64decode(b64))
    print(f"✅ Image test générée : {test_img}")
    print("   (ouvre-la pour vérifier la qualité)")

    # Sauvegarde dans .env
    from src.tiktok_publisher import update_env_vars
    update_env_vars({
        "CLOUDFLARE_ACCOUNT_ID": account_id,
        "CLOUDFLARE_API_TOKEN": api_token,
    })
    print()
    print("┌─────────────────────────────────────────────────────────────")
    print("│ ✅ Cloudflare Workers AI configuré et testé !")
    print("│")
    print("│ Les prochaines vidéos utiliseront FLUX-schnell pour les")
    print("│ images IA (12 par vidéo). Free tier : ~130 images/jour.")
    print("└─────────────────────────────────────────────────────────────")
    return 0


if __name__ == "__main__":
    sys.exit(main())
