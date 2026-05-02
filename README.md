# 🎬 Vidéos IA Mayotte — Génération automatique TikTok

Site qui génère automatiquement des vidéos courtes (9:16, 50s) en français sur Mayotte :
**actualités**, **légendes mahoraises**, **faits insolites**. Tout est gratuit.

## 📦 Stack utilisée (100 % gratuit)

| Composant | Outil | Rôle |
|---|---|---|
| Scénario | [Groq](https://groq.com) (Llama 3.3) | Génère le titre + scènes + image prompts en JSON |
| Voix off | [Edge-TTS](https://github.com/rany2/edge-tts) | Voix française naturelle (Microsoft) |
| Images | [Pollinations.ai](https://pollinations.ai) | Génération image (Flux) sans inscription |
| Montage | [FFmpeg](https://ffmpeg.org) | Assemble images + voix + sous-titres animés |
| Sous-titres | ASS / libass | Sous-titres karaoké style TikTok |
| Cron 12 h | GitHub Actions | Lance le script automatiquement |
| Galerie | HTML + Python `http.server` | Visualise les vidéos en local |

## 🚀 Démarrer (en local sur ton PC)

### 1. Pré-requis

- **Python 3.12+** ([python.org](https://www.python.org/downloads/))
- **FFmpeg** : `winget install Gyan.FFmpeg` (Windows)
- **Une clé API Groq gratuite** : crée un compte sur https://console.groq.com/keys puis copie ta clé

### 2. Installation

```bash
# Crée un environnement virtuel
python -m venv .venv
.venv\Scripts\activate     # Windows
# source .venv/bin/activate  # macOS/Linux

# Installe les dépendances
pip install -r requirements.txt

# Configure ta clé API
copy .env.example .env     # Windows
# cp .env.example .env       # macOS/Linux
# puis ouvre .env et colle ta clé Groq
```

### 3. Génération d'une vidéo

```bash
# Thème aléatoire
python generate_video.py

# Thème forcé
python generate_video.py --topic actu_mayotte
python generate_video.py --topic legende_mahoraise
python generate_video.py --topic fait_insolite
```

La vidéo `.mp4` apparaît dans `output/` avec un fichier `.json` de métadonnées.

### 4. Galerie web

```bash
python serve.py
```

Ouvre automatiquement http://localhost:8000 — tu vois toutes tes vidéos avec
bouton **Télécharger** pour publier sur TikTok manuellement.

## ⚙️ Automatisation toutes les 12 h via GitHub Actions

1. Crée un dépôt GitHub privé et pousse ce projet :
   ```bash
   git init
   git add .
   git commit -m "init"
   git branch -M main
   git remote add origin https://github.com/TON_USER/ton-repo.git
   git push -u origin main
   ```
2. Sur GitHub : **Settings → Secrets and variables → Actions → New secret**
   - Nom : `GROQ_API_KEY`
   - Valeur : ta clé Groq
3. Le workflow `.github/workflows/generate-video.yml` tournera automatiquement à
   **06:00 et 18:00 UTC** (08 h / 20 h Paris) et committera la vidéo dans `output/`.
4. Tu peux aussi le lancer à la main : onglet **Actions → Run workflow**.

## 📁 Structure du projet

```
.
├── generate_video.py          # script principal (1 vidéo)
├── test_pipeline.py           # test sans Groq
├── serve.py                   # mini-serveur galerie web
├── src/
│   ├── config.py              # paramètres (résolution, voix, ffmpeg)
│   ├── topics.py              # thèmes + prompts système
│   ├── script_writer.py       # appel Groq → JSON scénario
│   ├── voice.py               # Edge-TTS (voix + SRT)
│   ├── images.py              # Pollinations.ai
│   ├── subtitles.py           # SRT → ASS animés
│   └── editor.py              # FFmpeg (Ken Burns + concat)
├── web/index.html             # galerie HTML
├── output/                    # vidéos générées (.mp4 + .json)
└── .github/workflows/         # GitHub Actions (cron 12 h)
```

## 🎯 Publication TikTok

**Pour l'instant : manuel.** Une fois la vidéo générée :
1. Ouvre `web/index.html` (ou lance `python serve.py`)
2. Clique **Télécharger** sur la vidéo
3. Ouvre TikTok, importe la vidéo, clique **Publier**

**Plus tard : semi-automatique** (via TikTok Content Posting API). Les vidéos
seront poussées en *brouillon privé* sur ton compte. Il te restera à ouvrir
l'app et cliquer **Publier**.

## 🔧 Personnalisation rapide

- **Voix** : modifie `VOICE` dans `src/config.py`. Liste : `edge-tts --list-voices`
- **Résolution** : par défaut 1080×1920 (TikTok). Modifiable dans `config.py`.
- **Style sous-titres** : édite la `Style:` dans `src/subtitles.py`.
- **Thèmes** : ajoute/modifie dans `src/topics.py`.

## 💰 Limites gratuites à connaître

- **Groq** : 6 000 tokens/min gratuits → largement suffisant (1 vidéo = ~500 tokens)
- **Pollinations.ai** : illimité mais lent en heures de pointe (60-90 s/image)
- **Edge-TTS** : illimité
- **GitHub Actions** : 2 000 minutes gratuites/mois → 60 vidéos/mois en cron 12 h ✅

## ⚠️ Note importante

TikTok est strict sur les comptes qui publient du contenu IA en boucle.
Recommandé : **regarder/valider les vidéos avant publication**. La galerie web
est faite pour ça.
