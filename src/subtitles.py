"""Sous-titres karaoké style TikTok haut de gamme.

Effets :
- Fond : 1 à 3 mots à la fois, blanc, contour noir épais, ombre douce
- Mot actif : surligné jaune avec un petit pop-in (scale 130 → 100)
- Apparition : fade-in 80ms en bas, fade-out 80ms (transitions douces)
- Position : ancrée bas-centre (~70% hauteur), grande taille, lisible mobile
- Police : Montserrat Black bundlée dans assets/fonts (chargée via fontsdir FFmpeg)
"""
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
Style: Keyword,Montserrat Black,108,&H005000FF,&H000000FF,&H00000000,&HAA000000,1,0,0,0,100,100,2,0,1,10,4,2,80,80,0,1
Style: Hook,Montserrat Black,82,&H0000F0FF,&H000000FF,&H00000000,&HCC000000,1,0,0,0,100,100,1,0,1,8,4,5,110,110,0,1
Style: Number,Montserrat Black,180,&H0000F0FF,&H000000FF,&H00000000,&H00000000,1,0,0,0,100,100,0,0,1,16,8,5,60,60,0,1
Style: Emoji,Arial,160,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,4,5,80,80,0,1
Style: Brand,Montserrat Black,38,&H00FFFFFF,&H000000FF,&H00000000,&H88000000,1,0,0,0,100,100,0,0,1,2,2,9,30,30,30,1
Style: CTA,Montserrat Black,116,&H00FFFFFF,&H000000FF,&H00000000,&HDD000000,1,0,0,0,100,100,2,0,1,12,5,5,70,70,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

# Mots qui forment une "unité" qu'on garde collée au nombre (1500 km², 95 %…)
_UNIT_WORDS = {"km", "km²", "km2", "m", "mètres", "metres", "%", "ans", "an",
               "kg", "tonnes", "habitants", "espèces", "especes", "millions",
               "milliers", "fois", "siècles", "siecles", "minutes", "heures"}
_NUMBER_RE = __import__("re").compile(r"\d")

# Mots-clés colorés en ROSE TIKTOK au lieu du jaune par défaut (noms propres,
# concepts forts, mots à impact narratif). Match en minuscules sans accents
# n'est pas fait — on stocke directement les variantes les plus courantes.
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
    (minuscules + suppression de la ponctuation et des espaces)."""
    return raw.lower().strip(" .,;:!?\"'()[]«»\t\n")

# Position : bas-centre, sur ~30% de la hauteur en bas
# (Alignement 2 = bas-centre ; MarginV = pixels au-dessus du bord bas)
POS_Y_RATIO = 0.72  # 72% de la hauteur (donc à 28% du bas)


def _t(seconds: float) -> str:
    if seconds < 0:
        seconds = 0
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def _clean(word: str) -> str:
    return word.replace("\\", "\\\\").replace("{", "(").replace("}", ")")


def _group_words(words: list[dict], max_per_group: int = 3) -> list[list[dict]]:
    """Groupe par 2-3 mots. Coupe la suite quand un mot finit par ponctuation forte."""
    groups: list[list[dict]] = []
    current: list[dict] = []
    for w in words:
        current.append(w)
        ends_punct = w["word"].strip().endswith((".", "!", "?", ":", ";"))
        if len(current) >= max_per_group or ends_punct:
            groups.append(current)
            current = []
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


def _hook_lines(hook_text: str, width: int, height: int) -> list[str]:
    """Génère les lignes ASS du hook affiché ~0-3.5s en haut de l'écran.

    Texte sur 1-2 lignes équilibrées, taille modérée, effet « stop scroll »
    (pop-in + léger pulse + fondu de sortie).
    """
    if not hook_text or not hook_text.strip():
        return []
    text = hook_text.strip().upper()
    text = text.replace("\\", "").replace("{", "(").replace("}", ")")
    text = _wrap_balanced(text, max_chars_per_line=18)
    pos_x = width // 2
    pos_y = int(height * 0.26)  # haut de l'écran, au-dessus des sous-titres

    # 0 → 3.6s : pop-in + pulse léger + fondu de sortie
    fx = (
        f"{{\\an5\\pos({pos_x},{pos_y})\\bord8\\shad4"
        f"\\fad(0,250)"
        f"\\t(0,180,\\fscx108\\fscy108)"
        f"\\t(180,320,\\fscx100\\fscy100)"
        f"\\t(1500,1750,\\fscx104\\fscy104)"
        f"\\t(1750,2000,\\fscx100\\fscy100)}}"
    )
    return [f"Dialogue: 2,{_t(0.10)},{_t(3.60)},Hook,,0,0,0,,{fx}{text}"]


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


def _emoji_lines(words: list[dict], width: int, height: int) -> list[str]:
    """Affiche en gros un emoji pop quand un mot-clé Mayotte est prononcé.

    Chaque emoji n'apparaît qu'UNE seule fois par vidéo (sa 1ère occurrence)
    pour rester impactant sans pollution visuelle. Position : centre vertical,
    au-dessus de la zone karaoké, en dessous du hook.
    """
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
        # On n'affiche pas les emojis pendant la zone du hook (0-3.6s) pour
        # ne pas surcharger l'attention dès l'intro
        if start < 3.7:
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
    return [
        f"Dialogue: 3,{_t(start)},{_t(total_duration)},CTA,,0,0,0,,{fx}ABONNE-TOI 🔔"
    ]


def build_karaoke_ass(
    words: list[dict],
    ass_path: Path,
    width: int,
    height: int,
    hook_text: str = "",
    show_numbers: bool = True,
    cta: bool = True,
) -> None:
    """Génère un .ass karaoké style TikTok premium.

    Pour chaque groupe de 1-3 mots :
    - Une ligne 'Base' affiche tout le groupe en blanc (avec fade in/out 80ms)
    - Pour chaque mot, une ligne 'Hilite' jaune POP-IN pendant qu'il est dit
      (scale 130 → 100 sur 120ms, fade-out 100ms après)
    """
    lines = [ASS_HEADER.format(w=width, h=height)]
    pos_x = width // 2
    pos_y = int(height * POS_Y_RATIO)

    # Watermark de la chaîne (@mister_decouverte) en haut à droite,
    # visible toute la vidéo, semi-transparent pour ne pas distraire.
    if words:
        total_dur = words[-1]["end"]
        lines.append(
            f"Dialogue: 0,{_t(0)},{_t(total_dur)},Brand,,0,0,0,,"
            f"{{\\alpha&H40&}}@mister_decouverte"
        )

    # Hook géant 0-3.6s (texte « stop scroll » en haut)
    lines.extend(_hook_lines(hook_text, width, height))

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

    groups = _group_words(words, max_per_group=3)

    for group in groups:
        if not group:
            continue
        g_start = group[0]["start"]
        g_end = group[-1]["end"] + 0.08
        full_text = " ".join(_clean(w["word"]) for w in group)

        # Ligne FOND : groupe entier en blanc + fade
        base_fx = f"{{\\fad(90,90)\\an2\\pos({pos_x},{pos_y})\\bord10\\shad4}}"
        lines.append(
            f"Dialogue: 0,{_t(g_start)},{_t(g_end)},Base,,0,0,0,,{base_fx}{full_text}"
        )

        # MOT ACTIF (jaune, pop-in)
        for i, w in enumerate(group):
            before = " ".join(_clean(group[j]["word"]) for j in range(i))
            current = _clean(w["word"])
            after = " ".join(_clean(group[j]["word"]) for j in range(i + 1, len(group)))
            invis_before = f"{{\\alpha&HFF&}}{before}{{\\alpha&H00&}}" if before else ""
            invis_after = f"{{\\alpha&HFF&}}{after}{{\\alpha&H00&}}" if after else ""
            # Pop-in (scale 130 → 100 sur 120ms), légère oscillation, fade-out 100ms
            fx = (
                f"{{\\an2\\pos({pos_x},{pos_y})\\bord10\\shad4"
                f"\\t(0,120,\\fscx130\\fscy130)"
                f"\\t(120,220,\\fscx100\\fscy100)"
                f"\\fad(0,100)}}"
            )
            full = (invis_before + (" " if before else "") + fx + current
                    + (" " if after else "") + invis_after)
            # Mots-clés Mayotte → style "Keyword" (rose TikTok)
            # Sinon → "Hilite" (jaune par défaut)
            style = "Keyword" if _normalize_word(w["word"]) in KEYWORD_COLORS else "Hilite"
            lines.append(
                f"Dialogue: 1,{_t(w['start'])},{_t(w['end'] + 0.05)},{style},,0,0,0,,{full}"
            )

    ass_path.write_text("\n".join(lines), encoding="utf-8")
