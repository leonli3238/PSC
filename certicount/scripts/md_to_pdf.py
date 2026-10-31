"""Render a Markdown note of ``docs/`` to PDF (Chinese text, tables, code blocks).

Only the Markdown used in the notes is supported: ``#``/``##``/``###``
headings, paragraphs, ``-`` and ``1.`` lists, pipe tables (``\\|`` for a
literal bar inside a cell), fenced code blocks, ``**bold**`` and ``inline
code``.  reportlab cannot embed CFF fonts, so the needed glyphs of a Noto
Sans CJK collection are subset and converted to TrueType first.

    python3 scripts/md_to_pdf.py docs/OPENING_REPORT_FINAL_2026-10-18.md
    python3 scripts/md_to_pdf.py note.md --out note.pdf --font /path/NotoSansCJK-Regular.ttc
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import tempfile
from pathlib import Path
from xml.sax.saxutils import escape

from fontTools import subset
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTCollection, newTable
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, Preformatted, SimpleDocTemplate, Spacer, Table, TableStyle

DEFAULT_FONT = os.getenv("PSC_CJK_FONT", "/data/workspace/BAT_old/fonts/NotoSansCJK-Regular.ttc")
SANS_INDEX, MONO_INDEX = 2, 7  # Noto Sans CJK SC / Noto Sans Mono CJK SC in the collection
ACCENT_HEX = "#1f4e79"
ACCENT = colors.HexColor(ACCENT_HEX)


# ---------------------------------------------------------------------------
# Fonts
# ---------------------------------------------------------------------------


def _cff_to_truetype(font) -> None:
    """Replace the CFF outlines of ``font`` by quadratic ``glyf`` outlines (fontTools' otf2ttf recipe)."""
    order = font.getGlyphOrder()
    glyph_set = font.getGlyphSet()
    glyf = newTable("glyf")
    glyf.glyphOrder = order
    glyf.glyphs = {}
    for name in order:
        pen = TTGlyphPen(glyph_set)
        glyph_set[name].draw(Cu2QuPen(pen, 1.0, reverse_direction=True))
        glyf.glyphs[name] = pen.glyph()
    font["glyf"] = glyf
    font["loca"] = newTable("loca")
    for tag in ("CFF ", "VORG"):
        if tag in font:
            del font[tag]
    font["head"].glyphDataFormat = 0
    post = font["post"]
    post.formatType, post.extraNames, post.mapping, post.glyphOrder = 2.0, [], {}, order
    maxp = font["maxp"]
    maxp.tableVersion = 0x00010000
    for field in ("maxTwilightPoints", "maxStorage", "maxFunctionDefs", "maxInstructionDefs",
                  "maxStackElements", "maxSizeOfInstructions"):
        setattr(maxp, field, 0)
    maxp.maxZones = 1
    maxp.maxComponentElements = max(len(getattr(g, "components", []) or []) for g in glyf.glyphs.values())
    font.sfntVersion = "\000\001\000\000"


def build_font(ttc: str, index: int, chars: set[str], cache: Path) -> Path:
    codepoints = sorted({ord(c) for c in chars} | set(range(0x20, 0x7F)))
    key = hashlib.sha1(f"{ttc}|{index}|{codepoints}".encode()).hexdigest()[:12]
    out = cache / f"cjk_{index}_{key}.ttf"
    if out.exists():
        return out
    font = TTCollection(ttc).fonts[index]
    opts = subset.Options()
    opts.notdef_outline = True
    opts.hinting = False
    opts.desubroutinize = True
    opts.layout_features = []
    sub = subset.Subsetter(opts)
    sub.populate(unicodes=codepoints)
    sub.subset(font)
    _cff_to_truetype(font)
    cache.mkdir(parents=True, exist_ok=True)
    font.save(out)
    return out


def missing_glyphs(path: Path, chars: set[str]) -> list[str]:
    from fontTools.ttLib import TTFont as FTFont

    cmap = FTFont(path)["cmap"].getBestCmap()
    return sorted(c for c in chars if ord(c) not in cmap and not c.isspace())


# ---------------------------------------------------------------------------
# Markdown -> flowables
# ---------------------------------------------------------------------------


_PIPE = re.compile(r"(?<!\\)\|")


def inline(text: str) -> str:
    """Escape for reportlab markup; ``code`` and **bold**."""
    parts = re.split(r"(`[^`]+`)", text)
    out = []
    for part in parts:
        if part.startswith("`") and part.endswith("`") and len(part) > 1:
            out.append(f'<font name="Mono" color="#7a3e00">{escape(part[1:-1].replace(chr(92) + "|", "|"))}</font>')
        else:
            s = escape(part.replace("\\|", "|"))
            s = re.sub(r"\*\*(.+?)\*\*", rf'<font color="{ACCENT_HEX}"><b>\1</b></font>', s)
            out.append(s)
    return "".join(out)


def styles() -> dict[str, ParagraphStyle]:
    base = dict(fontName="Sans", wordWrap="CJK", textColor=colors.HexColor("#222222"))
    return {
        "title": ParagraphStyle("title", fontSize=20, leading=28, alignment=TA_CENTER, spaceAfter=4, textColor=ACCENT,
                                fontName="Sans", wordWrap="CJK"),
        "subtitle": ParagraphStyle("subtitle", fontSize=10, leading=14, alignment=TA_CENTER, spaceAfter=14,
                                   textColor=colors.HexColor("#666666"), fontName="Sans", wordWrap="CJK"),
        "h1": ParagraphStyle("h1", fontSize=15, leading=22, spaceBefore=14, spaceAfter=6, textColor=ACCENT, **{k: v for k, v in base.items() if k != "textColor"}),
        "h2": ParagraphStyle("h2", fontSize=12.5, leading=18, spaceBefore=10, spaceAfter=4, textColor=ACCENT, **{k: v for k, v in base.items() if k != "textColor"}),
        "body": ParagraphStyle("body", fontSize=10, leading=16, spaceAfter=5, **base),
        "bullet": ParagraphStyle("bullet", fontSize=10, leading=16, spaceAfter=2, leftIndent=14, bulletIndent=3, bulletFontName="Sans", **base),
        "cell": ParagraphStyle("cell", fontSize=8.6, leading=12.5, **base),
        "head": ParagraphStyle("head", fontSize=8.6, leading=12.5, fontName="Sans", wordWrap="CJK", textColor=colors.white),
        "code": ParagraphStyle("code", fontName="Mono", fontSize=8.2, leading=11.5, textColor=colors.HexColor("#1e1e1e")),
    }


def _table(rows: list[list[str]], st: dict, width: float) -> Table:
    ncol = max(len(r) for r in rows)
    rows = [r + [""] * (ncol - len(r)) for r in rows]
    weight = [max(min(len(r[i]), 60) for r in rows) + 4 for i in range(ncol)]
    total = sum(weight)
    widths = [max(width * w / total, 16 * mm if ncol > 2 else 30 * mm) for w in weight]
    scale = width / sum(widths)
    widths = [w * scale for w in widths]
    data = [[Paragraph(inline(c.strip()), st["head"] if i == 0 else st["cell"]) for c in r] for i, r in enumerate(rows)]
    t = Table(data, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f3f6fa")]),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#b8c4d4")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return t


def _code(lines: list[str], st: dict, width: float) -> Table:
    t = Table([[Preformatted("\n".join(lines), st["code"])]], colWidths=[width])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f5f5f0")),
        ("BOX", (0, 0), (-1, -1), 0.4, colors.HexColor("#d0d0c8")),
        ("LEFTPADDING", (0, 0), (-1, -1), 6), ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return t


def parse(md: str, st: dict, width: float) -> list:
    lines = md.splitlines()
    out: list = []
    para: list[str] = []
    i = 0

    def flush() -> None:
        if para:
            out.append(Paragraph(inline(" ".join(para)), st["body"]))
            para.clear()

    while i < len(lines):
        line = lines[i]
        s = line.strip()
        if s.startswith("```"):
            flush()
            block = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                block.append(lines[i])
                i += 1
            out += [_code(block, st, width), Spacer(1, 5)]
        elif s.startswith("|") and i + 1 < len(lines) and re.fullmatch(r"\|[\s:|-]+\|", lines[i + 1].strip()):
            flush()
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                if not re.fullmatch(r"\|[\s:|-]+\|", lines[i].strip()):
                    rows.append(_PIPE.split(lines[i].strip())[1:-1])
                i += 1
            out += [_table(rows, st, width), Spacer(1, 7)]
            continue
        elif s.startswith("### "):
            flush()
            out.append(Paragraph(inline(s[4:]), st["h2"]))
        elif s.startswith("## "):
            flush()
            out.append(Paragraph(inline(s[3:]), st["h1"]))
        elif s.startswith("# "):
            flush()
            out.append(Paragraph(inline(s[2:]), st["title"]))
            # the line right after the title is the subtitle
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines) and lines[j].strip() and not lines[j].lstrip().startswith(("#", "|", "-", "`")):
                out.append(Paragraph(inline(lines[j].strip()), st["subtitle"]))
                i = j
        elif re.match(r"^- ", s):
            flush()
            out.append(Paragraph(inline(s[2:]), st["bullet"], bulletText="•"))
        elif re.match(r"^\d+\. ", s):
            flush()
            num, rest = s.split(". ", 1)
            out.append(Paragraph(inline(rest), st["bullet"], bulletText=f"{num}."))
        elif not s:
            flush()
        else:
            para.append(s)
        i += 1
    flush()
    return out


def _footer(canvas, doc) -> None:
    canvas.saveState()
    canvas.setFont("Sans", 8)
    canvas.setFillColor(colors.HexColor("#888888"))
    canvas.drawCentredString(A4[0] / 2, 10 * mm, f"— {doc.page} —")
    canvas.restoreState()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("markdown")
    ap.add_argument("--out", default=None)
    ap.add_argument("--font", default=DEFAULT_FONT, help="Noto Sans CJK .ttc (Sans SC at index 2, Mono SC at 7)")
    ap.add_argument("--cache", default=str(Path(tempfile.gettempdir()) / "psc_pdf_fonts"))
    args = ap.parse_args()

    src = Path(args.markdown)
    md = src.read_text(encoding="utf-8")
    chars = set(md) | set("•—0123456789")
    cache = Path(args.cache)
    sans = build_font(args.font, SANS_INDEX, chars, cache)
    mono = build_font(args.font, MONO_INDEX, chars, cache)
    for path in (sans, mono):
        miss = missing_glyphs(path, chars)
        if miss:
            print(f"warning: {path.name} lacks {''.join(miss)!r}")
    pdfmetrics.registerFont(TTFont("Sans", str(sans)))
    pdfmetrics.registerFont(TTFont("Mono", str(mono)))
    pdfmetrics.registerFontFamily("Sans", normal="Sans", bold="Sans", italic="Sans", boldItalic="Sans")
    pdfmetrics.registerFontFamily("Mono", normal="Mono", bold="Mono", italic="Mono", boldItalic="Mono")

    out = Path(args.out) if args.out else src.with_suffix(".pdf")
    doc = SimpleDocTemplate(str(out), pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
                            topMargin=16 * mm, bottomMargin=18 * mm, title=src.stem, author="PSC")
    st = styles()
    doc.build(parse(md, st, doc.width), onFirstPage=_footer, onLaterPages=_footer)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
