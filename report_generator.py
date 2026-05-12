"""
report_generator.py — Premium PDF Report Builder for DataMind AI
Professional A4 report: Cover · Executive Summary · Key Findings ·
Charts · Statistical Summary · Anomalies · Recommendations · Appendix
"""

import io
import copy
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd
import numpy as np

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate, Frame, HRFlowable, Image,
    NextPageTemplate, PageBreak, PageTemplate,
    Paragraph, Spacer, Table, TableStyle, KeepTogether,
)
from reportlab.lib.colors import HexColor, white, black
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ─────────────────────────────────────────────
# PALETTE  (matches the dark-premium web UI)
# ─────────────────────────────────────────────
INK        = HexColor("#0f0c29")        # cover background
NAVY       = HexColor("#0d1b3e")        # cover accent
PURPLE     = HexColor("#7c3aed")        # primary accent
PURPLE_MID = HexColor("#6d28d9")        # darker purple
PURPLE_LT  = HexColor("#ede9fe")        # light purple tint
BLUE       = HexColor("#3b82f6")        # secondary accent
BLUE_LT    = HexColor("#eff6ff")        # light blue tint
GREEN      = HexColor("#059669")        # recommendation / positive
GREEN_LT   = HexColor("#ecfdf5")        # light green tint
AMBER      = HexColor("#d97706")        # warning
AMBER_LT   = HexColor("#fffbeb")        # light amber tint
RED        = HexColor("#dc2626")        # danger
RED_LT     = HexColor("#fef2f2")        # light red tint
DARK       = HexColor("#1e293b")        # body text
MID        = HexColor("#475569")        # secondary text
LIGHT      = HexColor("#94a3b8")        # muted text
BORDER     = HexColor("#e2e8f0")        # hairline
PAGE_BG    = HexColor("#ffffff")        # page background
ROW_ALT    = HexColor("#f8fafc")        # alternating row


# ─────────────────────────────────────────────
# CHART → PNG HELPER
# ─────────────────────────────────────────────

def _fig_to_png(fig, width: int = 800, height: int = 380) -> Optional[io.BytesIO]:
    """Render Plotly figure → PNG bytes. Returns None on failure."""
    try:
        import plotly.io as pio
        f2 = copy.deepcopy(fig)
        f2.update_layout(
            paper_bgcolor="white",
            plot_bgcolor="#f8f9ff",
            font=dict(color="#1e293b", family="Arial"),
        )
        f2.update_xaxes(gridcolor="#f0f0f0", linecolor="#e2e8f0", zerolinecolor="#e2e8f0")
        f2.update_yaxes(gridcolor="#f0f0f0", linecolor="#e2e8f0", zerolinecolor="#e2e8f0")
        png = pio.to_image(f2, format="png", width=width, height=height, scale=2)
        return io.BytesIO(png)
    except Exception:
        return None


# ─────────────────────────────────────────────
# STYLES
# ─────────────────────────────────────────────

def _styles() -> dict:
    S: dict = {}

    # Cover
    S["cover_eyebrow"] = ParagraphStyle(
        "cover_eyebrow", fontName="Helvetica-Bold", fontSize=7.5,
        textColor=HexColor("#a78bfa"), alignment=TA_CENTER,
        letterSpacing=3, spaceAfter=6,
    )
    S["cover_title"] = ParagraphStyle(
        "cover_title", fontName="Helvetica-Bold", fontSize=32,
        textColor=white, leading=38, alignment=TA_CENTER, spaceAfter=6,
    )
    S["cover_subtitle"] = ParagraphStyle(
        "cover_subtitle", fontName="Helvetica", fontSize=12,
        textColor=HexColor("#94a3b8"), leading=18, alignment=TA_CENTER, spaceAfter=4,
    )
    S["cover_meta"] = ParagraphStyle(
        "cover_meta", fontName="Helvetica", fontSize=8.5,
        textColor=HexColor("#64748b"), alignment=TA_CENTER, spaceAfter=3,
    )

    # Section headers
    S["section_label"] = ParagraphStyle(
        "section_label", fontName="Helvetica-Bold", fontSize=7.5,
        textColor=PURPLE, letterSpacing=2.5, spaceAfter=2,
    )
    S["section_title"] = ParagraphStyle(
        "section_title", fontName="Helvetica-Bold", fontSize=18,
        textColor=DARK, leading=22, spaceAfter=2,
    )

    # Body text
    S["body"] = ParagraphStyle(
        "body", fontName="Helvetica", fontSize=9.5,
        textColor=HexColor("#374151"), leading=16, alignment=TA_JUSTIFY,
        spaceAfter=6,
    )
    S["body_small"] = ParagraphStyle(
        "body_small", fontName="Helvetica", fontSize=8.5,
        textColor=MID, leading=13, spaceAfter=4,
    )

    # Finding / Reco cards
    S["card_title"] = ParagraphStyle(
        "card_title", fontName="Helvetica-Bold", fontSize=10,
        textColor=DARK, leading=14, spaceAfter=3,
    )
    S["card_body"] = ParagraphStyle(
        "card_body", fontName="Helvetica", fontSize=9,
        textColor=HexColor("#4b5563"), leading=14, spaceAfter=0,
    )

    # Table
    S["th"] = ParagraphStyle(
        "th", fontName="Helvetica-Bold", fontSize=7.5, textColor=white, leading=10,
    )
    S["td"] = ParagraphStyle(
        "td", fontName="Helvetica", fontSize=8, textColor=DARK, leading=11,
    )
    S["td_muted"] = ParagraphStyle(
        "td_muted", fontName="Helvetica", fontSize=8, textColor=MID, leading=11,
    )

    # TOC
    S["toc_num"] = ParagraphStyle(
        "toc_num", fontName="Helvetica-Bold", fontSize=9,
        textColor=PURPLE, alignment=TA_CENTER,
    )
    S["toc_title"] = ParagraphStyle(
        "toc_title", fontName="Helvetica", fontSize=9.5, textColor=DARK,
    )

    # Caption
    S["caption"] = ParagraphStyle(
        "caption", fontName="Helvetica-Oblique", fontSize=7.5,
        textColor=LIGHT, leading=10, spaceAfter=4, alignment=TA_CENTER,
    )

    # KPI tile
    S["kpi_value"] = ParagraphStyle(
        "kpi_value", fontName="Helvetica-Bold", fontSize=18,
        textColor=DARK, alignment=TA_CENTER, leading=20,
    )
    S["kpi_label"] = ParagraphStyle(
        "kpi_label", fontName="Helvetica-Bold", fontSize=6.5,
        textColor=LIGHT, alignment=TA_CENTER, letterSpacing=1.2, leading=9,
    )

    return S


# ─────────────────────────────────────────────
# PAGE TEMPLATES
# ─────────────────────────────────────────────

def _cover_tpl(doc):
    frame = Frame(0, 0, A4[0], A4[1], leftPadding=0, rightPadding=0,
                  topPadding=0, bottomPadding=0, id="cf")
    return PageTemplate(id="Cover", frames=[frame])


def _body_tpl(doc, title: str):
    W, H = A4
    M = 20 * mm
    FH = 12 * mm   # footer height
    HH = 13 * mm   # header height

    def on_page(canvas, doc):
        canvas.saveState()
        # ── header ──
        canvas.setFillColor(DARK)
        canvas.rect(0, H - HH, W, HH, fill=1, stroke=0)
        # left rule line
        canvas.setFillColor(PURPLE)
        canvas.rect(0, H - HH, 4, HH, fill=1, stroke=0)
        # title
        canvas.setFont("Helvetica-Bold", 7.5)
        canvas.setFillColor(HexColor("#94a3b8"))
        canvas.drawString(M + 4, H - HH + 4.5 * mm, title.upper())
        # right — date
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(HexColor("#64748b"))
        canvas.drawRightString(W - M, H - HH + 4.5 * mm,
                               datetime.now().strftime("%d %B %Y"))

        # ── footer ──
        canvas.setStrokeColor(BORDER)
        canvas.setLineWidth(0.5)
        canvas.line(M, FH + 2 * mm, W - M, FH + 2 * mm)
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(LIGHT)
        canvas.drawString(M, FH - 2 * mm, "DataMind AI · Confidential")
        canvas.drawCentredString(W / 2, FH - 2 * mm, f"Page {doc.page}")
        canvas.drawRightString(W - M, FH - 2 * mm, "AI-Generated Report")
        canvas.restoreState()

    frame = Frame(M, FH + 4 * mm, W - 2 * M,
                  H - HH - FH - 6 * mm, id="body_frame")
    return PageTemplate(id="Body", frames=[frame], onPage=on_page)


# ─────────────────────────────────────────────
# HELPER FLOWABLES
# ─────────────────────────────────────────────

def _section_header(num: str, title: str, S: dict) -> list:
    label = f"0{num}" if len(num) == 1 else num
    return [
        Paragraph(f"{label}  ·  SECTION", S["section_label"]),
        Paragraph(title, S["section_title"]),
        HRFlowable(width="100%", thickness=1.5, color=PURPLE,
                   spaceAfter=10, spaceBefore=2),
    ]


def _card(title: str, body: str, S: dict,
          bar: HexColor = PURPLE, bg: HexColor = PURPLE_LT) -> Table:
    """Bordered card with coloured left bar, bold title, body text."""
    content = []
    if title:
        content.append(Paragraph(title, S["card_title"]))
        content.append(Spacer(1, 1.5 * mm))
    content.append(Paragraph(body, S["card_body"]))

    t = Table([[content]], colWidths=["100%"])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), bg),
        ("LEFTPADDING",   (0, 0), (-1, -1), 12),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 12),
        ("TOPPADDING",    (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ("LINEBEFORE",    (0, 0), (0, -1),  4, bar),
        ("LINEBELOW",     (0, 0), (-1, -1), 0.3, BORDER),
    ]))
    return t


def _kpi_tile(icon: str, value: str, label: str, S: dict) -> list:
    return [
        Paragraph(icon, ParagraphStyle("ki", fontSize=18, alignment=TA_CENTER)),
        Paragraph(value, S["kpi_value"]),
        Paragraph(label.upper(), S["kpi_label"]),
    ]


def _kpi_row(items: list, S: dict) -> Table:
    """Row of KPI tiles — items = [(icon, value, label), ...]"""
    cells = [_kpi_tile(ic, v, lb, S) for ic, v, lb in items]
    W = A4[0] - 40 * mm
    cw = [W / len(cells)] * len(cells)
    t = Table([cells], colWidths=cw)
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), ROW_ALT),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN",         (0, 0), (-1, -1), "CENTRE"),
        ("LINEABOVE",     (0, 0), (-1, 0),  2.5, PURPLE),
        ("LINEBELOW",     (0, 0), (-1, -1), 1, BORDER),
        ("LINEBEFORE",    (1, 0), (-1, -1), 0.5, BORDER),
        ("BOX",           (0, 0), (-1, -1), 0.5, BORDER),
    ]))
    return t


def _data_table(headers: list, rows: list, S: dict,
                col_widths=None, accent: HexColor = PURPLE) -> Table:
    """Styled data table — purple header, alternating rows."""
    hrow = [Paragraph(h, S["th"]) for h in headers]
    data = [hrow]
    for row in rows:
        data.append([Paragraph(str(c), S["td"]) for c in row])

    if col_widths is None:
        avail = A4[0] - 40 * mm
        col_widths = [avail / len(headers)] * len(headers)

    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        # Header
        ("BACKGROUND",    (0, 0), (-1, 0),  accent),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  white),
        ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, 0),  7.5),
        ("TOPPADDING",    (0, 0), (-1, 0),  6),
        ("BOTTOMPADDING", (0, 0), (-1, 0),  6),
        # Rows
        ("ALIGN",         (0, 0), (-1, -1), "LEFT"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 1), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 7),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 7),
        ("FONTNAME",      (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",      (0, 1), (-1, -1), 8),
        ("LINEBELOW",     (0, 0), (-1, 0),  1, HexColor("#5b21b6")),
        ("LINEBELOW",     (0, 1), (-1, -1), 0.25, BORDER),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [white, ROW_ALT]),
        ("BOX",           (0, 0), (-1, -1), 0.5, BORDER),
    ]))
    return t


def _chart_flowable(fig, caption: str, S: dict,
                    width_mm: float = 155, height_mm: float = 78) -> list:
    """Convert Plotly fig → Image flowable with caption. Falls back gracefully."""
    buf = _fig_to_png(fig, width=int(width_mm * 3.8), height=int(height_mm * 3.8))
    if buf is None:
        return [
            _card("", f"[Chart unavailable: {caption}. Install kaleido to embed charts.]",
                  S, bar=BORDER, bg=ROW_ALT),
            Spacer(1, 3 * mm),
        ]
    img = Image(buf, width=width_mm * mm, height=height_mm * mm)
    img.hAlign = "CENTRE"
    return [img, Paragraph(caption, S["caption"]), Spacer(1, 4 * mm)]


# ─────────────────────────────────────────────
# COVER PAGE
# ─────────────────────────────────────────────

def _build_cover(story: list, title: str, company: str, analyst: str,
                 filename: str, df: pd.DataFrame, tone: str,
                 industry: str, health_score: int, health_grade: str,
                 S: dict):
    W, H = A4

    # ── Full-page dark gradient block ──
    items_in_block = []
    items_in_block.append(Spacer(1, 22 * mm))

    # Eyebrow
    items_in_block.append(Paragraph("◈  DATAMIND AI  ·  POWERED BY GROQ LLAMA 3.3 · 70B", S["cover_eyebrow"]))
    items_in_block.append(Spacer(1, 8 * mm))

    # Title
    items_in_block.append(Paragraph(title, S["cover_title"]))
    items_in_block.append(Spacer(1, 3 * mm))
    items_in_block.append(Paragraph("AI-Generated Business Intelligence Report", S["cover_subtitle"]))
    items_in_block.append(Spacer(1, 6 * mm))

    # Divider line
    items_in_block.append(HRFlowable(
        width="55%", thickness=1, color=HexColor("#4c1d95"),
        spaceAfter=6, hAlign="CENTRE",
    ))

    # Meta
    items_in_block.append(Paragraph(
        f"Organisation: <b>{company}</b>   ·   Analyst: <b>{analyst}</b>   ·   Tone: <b>{tone}</b>",
        S["cover_meta"],
    ))
    items_in_block.append(Paragraph(
        f"Industry: <b>{industry}</b>   ·   Generated: <b>{datetime.now().strftime('%d %B %Y, %H:%M')}</b>",
        S["cover_meta"],
    ))
    items_in_block.append(Paragraph(
        f"Source file: {filename}",
        S["cover_meta"],
    ))
    items_in_block.append(Spacer(1, 10 * mm))

    # Health badge on cover
    health_colours = {
        "Excellent": "#16a34a", "Good": "#2563eb",
        "Fair": "#d97706", "Poor": "#dc2626",
    }
    hc = health_colours.get(health_grade, "#6d28d9")
    items_in_block.append(
        Table([[Paragraph(
            f'<font color="{hc}">◉</font>  Data Health: <b><font color="{hc}">{health_grade}</font></b> &nbsp; ({health_score}/100)',
            ParagraphStyle("hbadge", fontName="Helvetica-Bold", fontSize=9,
                           textColor=HexColor("#94a3b8"), alignment=TA_CENTER),
        )]], colWidths=[100 * mm])
    )
    items_in_block.append(Spacer(1, 10 * mm))

    cover_block = Table(
        [[item] for item in items_in_block],
        colWidths=[W],
    )
    cover_block.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), INK),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("ALIGN",         (0, 0), (-1, -1), "CENTRE"),
    ]))
    story.append(cover_block)

    # ── KPI tiles ──
    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
    cat_cols     = df.select_dtypes(include=["object", "category"]).columns.tolist()
    miss_pct     = round(df.isnull().sum().sum() / (df.shape[0] * df.shape[1]) * 100, 1)
    dup_count    = int(df.duplicated().sum())

    story.append(Spacer(1, 6 * mm))
    story.append(_kpi_row([
        ("◻", f"{df.shape[0]:,}",     "Total Rows"),
        ("◻", str(df.shape[1]),        "Columns"),
        ("◻", str(len(numeric_cols)),  "Numeric"),
        ("◻", str(len(cat_cols)),      "Categorical"),
        ("◻", f"{miss_pct}%",          "Missing"),
        ("◻", str(dup_count),          "Duplicates"),
    ], S))
    story.append(Spacer(1, 8 * mm))

    # ── Table of Contents ──
    toc_hdr = Table([[
        Paragraph("Table of Contents",
                  ParagraphStyle("tochdr", fontName="Helvetica-Bold", fontSize=12,
                                 textColor=DARK, spaceAfter=0)),
    ]], colWidths=[W - 40 * mm])
    toc_hdr.setStyle(TableStyle([
        ("LINEBELOW",     (0, 0), (-1, -1), 2, PURPLE),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(toc_hdr)
    story.append(Spacer(1, 3 * mm))

    sections = [
        ("01", "Executive Summary",        "Overview of dataset scope, patterns, and business implications"),
        ("02", "Key Findings",             "Five data-driven insights with specific metrics"),
        ("03", "Charts & Visualisations",  "Trend, distribution, correlation, and composition charts"),
        ("04", "Statistical Summary",      "Descriptive statistics and correlation analysis"),
        ("05", "Anomalies & Data Quality", "Outliers, missing data, skewness, and data health"),
        ("06", "Actionable Recommendations","Five strategic actions based on the analysis"),
        ("07", "Appendix — Column Profiles","Per-column numeric and categorical breakdowns"),
    ]
    toc_rows = [[
        Paragraph(num, S["toc_num"]),
        Paragraph(f"<b>{name}</b>", S["toc_title"]),
        Paragraph(desc, S["body_small"]),
    ] for num, name, desc in sections]

    toc_t = Table(toc_rows, colWidths=[12 * mm, 52 * mm, W - 40 * mm - 64 * mm])
    toc_t.setStyle(TableStyle([
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 4),
        ("LINEBELOW",     (0, 0), (-1, -1), 0.3, BORDER),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS",(0, 0), (-1, -1), [white, ROW_ALT]),
    ]))
    story.append(toc_t)


# ─────────────────────────────────────────────
# SECTION BUILDERS
# ─────────────────────────────────────────────

def _build_exec_summary(story: list, text: str, S: dict):
    story.extend(_section_header("1", "Executive Summary", S))
    paras = [p.strip() for p in text.split("\n") if p.strip()]
    for i, para in enumerate(paras):
        story.append(Paragraph(para, S["body"]))
        if i < len(paras) - 1:
            story.append(Spacer(1, 3 * mm))


def _build_key_findings(story: list, text: str, S: dict):
    story.extend(_section_header("2", "Key Findings", S))
    lines = [l.strip() for l in text.split("\n") if l.strip() and len(l.strip()) > 4]
    for line in lines:
        is_numbered = len(line) > 1 and line[0].isdigit()
        if is_numbered and ":" in line:
            parts = line.split(":", 1)
            t = parts[0].strip().lstrip("0123456789. ").strip("*").strip()
            b = parts[1].strip() if len(parts) > 1 else ""
            story.append(KeepTogether([
                _card(t, b, S, bar=PURPLE, bg=PURPLE_LT),
                Spacer(1, 3 * mm),
            ]))
        elif is_numbered:
            story.append(_card("", line, S, bar=PURPLE, bg=PURPLE_LT))
            story.append(Spacer(1, 3 * mm))
        else:
            story.append(_card("", line, S, bar=BORDER, bg=ROW_ALT))
            story.append(Spacer(1, 2 * mm))


def _build_charts_section(story: list, charts: list, forecast_fig, S: dict):
    story.extend(_section_header("3", "Charts & Visualisations", S))

    if not charts and forecast_fig is None:
        story.append(Paragraph("No charts were generated for this dataset.", S["body"]))
        return

    chart_meta = [
        ("Trend Over Time",          155, 78),
        ("Category Comparison",      155, 78),
        ("Correlation Matrix",       155, 88),
        ("Distribution (Violin)",    155, 88),
        ("Scatter Plot",             155, 78),
        ("Composition (Donut)",      155, 78),
        ("Top-N Ranking",            155, 78),
    ]

    # Pair charts that work side-by-side (two per row, ~74mm each)
    # Full-width: heatmap (idx 2), violin (idx 3)
    full_width_idx = {2, 3}
    i = 0
    while i < len(charts):
        if i in full_width_idx:
            label, _w, h = chart_meta[i] if i < len(chart_meta) else (f"Chart {i+1}", 155, 85)
            story.extend(_chart_flowable(charts[i], label, S, 155, h))
            i += 1
        elif i + 1 < len(charts) and (i + 1) not in full_width_idx:
            # Side-by-side pair
            la = chart_meta[i][0]   if i   < len(chart_meta) else f"Chart {i+1}"
            lb = chart_meta[i+1][0] if i+1 < len(chart_meta) else f"Chart {i+2}"
            pair_w = 74
            pair_h = 72
            buf_a = _fig_to_png(charts[i],   width=int(pair_w * 4), height=int(pair_h * 4))
            buf_b = _fig_to_png(charts[i+1], width=int(pair_w * 4), height=int(pair_h * 4))

            def _cell(buf, lbl, pw=pair_w, ph=pair_h, S=S):
                if buf is None:
                    return [Paragraph(f"[{lbl} unavailable]", S["caption"])]
                img = Image(buf, width=pw * mm, height=ph * mm)
                img.hAlign = "CENTRE"
                return [img, Paragraph(lbl, S["caption"])]

            pair = Table(
                [[_cell(buf_a, la), _cell(buf_b, lb)]],
                colWidths=[(pair_w + 3) * mm, (pair_w + 3) * mm],
            )
            pair.setStyle(TableStyle([
                ("VALIGN",       (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING",  (0, 0), (-1, -1), 2),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                ("LINEAFTER",    (0, 0), (0, -1),  0.3, BORDER),
            ]))
            story.append(pair)
            story.append(Spacer(1, 5 * mm))
            i += 2
        else:
            label, _w, h = chart_meta[i] if i < len(chart_meta) else (f"Chart {i+1}", 155, 78)
            story.extend(_chart_flowable(charts[i], label, S, 155, h))
            i += 1

    # Forecast chart — full width
    if forecast_fig is not None:
        story.append(Spacer(1, 3 * mm))
        story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER, spaceAfter=6))
        story.append(Paragraph("Trend Forecast (Linear Regression)", S["card_title"]))
        story.append(Spacer(1, 2 * mm))
        story.extend(_chart_flowable(forecast_fig, "Linear regression forecast with confidence band", S, 155, 85))


def _build_statistical_summary(story: list, df: pd.DataFrame,
                                stats_summary: dict, S: dict):
    story.extend(_section_header("4", "Statistical Summary", S))

    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
    if not numeric_cols:
        story.append(Paragraph("No numeric columns found.", S["body"]))
        return

    # Descriptive stats table (up to 6 cols)
    cols6 = numeric_cols[:6]
    desc  = df[cols6].describe().round(2)
    avail = A4[0] - 40 * mm
    cw    = [26 * mm] + [(avail - 26 * mm) / len(cols6)] * len(cols6)

    story.append(_data_table(
        ["Statistic"] + [str(c) for c in cols6],
        [[str(idx)] + [str(desc.loc[idx, c]) for c in cols6] for idx in desc.index],
        S, col_widths=cw,
    ))
    story.append(Spacer(1, 5 * mm))

    # If more than 6 columns, show the rest
    if len(numeric_cols) > 6:
        extra = numeric_cols[6:]
        desc2 = df[extra].describe().round(2)
        cw2   = [26 * mm] + [(avail - 26 * mm) / len(extra)] * len(extra)
        story.append(Paragraph("<b>Additional Numeric Columns</b>", S["card_title"]))
        story.append(Spacer(1, 2 * mm))
        story.append(_data_table(
            ["Statistic"] + [str(c) for c in extra],
            [[str(idx)] + [str(desc2.loc[idx, c]) for c in extra] for idx in desc2.index],
            S, col_widths=cw2,
        ))
        story.append(Spacer(1, 5 * mm))

    # Strong correlations
    corrs = stats_summary.get("strong_correlations", [])
    if corrs:
        story.append(Paragraph("<b>Notable Correlations</b>", S["card_title"]))
        story.append(Spacer(1, 2 * mm))
        cw_c = [avail * p for p in [0.28, 0.28, 0.22, 0.22]]
        story.append(_data_table(
            ["Column A", "Column B", "Pearson r", "Strength"],
            [[c["col1"], c["col2"], str(c["r"]), c["strength"]] for c in corrs[:10]],
            S, col_widths=cw_c, accent=BLUE,
        ))


def _build_anomalies(story: list, text: str, anomalies: dict, S: dict):
    story.extend(_section_header("5", "Anomalies & Data Quality", S))

    paras = [p.strip() for p in text.split("\n") if p.strip()]
    for para in paras:
        lo = para.lower()
        if any(w in lo for w in ["critical", "extreme", "major", "significant"]):
            bar, bg = RED, RED_LT
        elif any(w in lo for w in ["moderate", "warning", "missing", "outlier", "duplicate", "skew"]):
            bar, bg = AMBER, AMBER_LT
        else:
            bar, bg = GREEN, GREEN_LT
        story.append(_card("", para, S, bar=bar, bg=bg))
        story.append(Spacer(1, 3 * mm))

    # Outlier table
    outliers = anomalies.get("outliers", {})
    if outliers:
        story.append(Spacer(1, 3 * mm))
        story.append(Paragraph("<b>Outlier Summary — IQR Method</b>", S["card_title"]))
        story.append(Spacer(1, 2 * mm))
        avail = A4[0] - 40 * mm
        story.append(_data_table(
            ["Column", "Count", "Outlier %", "Lower Bound", "Upper Bound", "Data Max"],
            [[col, str(v["count"]), f"{v['pct']}%",
              str(v["lower_bound"]), str(v["upper_bound"]), str(v["extreme_max"])]
             for col, v in outliers.items()],
            S,
            col_widths=[avail * p for p in [0.22, 0.13, 0.13, 0.18, 0.18, 0.16]],
            accent=AMBER,
        ))

    # Other flags
    const      = anomalies.get("constant_columns", [])
    high_miss  = anomalies.get("high_missing", [])
    skewed     = anomalies.get("high_skewness", {})

    flags = []
    if const:
        flags.append(["Constant Columns", ", ".join(const)])
    if high_miss:
        flags.append(["High Missing (>20%)", ", ".join(high_miss)])
    for col, sk in skewed.items():
        flags.append([f"High Skewness — {col}", f"Skewness: {sk}"])

    if flags:
        story.append(Spacer(1, 4 * mm))
        story.append(Paragraph("<b>Additional Data Quality Flags</b>", S["card_title"]))
        story.append(Spacer(1, 2 * mm))
        avail = A4[0] - 40 * mm
        story.append(_data_table(
            ["Flag", "Detail"], flags, S,
            col_widths=[avail * 0.38, avail * 0.62],
            accent=RED,
        ))


def _build_recommendations(story: list, text: str, S: dict):
    story.extend(_section_header("6", "Actionable Recommendations", S))
    lines = [l.strip() for l in text.split("\n") if l.strip() and len(l.strip()) > 4]
    for line in lines:
        is_numbered = len(line) > 1 and line[0].isdigit()
        if is_numbered and ":" in line:
            parts = line.split(":", 1)
            t = parts[0].strip().lstrip("0123456789. ").strip("*").strip()
            b = parts[1].strip() if len(parts) > 1 else ""
            story.append(KeepTogether([
                _card(t, b, S, bar=GREEN, bg=GREEN_LT),
                Spacer(1, 3 * mm),
            ]))
        else:
            story.append(_card("", line, S, bar=GREEN, bg=GREEN_LT))
            story.append(Spacer(1, 3 * mm))


def _build_appendix(story: list, df: pd.DataFrame, stats_summary: dict, S: dict):
    story.extend(_section_header("7", "Appendix — Column Profiles", S))

    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
    cat_cols     = df.select_dtypes(include=["object", "category"]).columns.tolist()
    key_stats    = stats_summary.get("key_stats", {})
    cat_stats    = stats_summary.get("cat_stats", {})
    avail        = A4[0] - 40 * mm

    if numeric_cols and key_stats:
        story.append(Paragraph("<b>Numeric Column Profiles</b>", S["card_title"]))
        story.append(Spacer(1, 2 * mm))
        rows = []
        for col in numeric_cols:
            if col not in key_stats:
                continue
            st = key_stats[col]
            rows.append([
                col, str(st["mean"]), str(st["median"]), str(st["std"]),
                str(st["min"]), str(st["max"]), str(st["skew"]),
                f"{st['cv']}%" if "cv" in st else "—",
                f"{st['missing_pct']}%",
            ])
        cw = [avail * p for p in [0.17, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.10, 0.09]]
        story.append(_data_table(
            ["Column", "Mean", "Median", "Std Dev", "Min", "Max", "Skew", "CV%", "Missing%"],
            rows, S, col_widths=cw,
        ))
        story.append(Spacer(1, 6 * mm))

    if cat_cols and cat_stats:
        story.append(Paragraph("<b>Categorical Column Profiles</b>", S["card_title"]))
        story.append(Spacer(1, 2 * mm))
        rows = []
        for col in cat_cols:
            if col not in cat_stats:
                continue
            st = cat_stats[col]
            rows.append([
                col, str(st["unique"]), str(st["top"]),
                str(st["top_count"]), f"{st['top_pct']}%", f"{st['missing_pct']}%",
            ])
        cw = [avail * p for p in [0.22, 0.14, 0.28, 0.13, 0.11, 0.12]]
        story.append(_data_table(
            ["Column", "Unique", "Top Value", "Top Count", "Top %", "Missing%"],
            rows, S, col_widths=cw, accent=BLUE,
        ))


# ─────────────────────────────────────────────
# MAIN ENTRY POINT
# ─────────────────────────────────────────────

def generate_pdf_report(
    title: str,
    company: str,
    analyst: str,
    filename: str,
    df: pd.DataFrame,
    exec_summary: str,
    key_findings: str,
    anomaly_narrative: str,
    recommendations: str,
    stats_summary: dict,
    anomalies: dict,
    charts: list,
    forecast_fig=None,
    tone: str = "Professional",
    industry: str = "General",
    health_score: int = 0,
    health_grade: str = "Good",
) -> bytes:
    """
    Build and return the complete premium PDF as bytes.
    Charts are embedded if kaleido is installed; otherwise a placeholder is shown.
    """
    buf = io.BytesIO()
    S   = _styles()

    doc = BaseDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=title,
        author=analyst,
        subject=f"{company} — Business Intelligence Report",
        creator="DataMind AI",
        keywords="AI, analytics, business intelligence, data",
    )

    cover_tpl = _cover_tpl(doc)
    body_tpl  = _body_tpl(doc, title)
    doc.addPageTemplates([cover_tpl, body_tpl])

    story: list = []

    # ── Cover ──────────────────────────────────────
    story.append(NextPageTemplate("Cover"))
    _build_cover(
        story, title, company, analyst, filename, df,
        tone, industry, health_score, health_grade, S,
    )

    # ── Switch to body ──────────────────────────────
    story.append(NextPageTemplate("Body"))
    story.append(PageBreak())

    _build_exec_summary(story, exec_summary, S)
    story.append(PageBreak())

    _build_key_findings(story, key_findings, S)
    story.append(PageBreak())

    _build_charts_section(story, charts, forecast_fig, S)
    story.append(PageBreak())

    _build_statistical_summary(story, df, stats_summary, S)
    story.append(PageBreak())

    _build_anomalies(story, anomaly_narrative, anomalies, S)
    story.append(PageBreak())

    _build_recommendations(story, recommendations, S)
    story.append(PageBreak())

    _build_appendix(story, df, stats_summary, S)

    doc.build(story)
    buf.seek(0)
    return buf.read()
