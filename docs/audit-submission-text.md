# 📝 Textes à coller dans le formulaire d'audit TikTok

## App icon
Fichier : `docs/app-icon.png` (1024×1024, ~20 KB)

## Category
**Utilities** (déjà coché)

## Description (déjà saisie : 94/120)
```
Auto-publication de vidéos éducatives sur Mayotte (légendes, traditions, faune, actualités).
```

## App review explanation (979/1000 chars)
```
This is a personal automation tool used exclusively by its author (Djama Darsaindou) to publish educational videos about Mayotte (French overseas territory) on his own TikTok account @mister_decouverte. The app runs locally as a Python script with a 6-hour cron schedule.

Login Kit (user.info.basic): used once at OAuth setup to authenticate the author and retrieve his own open_id. No third-party user data accessed.

Content Posting API:
- video.upload: currently used in production via Sandbox mode. Each generated video is uploaded as an INBOX draft. The author manually validates the post from the TikTok app (1 click).
- video.publish: requested for full automation. Once approved, videos will be directly posted to the authors profile without manual intervention, at maximum 4 per day.

All videos respect TikTok Community Guidelines: educational content only (legends, traditions, fauna, official RSS news of Mayotte). No spam, no misinformation, no third-party content.
```

## URLs (toutes vers GitHub Pages — à vérifier via "Verify URL properties")
- **Web/Desktop URL :** `https://djamadarsaindou-dot.github.io/mayotte-tiktok-videos/`
- **Terms of Service URL :** `https://djamadarsaindou-dot.github.io/mayotte-tiktok-videos/terms.html`
- **Privacy Policy URL :** `https://djamadarsaindou-dot.github.io/mayotte-tiktok-videos/privacy.html`

## Redirect URI (Login Kit)
- **Web :** `https://oauth.pstmn.io/v1/callback`
- ⚠️ Bien cliquer **"Add a URI"** après collage pour valider

## Scopes à GARDER (3 seulement)
- ✅ `user.info.basic`
- ✅ `video.upload`
- ✅ `video.publish`

## Scopes à RETIRER (cochés par défaut)
- ❌ `user.info.profile`
- ❌ `user.info.stats`
- ❌ `video.list`

(Demander ces scopes en plus = audit refusé car on ne les utilise pas)

## Démo vidéo
- Format : MP4 ou MOV, max 50 MB
- Durée recommandée : 1-3 min
- Doit montrer :
  1. Lancement du script `generate_video.py`
  2. Pipeline qui tourne (peut être en timelapse)
  3. Appel API TikTok (publish_inbox)
  4. Vidéo qui apparaît dans la boîte de réception TikTok
