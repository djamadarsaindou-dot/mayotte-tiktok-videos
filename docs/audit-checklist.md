# 📋 Audit TikTok — Checklist de soumission

## Avant de soumettre (à préparer)

### 1. URLs publiques (GitHub Pages — étape suivante)

Une fois GitHub Pages activé sur le repo, ces URLs seront live :

- **Home :** https://djamadarsaindou-dot.github.io/mayotte-tiktok-videos/
- **Privacy Policy :** https://djamadarsaindou-dot.github.io/mayotte-tiktok-videos/privacy.html
- **Terms of Service :** https://djamadarsaindou-dot.github.io/mayotte-tiktok-videos/terms.html

### 2. Activer GitHub Pages

1. https://github.com/djamadarsaindou-dot/mayotte-tiktok-videos/settings/pages
2. Section "Build and deployment"
3. **Source :** Deploy from a branch
4. **Branch :** `main` — Folder : `/docs`
5. Save → attendre 2-3 minutes → URLs ci-dessus accessibles

### 3. Vidéo de démo (à enregistrer)

Format attendu par TikTok : screencast de 30s à 2min qui montre :
- Lancement du script `generate_video.py`
- Génération de la vidéo (timelapse OK)
- Upload TikTok via API
- Vidéo qui apparaît dans la boîte de réception

Outils : OBS Studio (gratuit) ou Xbox Game Bar (Win+G intégré Windows).

---

## Soumission sur le dev portal TikTok

URL : https://developers.tiktok.com/apps → ton app → "Go Live"

### Champs du formulaire

| Champ | Valeur |
|---|---|
| **App name** | Mayotte TikTok |
| **App description** | Application personnelle d'auto-publication de vidéos éducatives sur Mayotte (légendes, traditions, faune, actualités). Génère des vidéos verticales 1080×1920 via IA et les publie sur @mister_decouverte. |
| **Category** | Content Creation / Tools |
| **Platform** | Web / Server-side script |
| **Website URL** | https://djamadarsaindou-dot.github.io/mayotte-tiktok-videos/ |
| **Privacy Policy URL** | https://djamadarsaindou-dot.github.io/mayotte-tiktok-videos/privacy.html |
| **Terms of Service URL** | https://djamadarsaindou-dot.github.io/mayotte-tiktok-videos/terms.html |
| **Redirect URI** | https://oauth.pstmn.io/v1/callback (Postman relay, déjà configuré) |

### Scopes demandés

- ✅ `user.info.basic` (déjà actif)
- ✅ `video.upload` (déjà actif — mode INBOX)
- 🆕 `video.publish` (à demander pour Direct Post public)

### Justification du scope `video.publish`

Texte à coller dans le formulaire d'audit :

> Cette application est un outil personnel d'auto-publication développé par son
> auteur pour son propre compte TikTok @mister_decouverte. Le scope video.publish
> est nécessaire pour finaliser l'automatisation : la vidéo générée par le
> pipeline doit être publiée directement sans intervention manuelle, à raison
> de maximum 4 vidéos par jour (cron toutes les 6h). Toutes les vidéos respectent
> les Community Guidelines TikTok (contenu éducatif uniquement, aucune désinformation,
> aucun spam). Le contenu est généré par IA sur la base de connaissances générales
> sur l'île de Mayotte et de flux RSS d'actualités locales officielles.

---

## Délai et suite

- **Délai officiel TikTok :** 2-6 semaines (variable, parfois 3-5 jours)
- **Pendant l'attente :** le mode INBOX (clic manuel) continue de fonctionner
- **Si refus :** TikTok donne la raison → on adapte et on resoumet
- **Si validation :** je code l'endpoint `Direct Post` (très proche du INBOX existant)

---

## Notes

- Pas besoin de PRD complet ni de mockups : TikTok comprend que c'est une app perso
- La démo vidéo est le plus important — montre concrètement que l'app fait du contenu sain
- L'app ne sera utilisée QUE par toi → c'est un point important à souligner (pas de risque pour d'autres utilisateurs)
