"""Sous-titres karaoké style TikTok haut de gamme.

Effets :
- Fond : 1 à 5 mots à la fois (borné en largeur), blanc, contour noir épais, ombre douce
- Mot actif : surligné jaune avec un petit pop-in (scale 115 → 100)
- Apparition : fade-in 80ms en bas, fade-out 80ms (transitions douces)
- Position : ancrée bas-centre (~70% hauteur), grande taille, lisible mobile
- Police : Montserrat Black bundlée dans assets/fonts (chargée via fontsdir FFmpeg)
- Emojis « kinetic pop » : DÉSACTIVÉS (voir EMOJIS_ENABLED) — libass ne rend
  pas les emojis couleur (tables COLR ignorées), ils sortaient en contours
  monochromes cassés. Les pictogrammes inline (📍 du label, 🔔 du CTA) sont
  conservés : rendus volontairement en contours Segoe UI Emoji, cohérents
  avec le texte blanc/contour noir.
"""
import unicodedata
from pathlib import Path

ASS_HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: {w}
PlayResY: {h}
ScaledBorderAndShadow: yes
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Base,Montserrat Black,108,&H00FFFFFF,&H000000FF,&H00000000,&HAA000000,1,0,0,0,100,100,2,0,1,10,4,2,80,80,0,1
Style: Hilite,Montserrat Black,108,&H0000F0FF,&H000000FF,&H00000000,&HAA000000,1,0,0,0,100,100,2,0,1,10,4,2,80,80,0,1
Style: Keyword,Montserrat Black,108,&H00FF00FF,&H000000FF,&H00000000,&HAA000000,1,0,0,0,100,100,2,0,1,10,4,2,80,80,0,1
Style: Hook,Montserrat Black,82,&H0000F0FF,&H000000FF,&H00000000,&HCC000000,1,0,0,0,100,100,1,0,1,8,4,5,110,110,0,1
Style: Number,Montserrat Black,180,&H0000F0FF,&H000000FF,&H00000000,&H00000000,1,0,0,0,100,100,0,0,1,16,8,5,60,60,0,1
Style: Emoji,Segoe UI Emoji,160,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,4,5,80,80,0,1
Style: Brand,Montserrat Black,38,&H00FFFFFF,&H000000FF,&H00000000,&H88000000,1,0,0,0,100,100,0,0,1,2,2,9,30,30,30,1
Style: Label,Montserrat Black,52,&H00FFFFFF,&H000000FF,&H0000F0FF,&HBB000000,1,0,0,0,100,100,0,0,1,3,2,2,60,60,0,1
Style: CTA,Montserrat Black,116,&H00FFFFFF,&H000000FF,&H00000000,&HDD000000,1,0,0,0,100,100,2,0,1,12,5,5,70,70,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

# Mots qui forment une "unité" qu'on garde collée au nombre (1500 km², 95 %…)
_UNIT_WORDS = {"km", "km²", "km2", "m", "mètres", "metres", "%", "ans", "an",
               "kg", "tonnes", "habitants", "espèces", "especes", "millions",
               "milliers", "fois", "siècles", "siecles", "minutes", "heures"}
_NUMBER_RE = __import__("re").compile(r"\d")

# Mots-clés colorés en MAGENTA TIKTOK au lieu du jaune par défaut (noms propres,
# concepts forts, mots à impact narratif). Le match se fait en minuscules et
# SANS accents (voir _normalize_word) : « mystère » et « mystere » matchent
# tous les deux, inutile de doubler les entrées.
KEYWORD_COLORS = {
    # Noms propres
    "mayotte", "mahorais", "mahoraise", "mahoraises",
    # Faune/flore emblématique
    "tortue", "tortues", "baleine", "baleines", "dauphin", "dauphins",
    "lagon", "dugong", "baobab", "baobabs", "maki", "makis",
    "caméléon", "ylang", "vanille", "corail", "coraux", "manta",
    # Culture mahoraise
    "djinn", "djinns", "esprit", "esprits", "légende",
    "manzaraka", "debaa", "salouva", "kishali", "wadaha", "mawlid",
    # Émotions / mots à impact
    "secret", "secrets", "mystère", "mystères", "magique", "magie",
    "incroyable", "fou", "folle", "extraordinaire",
    "interdit", "interdite", "jamais", "personne", "unique",
}

# Mots-clés → emoji affiché en gros qui pop quand le mot est prononcé.
# Chaque emoji n'apparaît qu'UNE FOIS par vidéo (la 1ère occurrence) pour
# éviter le spam visuel.
KEYWORD_EMOJIS = {
    # Mer & vie aquatique
    "lagon": "🌊", "mer": "🌊", "océan": "🌊", "vague": "🌊", "vagues": "🌊",
    "tortue": "🐢", "tortues": "🐢",
    "baleine": "🐋", "baleines": "🐋",
    "dauphin": "🐬", "dauphins": "🐬",
    "corail": "🪸", "coraux": "🪸", "récif": "🪸",
    "dugong": "🦭",
    "poisson": "🐠", "poissons": "🐠",
    "plongée": "🤿", "plongeur": "🤿",
    # Faune terrestre
    "maki": "🐒", "makis": "🐒", "lémurien": "🐒",
    "caméléon": "🦎", "gecko": "🦎",
    "oiseau": "🐦", "oiseaux": "🐦", "drongo": "🐦",
    "crabe": "🦀", "crabes": "🦀",
    "papillon": "🦋",
    # Flore
    "baobab": "🌳", "baobabs": "🌳",
    "fleur": "🌺", "fleurs": "🌺", "vanille": "🌺", "ylang": "🌺",
    "forêt": "🌳", "arbre": "🌳", "arbres": "🌳",
    # Lieux / nature
    "île": "🏝️", "îles": "🏝️", "mayotte": "🏝️",
    "plage": "🏖️", "plages": "🏖️",
    "montagne": "⛰️", "volcan": "🌋",
    "cascade": "💦", "rivière": "💧",
    "soleil": "☀️", "lune": "🌙",
    "cyclone": "🌀", "pluie": "🌧️",
    # Culture & société
    "musique": "🎵", "danse": "💃", "chant": "🎤", "chants": "🎤",
    "mariage": "💍",
    "mosquée": "🕌", "prière": "🤲",
    "or": "💛",
    # Cuisine
    "feu": "🔥", "grillé": "🔥", "grillée": "🔥",
    "coco": "🥥", "noix": "🥥",
    "banane": "🍌", "bananes": "🍌",
    "piment": "🌶️", "épice": "🌶️", "épices": "🌶️",
    # Émotions / impact narratif
    "secret": "🤫", "secrets": "🤫",
    "mystère": "🔮", "mystères": "🔮",
    "magique": "✨", "magie": "✨",
    "incroyable": "🤯", "fou": "🤯", "folle": "🤯",
    "esprit": "👻", "esprits": "👻", "djinn": "👻", "djinns": "👻",
    "légende": "📜",
    "interdit": "⛔", "interdite": "⛔", "danger": "⚠️",
    "record": "🏆",
}


def _normalize_word(raw: str) -> str:
    """Normalise un mot pour la comparaison aux dictionnaires de mots-clés
    (minuscules + suppression des accents, de la ponctuation et des espaces)."""
    w = raw.lower().strip(" .,;:!?\"'()[]«»\t\n")
    # Décompose les lettres accentuées (NFD) puis retire les diacritiques
    # combinants : « mystère » et « mystere » donnent la même clé.
    w = unicodedata.normalize("NFD", w)
    return "".join(c for c in w if not unicodedata.combining(c))


# Les dictionnaires de mots-clés sont normalisés UNE fois au chargement du
# module : les variantes accentuées et non accentuées pointent ainsi vers la
# même clé, sans avoir à doubler les entrées à la main.
KEYWORD_COLORS = {_normalize_word(w) for w in KEYWORD_COLORS}
KEYWORD_EMOJIS = {_normalize_word(k): v for k, v in KEYWORD_EMOJIS.items()}

# Emojis « kinetic pop » désactivés : libass (0.17.4, celui du FFmpeg utilisé)
# ne rend PAS les emojis couleur — les tables COLR de Segoe UI Emoji sont
# ignorées et les emojis sortent en contours monochromes cassés (vérifié sur
# frames rendues, y compris avec seguiemj.ttf copiée dans le fontsdir).
# Mieux vaut pas d'emoji que des glyphes cassés. À réactiver si le pipeline
# passe à des overlays PNG ou à un libass avec rendu couleur.
EMOJIS_ENABLED = False

# Séparateur inter-mots du karaoké : 2 espaces (identiques sur les couches
# Base et Hilite pour un alignement parfait) — réserve la place du pop du mot
# actif (115%) pour qu'il ne morde jamais sur ses voisins.
_WORD_SEP = "  "

# Position : bas-centre (\an2 = l'ancre est le BAS du bloc de texte).
# Safe zone TikTok 2026 : les 25% du bas sont réservés (description, musique,
# nouveau bouton Playlist depuis janv. 2026). À 72%, le bas du texte est à
# 28% du bord bas, donc entièrement AU-DESSUS de la zone réservée.
POS_Y_RATIO = 0.72  # ancre à 72% de la hauteur (texte au-dessus des 28% du bas)


def _t(seconds: float) -> str:
    if seconds < 0:
        seconds = 0
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def _clean(word: str) -> str:
    return word.replace("\\", "\\\\").replace("{", "(").replace("}", ")")


def _group_words(words: list[dict], max_per_group: int = 5,
                 max_chars_per_group: int = 13) -> list[list[dict]]:
    """Groupe par 2-5 mots, borné en largeur d'écran.

    Coupe la suite quand un mot finit par une ponctuation forte, ou quand le
    groupe deviendrait trop large (max_chars_per_group ≈ 13 caractères à la
    taille 108 → ~140 px libres de chaque côté, zone safe UI droite TikTok).
    """
    groups: list[list[dict]] = []
    current: list[dict] = []
    current_len = 0
    for w in words:
        wlen = len(w["word"].strip())
        # Coupe AVANT d'ajouter si le groupe deviendrait trop large à l'écran
        if current and current_len + 1 + wlen > max_chars_per_group:
            groups.append(current)
            current, current_len = [], 0
        current.append(w)
        current_len += (1 if current_len else 0) + wlen
        ends_punct = w["word"].strip().endswith((".", "!", "?", ":", ";"))
        if len(current) >= max_per_group or ends_punct:
            groups.append(current)
            current, current_len = [], 0
    if current:
        groups.append(current)
    return groups


def _wrap_balanced(text: str, max_chars_per_line: int = 18) -> str:
    """Répartit le texte sur 1 ou 2 lignes équilibrées (séparateur ASS \\N)."""
    words = text.split()
    if len(words) <= 1 or len(text) <= max_chars_per_line:
        return text
    # Cherche le point de coupure qui équilibre le mieux les 2 lignes
    best_split, best_diff = 1, 10**9
    for k in range(1, len(words)):
        l1 = len(" ".join(words[:k]))
        l2 = len(" ".join(words[k:]))
        diff = abs(l1 - l2)
        if diff < best_diff:
            best_diff, best_split = diff, k
    return " ".join(words[:best_split]) + r"\N" + " ".join(words[best_split:])


def extract_punch_times(words: list[dict], start_after: float = 3.8,
                        min_gap: float = 2.5, limit: int = 10) -> list[float]:
    """Timestamps 'start' des mots FORTS, pour caler des punchs visuels.

    Un mot est FORT s'il est dans le dictionnaire de mots-clés (même
    normalisation NFD que le reste du module), s'il contient un chiffre
    (1500, 2011, 95%…), ou s'il est une unité collée à un nombre qui le
    précède immédiatement (km², %, ans…).

    - Exclut tout ce qui est avant `start_after` (la zone hook a déjà sa
      propre dynamique).
    - Garantit un écart >= `min_gap` entre deux punchs : dans une grappe
      serrée, seul le premier est conservé.
    - Plafonné à `limit` punchs, triés par ordre chronologique.
    - Robuste : liste vide ou mots sans timing exploitable -> [].
    """
    if not words or limit <= 0:
        return []
    candidates: list[float] = []
    prev_has_digit = False  # le mot PRÉCÉDENT contenait-il un chiffre ?
    for w in words:
        raw = str(w.get("word") or "").strip()
        has_digit = bool(_NUMBER_RE.search(raw))
        # Unité qui suit directement un nombre (« 1500 km² », « 95 % »)
        is_unit = prev_has_digit and raw.strip(".,;:!?").lower() in _UNIT_WORDS
        prev_has_digit = has_digit
        if not raw:
            continue
        strong = (has_digit or is_unit
                  or _normalize_word(raw) in KEYWORD_COLORS)
        if not strong:
            continue
        try:
            t = float(w.get("start"))
        except (TypeError, ValueError):
            continue  # mot sans timing exploitable : ignoré
        if t < start_after:
            continue
        candidates.append(t)
    candidates.sort()
    punches: list[float] = []
    for t in candidates:
        # Grappe serrée : on garde le premier, on saute les suivants
        if punches and t - punches[-1] < min_gap:
            continue
        punches.append(t)
        if len(punches) >= limit:
            break
    return punches


# Interligne du hook : fontsize 82 × ~1.22 (ascender 968 + descender 251
# pour 1000 UPM dans Montserrat Black) ≈ l'interligne naturel de libass,
# pour que les lignes en events séparés s'empilent comme l'ancien bloc \N.
_HOOK_LINE_H = 100


def _hook_lines(hook_text: str, width: int, height: int) -> list[str]:
    """Génère les lignes ASS du hook affiché ~0-3.6s en haut de l'écran.

    Texte sur 1-2 lignes équilibrées, taille modérée, effet « stop scroll »
    CINÉTIQUE : chaque ligne apparaît en cascade (~0.25s de décalage) avec
    un pop 80 → 100 % + fondu alpha rapide, puis un léger pulse synchronisé
    entre les lignes. Disparition inchangée (fondu 250 ms, fin à 3.6s).

    Un event ASS SÉPARÉ par ligne : les tags d'animation sont en tête
    d'event et s'appliquent à la ligne entière — jamais à une queue de
    ligne d'un autre event (le bug de chevauchement corrigé sur le karaoké
    ne peut pas se reproduire ici).
    """
    if not hook_text or not hook_text.strip():
        return []
    text = hook_text.strip().upper()
    text = text.replace("\\", "").replace("{", "(").replace("}", ")")
    # 16 caractères max par ligne à la taille 82 → ~140 px libres de chaque
    # côté (zone safe encoche/UI droite TikTok)
    text = _wrap_balanced(text, max_chars_per_line=16)
    line_texts = text.split(r"\N")
    pos_x = width // 2
    pos_y = int(height * 0.26)  # haut de l'écran, au-dessus des sous-titres

    hook_start, hook_end = 0.10, 3.60
    stagger = 0.25  # décalage d'apparition entre les lignes (cascade)

    events: list[str] = []
    n = len(line_texts)
    for i, line in enumerate(line_texts):
        # Empilement centré sur pos_y (même centre visuel que l'ancien bloc)
        y = pos_y + round((i - (n - 1) / 2) * _HOOK_LINE_H)
        line_start = min(hook_start + i * stagger, hook_end - 0.5)
        delay_ms = round((line_start - hook_start) * 1000)
        # Pulse léger à ~1.6s ABSOLUES : offsets recalés sur le départ décalé
        # de chaque ligne pour que toutes pulsent ENSEMBLE.
        p = 1500 - delay_ms
        pulse = (
            f"\\t({p},{p + 250},\\fscx104\\fscy104)"
            f"\\t({p + 250},{p + 500},\\fscx100\\fscy100)"
        ) if p > 400 else ""
        # État initial : invisible (alpha FF) et 80 %, puis pop + fondu
        # rapide via \t. \fad(0,250) ne gère QUE la sortie (multiplicateur
        # global libass, compatible avec l'animation \alpha d'entrée).
        fx = (
            f"{{\\an5\\pos({pos_x},{y})\\bord8\\shad4"
            f"\\alpha&HFF&\\fscx80\\fscy80"
            f"\\fad(0,250)"
            f"\\t(0,120,\\alpha&H00&)"
            f"\\t(0,180,\\fscx100\\fscy100)"
            f"{pulse}}}"
        )
        events.append(
            f"Dialogue: 2,{_t(line_start)},{_t(hook_end)},Hook,,0,0,0,,{fx}{line}"
        )
    return events


def _number_lines(words: list[dict], width: int, height: int) -> list[str]:
    """Affiche en GROS les nombres prononcés (1500 km², 95 %, 2011…).

    Le chiffre apparaît centré, légèrement au-dessus du milieu, avec un pop
    pendant qu'il est dit. Renforce l'impact des données factuelles.
    """
    lines: list[str] = []
    pos_x = width // 2
    pos_y = int(height * 0.42)

    for i, w in enumerate(words):
        raw = w["word"].strip()
        if not _NUMBER_RE.search(raw):
            continue
        # Colle l'unité qui suit si pertinent (km, %, ans…)
        display = raw
        end = w["end"]
        if i + 1 < len(words):
            nxt = words[i + 1]["word"].strip().strip(".,;:!?")
            if nxt.lower() in _UNIT_WORDS:
                display = f"{raw} {nxt}"
                end = words[i + 1]["end"]
        display = display.replace("\\", "").replace("{", "(").replace("}", ")")
        start = w["start"]
        dur_end = max(end, start + 1.2) + 0.3
        fx = (
            f"{{\\an5\\pos({pos_x},{pos_y})\\bord16\\shad8"
            f"\\fad(80,200)"
            f"\\t(0,140,\\fscx125\\fscy125)"
            f"\\t(140,260,\\fscx100\\fscy100)}}"
        )
        lines.append(
            f"Dialogue: 3,{_t(start)},{_t(dur_end)},Number,,0,0,0,,{fx}{display}"
        )
    return lines


def _label_lines(label: str, width: int, height: int) -> list[str]:
    """Étiquette « lower-third » avec le nom du sujet (style documentaire).

    Affichée de 4s à 9s, au-dessus de la zone des sous-titres karaoké, avec
    une entrée en fondu. Donne un cachet « reportage » et crédibilise le sujet.
    """
    if not label or not label.strip():
        return []
    text = label.strip().replace("\\", "").replace("{", "(").replace("}", ")")
    if len(text) > 44:
        text = text[:42].rstrip() + "…"
    # Pin rendu avec la police emoji couleur du système (Montserrat n'a pas
    # de glyphes emoji → contour monochrome cassé sinon)
    text = "{\\fnSegoe UI Emoji}📍{\\fnMontserrat Black} " + text
    pos_x = width // 2
    pos_y = int(height * 0.63)
    fx = f"{{\\an2\\pos({pos_x},{pos_y})\\fad(280,300)\\bord3\\shad2}}"
    return [f"Dialogue: 2,{_t(4.0)},{_t(9.0)},Label,,0,0,0,,{fx}{text}"]


def _emoji_lines(words: list[dict], width: int, height: int) -> list[str]:
    """Affiche en gros un emoji pop quand un mot-clé Mayotte est prononcé.

    Chaque emoji n'apparaît qu'UNE seule fois par vidéo (sa 1ère occurrence)
    pour rester impactant sans pollution visuelle. Position : centre vertical,
    au-dessus de la zone karaoké, en dessous du hook.

    Ne produit rien tant que EMOJIS_ENABLED est False (libass sans rendu
    couleur : les emojis sortiraient en contours monochromes cassés).
    """
    if not EMOJIS_ENABLED:
        return []
    lines: list[str] = []
    pos_x = width // 2
    pos_y = int(height * 0.50)
    already_shown: set[str] = set()

    for w in words:
        key = _normalize_word(w["word"])
        emoji = KEYWORD_EMOJIS.get(key)
        if not emoji or emoji in already_shown:
            continue
        already_shown.add(emoji)

        start = w["start"]
        # Fenêtre sans emoji réduite au cœur du hook (0-2.5s) pour ne pas
        # surcharger l'attention dès l'intro (audit : moins envahissant)
        if start < 2.5:
            continue
        end = start + 1.4

        # Pop-in spectaculaire : 130% → 100%, fade out long pour adoucir
        fx = (
            f"{{\\an5\\pos({pos_x},{pos_y})"
            f"\\fad(60,300)"
            f"\\t(0,140,\\fscx130\\fscy130)"
            f"\\t(140,280,\\fscx100\\fscy100)}}"
        )
        lines.append(
            f"Dialogue: 4,{_t(start)},{_t(end)},Emoji,,0,0,0,,{fx}{emoji}"
        )

    return lines


def _cta_lines(total_duration: float, width: int, height: int) -> list[str]:
    """Overlay « ABONNE-TOI 🔔 » sur les 4 dernières secondes."""
    if total_duration < 6:
        return []
    pos_x = width // 2
    pos_y = int(height * 0.40)
    start = max(0.0, total_duration - 4.0)
    fx = (
        f"{{\\an5\\pos({pos_x},{pos_y})\\bord12\\shad5"
        f"\\fad(200,150)"
        f"\\t(0,200,\\fscx115\\fscy115)"
        f"\\t(200,360,\\fscx100\\fscy100)"
        f"\\t(1600,1900,\\fscx108\\fscy108)"
        f"\\t(1900,2200,\\fscx100\\fscy100)}}"
    )
    # Cloche rendue avec la police emoji couleur du système (voir _label_lines)
    return [
        f"Dialogue: 3,{_t(start)},{_t(total_duration)},CTA,,0,0,0,,"
        f"{fx}ABONNE-TOI {{\\fnSegoe UI Emoji}}🔔"
    ]


def build_karaoke_ass(
    words: list[dict],
    ass_path: Path,
    width: int,
    height: int,
    hook_text: str = "",
    show_numbers: bool = True,
    cta: bool = True,
    topic_label: str = "",
) -> None:
    """Génère un .ass karaoké style TikTok premium.

    Pour chaque groupe de 1-5 mots (borné en largeur, voir _group_words) :
    - Une ligne 'Base' affiche tout le groupe en blanc (avec fade in/out 80ms)
    - Pour chaque mot, une ligne 'Hilite' jaune POP-IN pendant qu'il est dit
      (scale 115 → 100 sur 120ms, fade-out 100ms après)
    """
    lines = [ASS_HEADER.format(w=width, h=height)]
    pos_x = width // 2
    pos_y = int(height * POS_Y_RATIO)

    # Watermark de la chaîne (@mister_decouverte) en haut à droite,
    # visible toute la vidéo, semi-transparent pour ne pas distraire.
    # Ancré à 200 px du bord droit : zone safe encoche/UI droite TikTok.
    if words:
        total_dur = words[-1]["end"]
        wm_x = width - 200
        wm_y = 40
        lines.append(
            f"Dialogue: 0,{_t(0)},{_t(total_dur)},Brand,,0,0,0,,"
            f"{{\\an9\\pos({wm_x},{wm_y})\\alpha&H40&}}@mister_decouverte"
        )

    # Hook géant 0-3.6s (texte « stop scroll » en haut)
    lines.extend(_hook_lines(hook_text, width, height))

    # Étiquette lower-third (nom du sujet) ~4-9s, style reportage
    lines.extend(_label_lines(topic_label, width, height))

    # Chiffres animés géants (1500 km², 95 %…)
    if show_numbers and words:
        lines.extend(_number_lines(words, width, height))

    # Emojis pop sur les mots-clés Mayotte (1 occurrence par emoji max)
    if words:
        lines.extend(_emoji_lines(words, width, height))

    # CTA « Abonne-toi » sur les 4 dernières secondes
    if cta and words:
        total_dur = words[-1]["end"]
        lines.extend(_cta_lines(total_dur, width, height))

    groups = _group_words(words, max_per_group=5)

    for group in groups:
        if not group:
            continue
        g_start = group[0]["start"]
        g_end = group[-1]["end"] + 0.08
        full_text = _WORD_SEP.join(_clean(w["word"]) for w in group)

        # Ligne FOND : groupe entier en blanc + fade
        base_fx = f"{{\\fad(90,90)\\an2\\pos({pos_x},{pos_y})\\bord10\\shad4}}"
        lines.append(
            f"Dialogue: 0,{_t(g_start)},{_t(g_end)},Base,,0,0,0,,{base_fx}{full_text}"
        )

        # MOT ACTIF (jaune, pop-in)
        for i, w in enumerate(group):
            before = _WORD_SEP.join(_clean(group[j]["word"]) for j in range(i))
            current = _clean(w["word"])
            after = _WORD_SEP.join(_clean(group[j]["word"])
                                   for j in range(i + 1, len(group)))
            invis_before = f"{{\\alpha&HFF&}}{before}{{\\alpha&H00&}}" if before else ""
            # Pop-in (scale 115 → 100 sur 120ms), fade-out 100ms.
            # Bug audit (« sansfin ») : le \t s'appliquait à toute la fin de
            # la ligne → le centrage décalait le mot gonflé sur son voisin.
            # Correctif : pop réduit à 115% et \r juste après le mot actif
            # pour couper l'animation → le mot gonfle symétriquement dans
            # son emplacement, la marge des 2 espaces absorbe le débord.
            fx = (
                f"{{\\an2\\pos({pos_x},{pos_y})\\bord10\\shad4"
                f"\\t(0,120,\\fscx115\\fscy115)"
                f"\\t(120,220,\\fscx100\\fscy100)"
                f"\\fad(0,100)}}"
            )
            # \r réinitialise le style pour la queue de ligne (fin du \t) ;
            # on ré-applique l'alpha invisible, le séparateur reste à 100%
            invis_after = f"{{\\r\\alpha&HFF&}}{_WORD_SEP}{after}" if after else ""
            full = (invis_before + (_WORD_SEP if before else "") + fx + current
                    + invis_after)
            # Mots-clés Mayotte → style "Keyword" (rose TikTok)
            # Sinon → "Hilite" (jaune par défaut)
            style = "Keyword" if _normalize_word(w["word"]) in KEYWORD_COLORS else "Hilite"
            lines.append(
                f"Dialogue: 1,{_t(w['start'])},{_t(w['end'] + 0.05)},{style},,0,0,0,,{full}"
            )

    ass_path.write_text("\n".join(lines), encoding="utf-8")
