"""Convertit un SRT en sous-titres ASS animés (style TikTok)."""
import re
from pathlib import Path

ASS_HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: {w}
PlayResY: {h}
ScaledBorderAndShadow: yes
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Montserrat,84,&H00FFFFFF,&H00FFFFFF,&H00000000,&H88000000,1,0,0,0,100,100,0,0,1,6,2,2,80,80,420,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def _srt_time_to_ass(t: str) -> str:
    h, m, rest = t.split(":")
    s, ms = rest.split(",")
    cs = int(ms) // 10
    return f"{int(h)}:{int(m):02d}:{int(s):02d}.{cs:02d}"


def srt_to_ass(srt_path: Path, ass_path: Path, width: int, height: int) -> None:
    text = srt_path.read_text(encoding="utf-8").strip()
    blocks = re.split(r"\n\s*\n", text)
    lines = [ASS_HEADER.format(w=width, h=height)]

    for block in blocks:
        rows = [r for r in block.splitlines() if r.strip()]
        if len(rows) < 2:
            continue
        time_row = rows[1] if "-->" in rows[1] else rows[0]
        if "-->" not in time_row:
            continue
        start_raw, end_raw = [t.strip() for t in time_row.split("-->")]
        content_rows = rows[2:] if "-->" in rows[1] else rows[1:]
        content = " ".join(content_rows).strip()
        if not content:
            continue
        content = content.replace("\\", "\\\\").replace("{", "(").replace("}", ")")
        start = _srt_time_to_ass(start_raw)
        end = _srt_time_to_ass(end_raw)
        effect = "{\\fad(120,80)\\t(0,180,\\fscx110\\fscy110)\\t(180,300,\\fscx100\\fscy100)}"
        lines.append(
            f"Dialogue: 0,{start},{end},Default,,0,0,0,,{effect}{content}"
        )

    ass_path.write_text("\n".join(lines), encoding="utf-8")
