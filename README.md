# 🎬 Mayotte TikTok — Génération automatique de vidéos

Pipeline Python qui génère et publie automatiquement des vidéos TikTok éducatives sur **Mayotte** : légendes mahoraises, traditions, faune, faits insolites, actualités locales. Cron toutes les **6h**, voix off humaine, sous-titres karaoké, publication directe vers la boîte de réception TikTok.

> 🔗 **Compte TikTok :** [@mister_decouverte](https://www.tiktok.com/@mister_decouverte)
> 📄 **Privacy policy** • **Terms** : voir [`docs/`](docs/)

---

## 📦 Stack (100% gratuit)

| Composant | Outil | Rôle |
|---|---|---|
| Scénario | **Mistral Large** (fallback Gemini / Groq) | Génère titre + 12 scènes + image prompts en JSON |
| Voix off | **Coqui XTTS v2** (fallback Edge-TTS) | Voix française humaine clonée |
| Audio mastering | FFmpeg (loudnorm + EQ) | Niveau broadcast TikTok (-14 LUFS) |
| Images | **Pollinations Flux** + Pexels/Pixabay/Wikimedia | 16 visuels IA + 48 stock |
| Montage | **FFmpeg** (preset ultrafast) | Concat + Ken Burns + sous-titres karaoké |
| Sous-titres | ASS / libass | Karaoké style TikTok |
| Publication | **TikTok Content Posting API** (mode INBOX) | Brouillon dans l'app, validation 1-clic |
| Notification | **Telegram bot** | Push sur le tel quand brouillon prêt |
| Cron 6h | Windows Task Scheduler / Startup | 4 vidéos/jour |

---

## 🎯 Fonctionnalités

- ✅ **Rotation thématique** : 5 thèmes en boucle (découverte, tradition, légende, insolite, actu)
- ✅ **Anti-doublon** : verrou atomique (jamais 2 générations en parallèle)
- ✅ **Cache LLM** : évite de regénérer le même contenu (30j TTL)
- ✅ **Auto-publication TikTok** : upload INBOX → notif Telegram avec lien deep
- ✅ **Notification Windows** : toast avec bouton "Ouvrir le dossier"
- ✅ **Cleanup auto** : garde les N dernières vidéos (par défaut 50)
- ✅ **Auto-refresh tokens** : TikTok access_token rafraîchi automatiquement
- ✅ **Sous-titres karaoké** : highlight mot par mot, animation
- ✅ **Hook visuel** : titre animé en intro pour retenir l'attention TikTok
- ✅ **Progress bar** : barre de progression en bas de la vidéo

---

## 🚀 Démarrer en local

### 1. Pré-requis

- Python 3.12+ ([python.org](https://www.python.org/downloads/))
- FFmpeg (`winget install Gyan.FFmpeg` sur Windows)
- Une clé API LLM (Mistral / Groq / Gemini — tous gratuits)

### 2. Installation

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Édite `.env` et colle ta clé Mistral (recommandé) :

```env
MISTRAL_API_KEY=ta_clé
TTS_PROVIDER=coqui
```

### 3. Générer une vidéo

```bash
python generate_video.py
# ou forcer un thème :
python generate_video.py --topic legende_mahoraise
```

La vidéo MP4 (1080×1920, ~110s) apparaît dans `output/` et est copiée dans `~/Videos/Mayotte TikTok/`.

---

## 🤖 Auto-publication TikTok

### Setup unique (10 min)

```bash
# 1. Crée une app sur https://developers.tiktok.com/apps
# 2. Récupère client_key + client_secret, colle-les dans .env
# 3. OAuth via Postman relay (TikTok refuse localhost) :
python scripts/setup_tiktok.py
# 4. Active :
echo TIKTOK_AUTO_PUBLISH=true >> .env
```

### Notification Telegram (optionnel)

```bash
# 1. Crée un bot via @BotFather sur Telegram, récupère le TOKEN
# 2. Ouvre une conv avec ton bot, envoie un message
python scripts/setup_telegram.py
```

À chaque vidéo générée, tu reçois une notif Telegram avec un bouton **« Ouvrir TikTok »**.

---

## 🔁 Cron toutes les 6h

Windows Task Scheduler (recommandé) ou Startup folder. Le script `cron_loop.py` gère le verrouillage anti-doublon.

```bash
# Lancement manuel du cron en boucle :
python cron_loop.py
```

---

## 📁 Structure

```
.
├── generate_video.py          # Script principal (1 vidéo)
├── cron_loop.py               # Boucle toutes les 6h
├── src/
│   ├── config.py              # Paramètres globaux
│   ├── topics.py              # Rotation des thèmes
│   ├── script_writer.py       # Mistral / Gemini / Groq
│   ├── llm_cache.py           # Cache disque LLM
│   ├── llm.py                 # Wrapper LLM multi-provider
│   ├── voice_coqui.py         # Coqui XTTS v2 (voix clonée)
│   ├── voice.py               # Edge-TTS fallback
│   ├── audio_master.py        # Loudnorm + EQ broadcast
│   ├── images.py              # Pollinations Flux
│   ├── stock_*.py             # Pexels, Pixabay, Wikimedia
│   ├── subtitles.py           # Karaoké ASS
│   ├── editor.py              # FFmpeg orchestration
│   ├── tiktok_publisher.py    # Content Posting API
│   ├── telegram_notifier.py   # Bot Telegram
│   ├── notify.py              # Toast Windows
│   ├── locking.py             # Verrou atomique
│   ├── mayotte_knowledge.py   # Connaissances pré-encodées
│   └── news_rss.py            # Flux RSS Mayotte la 1ère / Mayotte Hebdo
├── scripts/
│   ├── setup_tiktok.py        # Wizard OAuth TikTok
│   └── setup_telegram.py      # Wizard bot Telegram
├── docs/                      # Privacy + Terms (GitHub Pages)
├── output/                    # Vidéos générées
└── assets/                    # Voix de référence, musique de fond
```

---

## ⚠️ Notes

- L'app est **personnelle** : utilisée uniquement par son auteur pour son propre compte `@mister_decouverte`. Pas d'utilisateurs tiers, pas de collecte de données.
- L'audit TikTok pour le scope `video.publish` (publication directe) est en cours. En attendant : mode INBOX = brouillon + clic manuel.
- Toutes les vidéos respectent les [TikTok Community Guidelines](https://www.tiktok.com/community-guidelines) (contenu éducatif uniquement).

---

## 📄 Licence

MIT — voir [LICENSE](LICENSE).
