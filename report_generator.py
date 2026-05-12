"""
report_generator.py — PDF report builder for DataMind AI
Cover page + 6 sections: Executive Summary, Key Findings, Statistical Summary,
Anomalies & Data Quality, Actionable Recommendations, Appendix — Column Profiles
"""

import io
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd
import numpy as np

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    HRFlowable,
    Image,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.lib.colors import HexColor, white, black

# ─────────────────────────────────────────────
# PALETTE
# ─────────────────────────────────────────────
PURPLE       = HexColor("#667eea")
PURPLE_DARK  = HexColor("#764ba2")
PURPLE_LIGHT = HexColor("#f0f4ff")
GREEN        = HexColor("#10b981")
GREEN_LIGHT  = HexColor("#f0fdf4")
AMBER        = HexColor("#f59e0b")
AMBER_LIGHT  = HexColor("#fffbeb")
RED          = HexColor("#ef4444")
RED_LIGHT    = HexColor("#fef2f2")
BLUE         = HexColor("#3b82f6")
BLUE_LIGHT   = HexColor("#eff6ff")
DARK         = HexColor("#1a202c")
GREY         = HexColor("#6b7280")
LIGHT_GREY   = HexColor("#f9fafb")
BORDER       = HexColor("#e5e7eb")
PAGE_BG      = HexColor("#ffffff")


# ─────────────────────────────────────────────
# STYLES
# ─────────────────────────────────────────────

def _styles() -> dict:
    base = getSampleStyleSheet()
    S: dict = {}

    S["cover_title"] = ParagraphStyle(
        "cover_title", fontName="Helvetica-Bold", fontSize=28,
        textColor=white, leading=34, alignment=TA_CENTER, spaceAfter=8,
    )
    S["cover_sub"] = ParagraphStyle(
        "cover_sub", fontName="Helvetica", fontSize=11,
        textColor=HexColor("#d1d5db"), leading=16, alignment=TA_CENTER, spaceAfter=6,
    )
    S["cover_meta"] = ParagraphStyle(
        "cover_meta", fontName="Helvetica", fontSize=9,
        textColor=HexColor("#9ca3af"), alignment=TA_CENTER, spaceAfter=4,
    )
    S["section_num"] = ParagraphStyle(
        "section_num", fontName="Helvetica-Bold", fontSize=9,
        textColor=PURPLE, leading=12, spaceBefore=4,
    )
    S["section_title"] = ParagraphStyle(
        "section_title", fontName="Helvetica-Bold", fontSize=16,
        textColor=DARK, leading=20, spaceAfter=4,
    )
    S["body"] = ParagraphStyle(
        "body", fontName="Helvetica", fontSize=9.5,
        textColor=HexColor("#374151"), leading=15, alignment=TA_JUSTIFY,
        spaceAfter=8,
    )
    S["finding_title"] = ParagraphStyle(
        "finding_title", fontName="Helvetica-Bold", fontSize=10,
        textColor=DARK, leading=14, spaceAfter=3,
    )
    S["finding_body"] = ParagraphStyle(
        "finding_body", fontName="Helvetica", fontSize=9,
        textColor=HexColor("#4b5563"), leading=14, spaceAfter=2,
    )
    S["table_header"] = ParagraphStyle(
        "table_header", fontName="Helvetica-Bold", fontSize=8,
        textColor=white,
    )
    S["table_cell"] = ParagraphStyle(
        "table_cell", fontName="Helvetica", fontSize=8,
        textColor=DARK,
    )
    S["toc_section"] = ParagraphStyle(
        "toc_section", fontName="Helvetica-Bold", fontSize=10,
        textColor=DARK, leading=16, spaceAfter=2,
    )
    S["toc_num"] = ParagraphStyle(
        "toc_num", fontName="Helvetica-Bold", fontSize=10,
        textColor=PURPLE, leading=16,
    )
    S["caption"] = ParagraphStyle(
        "caption", fontName="Helvetica-Oblique", fontSize=8,
        textColor=GREY, leading=11, spaceAfter=6,
    )
    S["badge_text"] = ParagraphStyle(
        "badge_text", fontName="Helvetica-Bold", fontSize=8,
        textColor=white, alignment=TA_CENTER,
    )
    return S


# ─────────────────────────────────────────────
# PAGE TEMPLATES
# ─────────────────────────────────────────────

def _cover_template(doc):
    frame = Frame(0, 0, A4[0], A4[1], leftPadding=0, rightPadding=0,
                  topPadding=0, bottomPadding=0, id="cover_frame")
    return PageTemplate(id="Cover", frames=[frame])


def _body_template(doc, title: str):
    W, H = A4
    MARGIN = 18 * mm
    FOOTER_H = 14 * mm
    HEADER_H = 14 * mm

    def _header_footer(canvas, doc):
        canvas.saveState()
        # Header bar
        canvas.setFillColor(PURPLE)
        canvas.rect(0, H - HEADER_H, W, HEADER_H, fill=1, stroke=0)
        canvas.setFont("Helvetica-Bold", 8)
        canvas.setFillColor(white)
        canvas.drawString(MARGIN, H - HEADER_H + 4 * mm, title)
        canvas.setFont("Helvetica", 8)
        canvas.drawRightString(W - MARGIN, H - HEADER_H + 4 * mm,
                               f"Generated: {datetime.now().strftime('%d %b %Y')}")
        # Footer
        canvas.setStrokeColor(BORDER)
        canvas.setLineWidth(0.5)
        canvas.line(MARGIN, FOOTER_H, W - MARGIN, FOOTER_H)
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(GREY)
        canvas.drawCentredString(W / 2, FOOTER_H - 4 * mm, f"Page {doc.page}")
        canvas.restoreState()

    frame = Frame(MARGIN, FOOTER_H + 2 * mm, W - 2 * MARGIN,
                  H - HEADER_H - FOOTER_H - 4 * mm, id="body_frame")
    return PageTemplate(id="Body", frames=[frame], onPage=_header_footer)


# ─────────────────────────────────────────────
# HELPER FLOWABLES
# ─────────────────────────────────────────────

def _section_header(num: str, title: str, S: dict):
    return [
        Paragraph(f"0{num}." if len(num) == 1 else num, S["section_num"]),
        Paragraph(title, S["section_title"]),
        HRFlowable(width="100%", thickness=2, color=PURPLE, spaceAfter=12),
    ]


def _coloured_card(text: str, border_colour: HexColor, bg_colour: HexColor,
                   S: dict, title: str = "") -> Table:
    """A coloured card with optional bold title and body text."""
    content = []
    if title:
        content.append(Paragraph(f"<b>{title}</b>", S["finding_title"]))
    content.append(Paragraph(text, S["finding_body"]))

    t = Table([[content]], colWidths=["100%"])
    t.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), bg_colour),
        ("LEFTPADDING",  (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING",   (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 8),
        ("LINEBEFORE",   (0, 0), (0, -1),  4, border_colour),
    ]))
    return t


def _metric_row(items: list, S: dict) -> Table:
    """
    items = list of (icon, value, label) tuples
    Renders a row of KPI cards.
    """
    cells = []
    for icon, value, label in items:
        cell = [
            Paragraph(icon, ParagraphStyle("ic", fontSize=16, alignment=TA_CENTER)),
            Paragraph(f"<b>{value}</b>",
                      ParagraphStyle("mv", fontName="Helvetica-Bold", fontSize=14,
                                     alignment=TA_CENTER, textColor=DARK)),
            Paragraph(label.upper(),
                      ParagraphStyle("ml", fontName="Helvetica", fontSize=7,
                                     alignment=TA_CENTER, textColor=GREY,
                                     letterSpacing=0.8)),
        ]
        cells.append(cell)

    col_w = (A4[0] - 36 * mm) / len(cells)
    t = Table([cells], colWidths=[col_w] * len(cells))
    t.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), LIGHT_GREY),
        ("LINEABOVE",    (0, 0), (-1, 0),  2, PURPLE),
        ("LINEBEFORE",   (1, 0), (-1, -1), 0.5, BORDER),
        ("TOPPADDING",   (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 8),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN",        (0, 0), (-1, -1), "CENTRE"),
        ("ROUNDEDCORNERS", [6]),
    ]))
    return t


def _styled_table(headers: list, rows: list, S: dict,
                  col_widths=None) -> Table:
    """Styled data table with purple header row."""
    header_row = [Paragraph(h, S["table_header"]) for h in headers]
    data = [header_row]
    for i, row in enumerate(rows):
        bg = LIGHT_GREY if i % 2 == 0 else white
        data.append([Paragraph(str(c), S["table_cell"]) for c in row])

    if col_widths is None:
        avail = A4[0] - 36 * mm
        col_widths = [avail / len(headers)] * len(headers)

    t = Table(data, colWidths=col_widths, repeatRows=1)
    style = [
        ("BACKGROUND",   (0, 0), (-1, 0),  PURPLE),
        ("TEXTCOLOR",    (0, 0), (-1, 0),  white),
        ("FONTNAME",     (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",     (0, 0), (-1, 0),  8),
        ("ALIGN",        (0, 0), (-1, -1), "LEFT"),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",   (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW",    (0, 0), (-1, 0),  1, PURPLE_DARK),
        ("LINEBELOW",    (0, 1), (-1, -1), 0.3, BORDER),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [LIGHT_GREY, white]),
    ]
    t.setStyle(TableStyle(style))
    return t


# ─────────────────────────────────────────────
# COVER PAGE BUILDER
# ─────────────────────────────────────────────

def _build_cover(story: list, title: str, company: str, analyst: str,
                 filename: str, df: pd.DataFrame, tone: str, S: dict):
    from reportlab.platypus import KeepInFrame

    W, H = A4

    class CoverBackground:
        def __init__(self):
            self.width = W
            self.height = H

        def wrap(self, aw, ah):
            return self.width, self.height

        def draw(self):
            pass

    # We'll use a Table as the cover page layout
    cover_items = []

    # Gradient-ish top block using a Table
    cover_items.append(Spacer(1, 25 * mm))

    # Badge
    badge_t = Table([[Paragraph("✦  POWERED BY AI ANALYTICS", ParagraphStyle(
        "badge", fontName="Helvetica-Bold", fontSize=8, textColor=HexColor("#a5b4fc"),
        alignment=TA_CENTER, letterSpacing=2,
    ))]], colWidths=[80 * mm])
    badge_t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), HexColor("#1e1b4b")),
        ("ROUNDEDCORNERS",[999]),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("ALIGN",         (0, 0), (-1, -1), "CENTRE"),
    ]))

    # Title block (dark gradient simulation)
    title_block_data = [
        [Spacer(1, 8 * mm)],
        [badge_t],
        [Spacer(1, 6 * mm)],
        [Paragraph(title, S["cover_title"])],
        [Spacer(1, 4 * mm)],
        [Paragraph("AI-Generated Business Intelligence Report", S["cover_sub"])],
        [Spacer(1, 3 * mm)],
        [Paragraph(f"Organisation: <b>{company}</b>  ·  Analyst: <b>{analyst}</b>  ·  Tone: <b>{tone}</b>",
                   S["cover_meta"])],
        [Paragraph(f"Source: {filename}  ·  Generated: {datetime.now().strftime('%d %b %Y, %H:%M')}",
                   S["cover_meta"])],
        [Spacer(1, 8 * mm)],
    ]
    title_block = Table(title_block_data, colWidths=[W])
    title_block.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), HexColor("#0f0c29")),
        ("ALIGN",         (0, 0), (-1, -1), "CENTRE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
    ]))

    story.append(title_block)
    story.append(Spacer(1, 8 * mm))

    # KPI tiles
    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    missing_pct = round(df.isnull().sum().sum() / (df.shape[0] * df.shape[1]) * 100, 1)
    dup_count = int(df.duplicated().sum())

    kpi_items = [
        ("📦", f"{df.shape[0]:,}", "Total Rows"),
        ("📐", str(df.shape[1]), "Columns"),
        ("🔢", str(len(numeric_cols)), "Numeric"),
        ("🏷️", str(len(cat_cols)), "Categories"),
        ("✅" if missing_pct == 0 else "⚠️", f"{missing_pct}%", "Missing"),
        ("🔁", str(dup_count), "Duplicates"),
    ]
    story.append(_metric_row(kpi_items, S))
    story.append(Spacer(1, 8 * mm))

    # Table of Contents
    toc_data = [
        [Paragraph("Table of Contents", ParagraphStyle(
            "toc_hdr", fontName="Helvetica-Bold", fontSize=13,
            textColor=DARK, spaceAfter=8,
        ))],
    ]
    toc_table = Table(toc_data, colWidths=[W - 36 * mm])
    toc_table.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, -1), 1.5, PURPLE),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(toc_table)
    story.append(Spacer(1, 4 * mm))

    sections = [
        ("01", "Executive Summary"),
        ("02", "Key Findings"),
        ("03", "Statistical Summary"),
        ("04", "Anomalies & Data Quality"),
        ("05", "Actionable Recommendations"),
        ("06", "Appendix — Column Profiles"),
    ]
    toc_rows = [[
        Paragraph(num, ParagraphStyle("tn", fontName="Helvetica-Bold", fontSize=10,
                                       textColor=PURPLE, alignment=TA_CENTER)),
        Paragraph(name, ParagraphStyle("tt", fontName="Helvetica", fontSize=10,
                                        textColor=DARK)),
    ] for num, name in sections]

    toc = Table(toc_rows, colWidths=[12 * mm, W - 36 * mm - 12 * mm])
    toc.setStyle(TableStyle([
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LINEBELOW",     (0, 0), (-1, -1), 0.3, BORDER),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(toc)


# ─────────────────────────────────────────────
# SECTION BUILDERS
# ─────────────────────────────────────────────

def _build_exec_summary(story: list, text: str, S: dict):
    story.extend(_section_header("1", "Executive Summary", S))
    for para in text.split("\n"):
        para = para.strip()
        if para:
            story.append(Paragraph(para, S["body"]))
            story.append(Spacer(1, 3 * mm))


def _build_key_findings(story: list, text: str, S: dict):
    story.extend(_section_header("2", "Key Findings", S))
    lines = [l.strip() for l in text.split("\n") if l.strip() and len(l.strip()) > 4]
    for line in lines:
        # detect numbered lines
        is_numbered = len(line) > 1 and line[0].isdigit()
        if is_numbered:
            # Split on first colon if present
            if ":" in line:
                parts = line.split(":", 1)
                title_part = parts[0].strip().lstrip("0123456789. ").strip("*").strip()
                body_part = parts[1].strip() if len(parts) > 1 else ""
            else:
                title_part = ""
                body_part = line
            card = _coloured_card(
                body_part, PURPLE, PURPLE_LIGHT, S, title=title_part
            )
        else:
            card = _coloured_card(line, BORDER, LIGHT_GREY, S)
        story.append(card)
        story.append(Spacer(1, 3 * mm))


def _build_statistical_summary(story: list, df: pd.DataFrame,
                                stats_summary: dict, S: dict):
    story.extend(_section_header("3", "Statistical Summary", S))
    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
    if not numeric_cols:
        story.append(Paragraph("No numeric columns found.", S["body"]))
        return

    desc = df[numeric_cols].describe().round(2)
    headers = ["Statistic"] + [str(c) for c in numeric_cols[:6]]
    rows = []
    for idx in desc.index:
        row = [str(idx)]
        for col in numeric_cols[:6]:
            row.append(str(desc.loc[idx, col]))
        rows.append(row)

    avail = A4[0] - 36 * mm
    col_w = [28 * mm] + [(avail - 28 * mm) / min(len(numeric_cols), 6)] * min(len(numeric_cols), 6)
    story.append(_styled_table(headers, rows, S, col_widths=col_w))
    story.append(Spacer(1, 5 * mm))

    # Strong correlations
    corrs = stats_summary.get("strong_correlations", [])
    if corrs:
        story.append(Paragraph("<b>Strong Correlations</b>", S["finding_title"]))
        story.append(Spacer(1, 2 * mm))
        corr_rows = [[c["col1"], c["col2"], str(c["r"]), c["strength"]] for c in corrs[:8]]
        story.append(_styled_table(["Column A", "Column B", "Pearson r", "Strength"],
                                   corr_rows, S))


def _build_anomalies(story: list, text: str, anomalies: dict, S: dict):
    story.extend(_section_header("4", "Anomalies & Data Quality", S))
    paras = [p.strip() for p in text.split("\n") if p.strip()]
    for para in paras:
        # choose colour based on keywords
        if any(w in para.lower() for w in ["critical", "extreme", "major", "significant"]):
            c = _coloured_card(para, RED, RED_LIGHT, S)
        elif any(w in para.lower() for w in ["moderate", "warning", "missing", "outlier", "duplicate"]):
            c = _coloured_card(para, AMBER, AMBER_LIGHT, S)
        else:
            c = _coloured_card(para, GREEN, GREEN_LIGHT, S)
        story.append(c)
        story.append(Spacer(1, 3 * mm))

    # Outlier table
    outliers = anomalies.get("outliers", {})
    if outliers:
        story.append(Spacer(1, 4 * mm))
        story.append(Paragraph("<b>Outlier Summary (IQR Method)</b>", S["finding_title"]))
        story.append(Spacer(1, 2 * mm))
        headers = ["Column", "Outlier Count", "Outlier %", "Lower Bound", "Upper Bound"]
        rows = [[col, str(v["count"]), f"{v['pct']}%",
                 str(v["lower_bound"]), str(v["upper_bound"])]
                for col, v in outliers.items()]
        avail = A4[0] - 36 * mm
        story.append(_styled_table(headers, rows, S,
                                   col_widths=[avail * p for p in [0.22, 0.18, 0.15, 0.22, 0.23]]))


def _build_recommendations(story: list, text: str, S: dict):
    story.extend(_section_header("5", "Actionable Recommendations", S))
    lines = [l.strip() for l in text.split("\n") if l.strip() and len(l.strip()) > 4]
    for line in lines:
        is_numbered = len(line) > 1 and line[0].isdigit()
        if is_numbered and ":" in line:
            parts = line.split(":", 1)
            title_part = parts[0].strip().lstrip("0123456789. ").strip("*").strip()
            body_part = parts[1].strip()
        else:
            title_part = ""
            body_part = line
        card = _coloured_card(body_part, GREEN, GREEN_LIGHT, S, title=title_part)
        story.append(card)
        story.append(Spacer(1, 3 * mm))


def _build_appendix(story: list, df: pd.DataFrame, stats_summary: dict, S: dict):
    story.extend(_section_header("6", "Appendix — Column Profiles", S))
    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    key_stats = stats_summary.get("key_stats", {})
    cat_stats = stats_summary.get("cat_stats", {})

    if numeric_cols and key_stats:
        story.append(Paragraph("<b>Numeric Column Profiles</b>", S["finding_title"]))
        story.append(Spacer(1, 2 * mm))
        headers = ["Column", "Mean", "Median", "Std Dev", "Min", "Max", "Skew", "Missing %"]
        rows = []
        for col in numeric_cols:
            if col not in key_stats:
                continue
            st = key_stats[col]
            rows.append([col, str(st["mean"]), str(st["median"]), str(st["std"]),
                         str(st["min"]), str(st["max"]), str(st["skew"]),
                         f"{st['missing_pct']}%"])
        avail = A4[0] - 36 * mm
        cw = [avail * p for p in [0.18, 0.10, 0.10, 0.10, 0.10, 0.10, 0.10, 0.12]]
        story.append(_styled_table(headers, rows, S, col_widths=cw))
        story.append(Spacer(1, 5 * mm))

    if cat_cols and cat_stats:
        story.append(Paragraph("<b>Categorical Column Profiles</b>", S["finding_title"]))
        story.append(Spacer(1, 2 * mm))
        headers = ["Column", "Unique Values", "Top Value", "Top Count", "Top %", "Missing %"]
        rows = []
        for col in cat_cols:
            if col not in cat_stats:
                continue
            st = cat_stats[col]
            rows.append([col, str(st["unique"]), str(st["top"]),
                         str(st["top_count"]), f"{st['top_pct']}%",
                         f"{st['missing_pct']}%"])
        avail = A4[0] - 36 * mm
        cw = [avail * p for p in [0.22, 0.16, 0.22, 0.14, 0.12, 0.14]]
        story.append(_styled_table(headers, rows, S, col_widths=cw))


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
    tone: str = "Professional",
) -> bytes:
    """
    Build and return the complete PDF as bytes.
    """
    buf = io.BytesIO()
    S = _styles()

    doc = BaseDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=title,
        author=analyst,
        subject=f"{company} Business Intelligence Report",
        creator="DataMind AI",
    )

    cover_tpl = _cover_template(doc)
    body_tpl  = _body_template(doc, title)
    doc.addPageTemplates([cover_tpl, body_tpl])

    story: list = []

    # ── COVER ──────────────────────────────────
    story.append(NextPageTemplate("Cover"))
    _build_cover(story, title, company, analyst, filename, df, tone, S)

    # ── BODY ───────────────────────────────────
    story.append(NextPageTemplate("Body"))
    story.append(PageBreak())

    # Section 1: Executive Summary
    _build_exec_summary(story, exec_summary, S)
    story.append(PageBreak())

    # Section 2: Key Findings
    _build_key_findings(story, key_findings, S)
    story.append(PageBreak())

    # Section 3: Statistical Summary
    _build_statistical_summary(story, df, stats_summary, S)
    story.append(PageBreak())

    # Section 4: Anomalies
    _build_anomalies(story, anomaly_narrative, anomalies, S)
    story.append(PageBreak())

    # Section 5: Recommendations
    _build_recommendations(story, recommendations, S)
    story.append(PageBreak())

    # Section 6: Appendix
    _build_appendix(story, df, stats_summary, S)

    # Build
    doc.build(story)
    buf.seek(0)
    return buf.read()
