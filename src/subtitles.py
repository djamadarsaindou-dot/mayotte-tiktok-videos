"""Sous-titres style TikTok karaoké : 1-3 mots à la fois, mot actif surligné."""
from pathlib import Path

ASS_HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: {w}
PlayResY: {h}
ScaledBorderAndShadow: yes
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Base,Montserrat Black,96,&H00FFFFFF,&H00FFFFFF,&H00000000,&H99000000,1,0,0,0,100,100,0,0,1,8,3,5,90,90,0,1
Style: Hilite,Montserrat Black,96,&H0000F0FF,&H0000F0FF,&H00000000,&H99000000,1,0,0,0,100,100,0,0,1,8,3,5,90,90,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


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
    """Groupe les mots par 2-3 pour l'affichage."""
    groups: list[list[dict]] = []
    current: list[dict] = []
    for w in words:
        current.append(w)
        if len(current) >= max_per_group or w["word"].strip().endswith((".", "!", "?", ":", ";")):
            groups.append(current)
            current = []
    if current:
        groups.append(current)
    return groups


def build_karaoke_ass(
    words: list[dict],
    ass_path: Path,
    width: int,
    height: int,
) -> None:
    """Génère un .ass karaoké TikTok avec mot actif surligné en jaune.

    Pour chaque groupe de mots :
    - Une ligne 'Base' qui affiche le groupe entier en blanc, fade-in léger
    - Une ligne 'Hilite' par mot actif, qui pop-in le mot pendant qu'il est dit
    """
    lines = [ASS_HEADER.format(w=width, h=height)]

    groups = _group_words(words, max_per_group=3)

    for group in groups:
        if not group:
            continue
        g_start = group[0]["start"]
        g_end = group[-1]["end"] + 0.05
        full_text = " ".join(_clean(w["word"]) for w in group)

        # Ligne fond : tout le groupe en blanc
        base_fx = "{\\fad(80,80)\\an2\\pos(540,1380)\\bord8\\shad3}"
        lines.append(
            f"Dialogue: 0,{_t(g_start)},{_t(g_end)},Base,,0,0,0,,{base_fx}{full_text}"
        )

        # Pour chaque mot, une overlay 'Hilite' jaune qui pop pendant qu'il est prononcé
        for i, w in enumerate(group):
            before = " ".join(_clean(group[j]["word"]) for j in range(i))
            current = _clean(w["word"])
            after = " ".join(_clean(group[j]["word"]) for j in range(i + 1, len(group)))
            # Texte invisible (alpha=FF) avant/après, surligné au milieu
            invis_before = f"{{\\alpha&HFF&}}{before}{{\\alpha&H00&}}" if before else ""
            invis_after = f"{{\\alpha&HFF&}}{after}{{\\alpha&H00&}}" if after else ""
            fx = (
                "{\\an2\\pos(540,1380)\\bord8\\shad3"
                "\\t(0,90,\\fscx125\\fscy125)"
                "\\t(90,180,\\fscx100\\fscy100)}"
            )
            full = (invis_before + (" " if before else "") + fx + current
                    + (" " if after else "") + invis_after)
            lines.append(
                f"Dialogue: 1,{_t(w['start'])},{_t(w['end'] + 0.02)},Hilite,,0,0,0,,{full}"
            )

    ass_path.write_text("\n".join(lines), encoding="utf-8")
