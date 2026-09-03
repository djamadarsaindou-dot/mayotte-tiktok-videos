# 🎬 HANDOFF — Usine à vidéos TikTok automatiques

> **Pour une nouvelle session Claude Code** : lis ce fichier en entier avant toute
> action. Il contient tout le contexte du projet, les décisions prises, les pièges,
> et l'état actuel. Le code fait foi — vérifie les `file:line` avant d'affirmer.

---

## 1. Ce que fait le projet

Pipeline Python **100 % automatique** qui génère et publie des vidéos verticales
TikTok (9:16, ~2min), en français, sur des sujets fascinants **vérifiés**.
Chaîne cible : **@mister_decouverte** (compte de l'utilisateur, Djama).

Cycle : un cron génère 2 vidéos/jour (8h et 18h) → upload en **brouillon** dans la
boîte de réception TikTok via l'API → notif Telegram → l'utilisateur valide en
1 clic dans l'app (il ajoute lui-même un son natif TikTok à ce moment).

- **Dossier projet** : `C:\Users\djama\Documents\Claude\Projects\Site internet - Montage vidéo`
- **Repo GitHub (public)** : `djamadarsaindou-dot/mayotte-tiktok-videos`
- **Sorties** : `C:\Users\djama\Videos\Mayotte TikTok\` (.mp4 + .txt légende)
- **Env Python** : `.venv\Scripts\python.exe` (Python 3.14, Windows)

---

## 2. Stack (100 % gratuit sauf mention)

| Étape | Techno | Détail |
|---|---|---|
| Script | **Mistral Large** API (`src/llm.py`) | fallback auto Groq. Gemini bloqué géographiquement à Mayotte — ne pas réessayer. Cache disque `src/llm_cache.py`. |
| Sujets | Banque de faits vérifiés `src/mayotte_knowledge.py` | ~120 sujets Mayotte + sujets « monde » en cours d'ajout. Anti-répétition `output/used_topics.json`. |
| Voix | **Edge-TTS** (`src/voice.py`) | `TTS_PROVIDER=edge`, voix `fr-FR-RemyMultilingualNeural`, `EDGE_RATE=-6%`, `EDGE_PITCH=-10Hz` → ton **« vieux conteur »** choisi par l'utilisateur. Cloud, ~10s/vidéo. Coqui/Chatterbox en fallback (lents, CPU). |
| Images | **Cloudflare Workers AI** FLUX-schnell (`src/cloudflare_images.py`) | Free tier ~130 img/jour. Mode **100 % IA** : 48 images/vidéo (`VISUALS_AI_ONLY=true`). Circuit breaker sur 402/429 → fallback stock. |
| Stock (fallback) | Pexels/Pixabay/Wikimedia (`src/stock_*.py`) | Utilisé seulement si l'IA échoue. |
| Sous-titres | Karaoké ASS (`src/subtitles.py`) | Montserrat Black bundlée dans `assets/fonts`. |
| Montage | FFmpeg (`src/editor.py`) | Ken Burns, color grading, mastering audio -14 LUFS. Voir §5 pour l'état ÉPURÉ. |
| Réseau | Session résiliente `src/net.py` | urllib3 Retry + backoff — indispensable, connexion Mayotte très instable. |
| Upload TikTok | Content Posting API INBOX (`src/tiktok_publisher.py`) | chunks configurables `TIKTOK_CHUNK_MB=5` (petit = robuste). |
| Notif | Bot Telegram (`src/telegram_notifier.py`) | notif « brouillon prêt » + bouton Ouvrir TikTok. |
| Planificateur | `scripts/cron_loop.py` | créneaux `SLOT_HOURS = [8, 18]`. Lancé par .bat au démarrage Windows (Task Scheduler bloqué par la politique domaine). Verrou `src/locking.py`. |

---

## 3. Configuration `.env` (gitignoré — clés jamais commitées)

```
MISTRAL_API_KEY=…            GROQ_API_KEY=…
PEXELS_API_KEY=…             PIXABAY_API_KEY=…
CLOUDFLARE_ACCOUNT_ID=b7f6c4823bd4bcad39cfe2e14d9c5e8e
CLOUDFLARE_API_TOKEN=…
TIKTOK_CLIENT_KEY=…  TIKTOK_CLIENT_SECRET=…  TIKTOK_ACCESS_TOKEN=…  TIKTOK_REFRESH_TOKEN=…
TIKTOK_AUTO_PUBLISH=true     TIKTOK_CHUNK_MB=5
TELEGRAM_BOT_TOKEN=…         TELEGRAM_CHAT_ID=…
TTS_PROVIDER=edge  EDGE_VOICE=fr-FR-RemyMultilingualNeural  EDGE_RATE=-6%  EDGE_PITCH=-10Hz
VISUALS_AI_ONLY=true         POLLINATIONS_PARALLEL=2
```

Scripts de (re)configuration one-shot : `scripts/setup_tiktok.py` (OAuth via relais
`oauth.pstmn.io`, TikTok refuse localhost), `scripts/setup_telegram.py`,
`scripts/setup_cloudflare.py`.

---

## 4. Commandes utiles

```bash
# Générer UNE vidéo (test manuel)
.venv/Scripts/python.exe generate_video.py

# Lancer le cron (boucle 8h/18h)
.venv/Scripts/python.exe scripts/cron_loop.py

# Nettoyer les process zombies AVANT un lancement manuel (fréquent après un test coupé)
#   PowerShell : tuer les python.exe 'generate_video' + les ffmpeg, puis supprimer logs/generate.lock
```

---

## 5. ⚠️ ÉTAT ACTUEL — travail en cours (15/07/2026)

Deux changements demandés par l'utilisateur, **en cours de finalisation** :

### A. Montage ÉPURÉ (demande explicite : « trop de trucs, ça devient ridicule »)
L'utilisateur veut **UNIQUEMENT images + sous-titres karaoké**. À RETIRER de
`src/subtitles.py` (fonctions présentes mais à désactiver dans `build_karaoke_ass`)
et `src/editor.py` :
- ❌ barre de progression, ❌ hook texte géant (`_hook_lines`), ❌ emojis (`_emoji_lines`),
  ❌ gros chiffres (`_number_lines`), ❌ « ABONNE-TOI » (`_cta_lines`), ❌ étiquette 📍
  (`_label_lines`), ❌ watermark @mister_decouverte (style Brand), ❌ flash blanc d'intro,
  ❌ punch-ins, ❌ vignette/grain si jugés « too much ».
- ✅ GARDER : les images (Ken Burns discret ok), le color grading léger, et le
  **karaoké mot-à-mot** seul.
- **Vérifier `build_karaoke_ass` dans `src/subtitles.py`** : commenter/retirer les
  `lines.extend(_hook_lines…)`, `_number_lines`, `_emoji_lines`, `_cta_lines`,
  `_label_lines` et la ligne Dialogue « Brand ». Retirer les filtres correspondants
  dans le `vf` de `assemble_video` (`src/editor.py`) : bar_filter, hook_intro_fade,
  punch_filter, grain.

### B. Sujets AU-DELÀ de Mayotte (demande : « des vidéos sur autre chose, sujets qui percent »)
La chaîne s'ouvre à des sujets viraux généralistes. **5 thèmes monde** recherchés
(faits vérifiés, hooks TikTok) : **espace/univers, animaux incroyables, histoires
vraies stupéfiantes, corps humain/cerveau, lieux extrêmes du monde**.
- Une 1ère vidéo espace a déjà été produite et validée techniquement :
  « 73 000 ans pour toucher une étoile » (100 % images IA, hashtags `#espace #astronomie`).
- **À FAIRE** : intégrer ces ~75 sujets monde dans `src/mayotte_knowledge.py` (ou un
  nouveau module type `src/world_knowledge.py`) + les brancher dans la rotation de
  thèmes (`src/topics.py`). Recherches lancées via 5 sous-agents (relancer si besoin :
  espace, animaux, histoires vraies, corps humain, lieux extrêmes).
- **Attention** : le module s'appelle encore `mayotte_knowledge` mais le projet n'est
  plus 100 % Mayotte. Prompts LLM (`src/script_writer.py`) et hashtags à
  dé-mayottiser pour les sujets monde (ne pas forcer `#mayotte` sur une vidéo espace).

---

## 6. Préférences utilisateur (IMPORTANT — respecter)

- **Débutant**, francophone, à Mayotte. Veut de l'accompagnement pas-à-pas, des choix
  techniques par défaut, et des explications simples.
- **Qualité > volume** : a choisi 2 vidéos/jour plutôt que 4.
- **Montage sobre** : déteste le montage surchargé (cf §5A).
- **Voix** : a écouté 12 échantillons et choisi Rémy « vieux conteur » (grave + lent).
- **Musique** : NE PAS intégrer de musique de fond — il ajoute un son natif TikTok
  dans l'app (meilleur pour l'algo).
- **Notifications** : pendant une génération, le prévenir **UNIQUEMENT à la fin**
  (vidéo prête / Telegram), pas à chaque étape/chunk.
- **Budget** : 50€/mois envisagé mais pas engagé. Pistes payantes évoquées :
  ElevenLabs (voix, ~22€), FLUX pro (images 9:16 natives, ~20€), Runway (vidéos IA).
- **Sécurité** : refuse le clonage de voix d'une personne réelle identifiable.
  A des tokens qui ont transité en chat (Telegram, Cloudflare, PAT GitHub `ghp_3kRZobS…`)
  → lui rappeler de les régénérer.
- **Rigueur factuelle** : aucune invention dans les faits narrés. Sujets sensibles
  (immigration, pauvreté) volontairement écartés. Fait à éviter : « ZEE 2e de France »
  (faux).

---

## 7. Pièges connus (NE PAS refaire)

- **Zombies** : un test coupé laisse des `generate_video.py` bloqués sur sockets +
  des `ffmpeg`. Toujours nettoyer (PowerShell kill + `rm logs/generate.lock`) avant
  un lancement manuel.
- **Launcher venv** : `.venv\Scripts\python.exe` crée 2 process (launcher + worker).
  Ce n'est **pas** un doublon de cron — ne pas paniquer.
- **FFmpeg `scale` dynamique** : besoin de `eval=frame` pour utiliser `t`. Le `crop`
  par défaut est figé à l'init → recentrer avec `x`/`y` explicites recalculés par frame.
- **drawtext FFmpeg sur Windows** : échoue (fontconfig absent). Faire le texte via ASS
  (`fontsdir`), pas via `drawtext`.
- **TikTok upload** : chunks de 5 MB (`TIKTOK_CHUNK_MB=5`) car connexion instable.
  HTTP 416 sur un chunk = doublon déjà reçu, PAS une erreur. Sur échec réseau, une
  boucle de retry externe (toutes les ~10 min) finit par passer.
- **Verrou** (`src/locking.py`) : l'atexit ne libère le lock que si le PID correspond
  (fix commité) — évite qu'un process qui meurt efface le lock d'un autre.
- **cmd Windows fr** : lit les .bat en CP-850, pas UTF-8 (accents cassent le `cd`).

---

## 8. Chantiers ouverts (aucun urgent)

1. Finaliser §5A (montage épuré) et §5B (sujets monde + dé-mayottisation).
2. **Audit TikTok** pour passer du brouillon à la publication 100 % auto (`docs/`
   contient les pages légales déjà en ligne via GitHub Pages ; il manque la
   vérification d'URL sur le portail dev — délai TikTok 2-6 semaines).
3. Pack payant si budget (ElevenLabs + FLUX pro).
4. Rôle humain de l'utilisateur : valider les brouillons, répondre aux commentaires
   la 1ère heure, regarder ce qui performe.

---

## 9. Comment reprendre proprement

1. `git pull` (le repo est à jour, tout est commité).
2. Lire `src/config.py` pour la liste vivante des réglages.
3. Vérifier l'état des demandes §5 dans le code (montage épuré fait ou non ? sujets
   monde intégrés ou non ?) — **le code fait foi, ce fichier peut dater**.
4. Pour tester : nettoyer les zombies, puis `generate_video.py`, surveiller le log
   dans `logs/run_*.log`, prévenir l'utilisateur seulement à la fin.
