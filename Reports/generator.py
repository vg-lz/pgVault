# reports/generator.py
# Genera reportes ejecutivo y técnico en PDF usando reportlab.

from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable
)
from reportlab.graphics.shapes import Drawing, Circle, String
from reportlab.graphics import renderPDF
try:
    from .scoring import calculate_score
    from .regulations_map import enrich_regulation_refs, format_regulations_inline
except ImportError:  # pragma: no cover - keeps direct script execution working.
    from scoring import calculate_score
    from regulations_map import enrich_regulation_refs, format_regulations_inline

# ── Rutas ────────────────────────────────────────────────────────────────────
OUTPUT_DIR = Path(__file__).parent.parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# ── Paleta de colores PgVault ─────────────────────────────────────────────────
DARK_BG      = colors.HexColor("#0f0f23")
PURPLE       = colors.HexColor("#6366f1")
RED          = colors.HexColor("#ef4444")
ORANGE       = colors.HexColor("#f97316")
YELLOW       = colors.HexColor("#f59e0b")
GREEN        = colors.HexColor("#22c55e")
GRAY_LIGHT   = colors.HexColor("#f9f9f9")
GRAY_BORDER  = colors.HexColor("#e5e7eb")
TEXT_DARK    = colors.HexColor("#1a1a2e")
TEXT_MUTED   = colors.HexColor("#6b7280")
WHITE        = colors.white

SEVERITY_COLOR = {
    "critical": RED,
    "high":     ORANGE,
    "medium":   YELLOW,
    "low":      GREEN,
}
SEVERITY_LABEL = {
    "critical": "CRÍTICO",
    "high":     "ALTO",
    "medium":   "MEDIO",
    "low":      "BAJO",
}


def _severity_key(finding: dict) -> str:
    return str(finding.get("severity", "low")).lower()

# ── Estilos de texto ──────────────────────────────────────────────────────────
def _build_styles():
    base = getSampleStyleSheet()
    styles = {}

    styles["title"] = ParagraphStyle(
        "title",
        parent=base["Title"],
        fontSize=26, fontName="Helvetica-Bold",
        textColor=WHITE, spaceAfter=6,
    )
    styles["subtitle"] = ParagraphStyle(
        "subtitle",
        parent=base["Normal"],
        fontSize=12, fontName="Helvetica",
        textColor=colors.HexColor("#aaaaaa"), spaceAfter=4,
    )
    styles["h2"] = ParagraphStyle(
        "h2",
        parent=base["Heading2"],
        fontSize=14, fontName="Helvetica-Bold",
        textColor=TEXT_DARK, spaceBefore=16, spaceAfter=10,
        borderPad=4,
    )
    styles["body"] = ParagraphStyle(
        "body",
        parent=base["Normal"],
        fontSize=10, fontName="Helvetica",
        textColor=TEXT_DARK, spaceAfter=4, leading=15,
    )
    styles["body_muted"] = ParagraphStyle(
        "body_muted",
        parent=base["Normal"],
        fontSize=9, fontName="Helvetica",
        textColor=TEXT_MUTED, spaceAfter=3,
    )
    styles["code"] = ParagraphStyle(
        "code",
        parent=base["Code"],
        fontSize=8, fontName="Courier",
        textColor=colors.HexColor("#334155"),
        backColor=colors.HexColor("#f1f5f9"),
        borderPad=6, spaceAfter=4, leading=13,
    )
    styles["reg_tag"] = ParagraphStyle(
        "reg_tag",
        parent=base["Normal"],
        fontSize=8, fontName="Helvetica-Bold",
        textColor=PURPLE, spaceAfter=2,
    )
    styles["cover_score"] = ParagraphStyle(
        "cover_score",
        parent=base["Normal"],
        fontSize=11, fontName="Helvetica",
        textColor=colors.HexColor("#aaaaaa"),
        alignment=1,  # centrado
    )
    return styles


# ── Helpers visuales ──────────────────────────────────────────────────────────

def _score_circle(score_value: int, label: str) -> Drawing:
    """Círculo con el score, similar al diseño original."""
    color_map = {
        "Aceptable":       GREEN,
        "Riesgo moderado": YELLOW,
        "Riesgo alto":     ORANGE,
        "Crítico":         RED,
    }
    ring_color = color_map.get(label, PURPLE)

    d = Drawing(160, 160)
    # Círculo de fondo
    d.add(Circle(80, 80, 70, fillColor=colors.HexColor("#1a1a3e"),
                 strokeColor=ring_color, strokeWidth=6))
    # Número
    d.add(String(80, 88, str(score_value),
                 fontSize=42, fontName="Helvetica-Bold",
                 fillColor=WHITE, textAnchor="middle"))
    # "/100"
    d.add(String(80, 68, "/ 100",
                 fontSize=12, fontName="Helvetica",
                 fillColor=colors.HexColor("#aaaaaa"), textAnchor="middle"))
    return d


def _severity_badge_table(severity: str) -> Table:
    """Badge de severidad coloreado."""
    severity_key = str(severity).lower()
    color = SEVERITY_COLOR.get(severity_key, GRAY_BORDER)
    label = SEVERITY_LABEL.get(severity_key, severity_key.upper())
    t = Table([[label]], colWidths=[1.8 * cm], rowHeights=[0.5 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, -1), color),
        ("TEXTCOLOR",   (0, 0), (-1, -1), WHITE),
        ("FONTNAME",    (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, -1), 7),
        ("ALIGN",       (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
        ("ROUNDEDCORNERS", [3]),
    ]))
    return t


def _summary_cards_table(breakdown: dict) -> Table:
    """Fila de 4 tarjetas con conteo por severidad."""
    data = [[
        Paragraph(f"<b>{breakdown.get('critical', 0)}</b>", ParagraphStyle(
            "sc", fontSize=28, fontName="Helvetica-Bold",
            textColor=WHITE, alignment=1)),
        Paragraph(f"<b>{breakdown.get('high', 0)}</b>", ParagraphStyle(
            "sc2", fontSize=28, fontName="Helvetica-Bold",
            textColor=WHITE, alignment=1)),
        Paragraph(f"<b>{breakdown.get('medium', 0)}</b>", ParagraphStyle(
            "sc3", fontSize=28, fontName="Helvetica-Bold",
            textColor=WHITE, alignment=1)),
        Paragraph(f"<b>{breakdown.get('low', 0)}</b>", ParagraphStyle(
            "sc4", fontSize=28, fontName="Helvetica-Bold",
            textColor=WHITE, alignment=1)),
    ], [
        Paragraph("Críticos",  ParagraphStyle("l1", fontSize=9, textColor=WHITE, alignment=1)),
        Paragraph("Altos",     ParagraphStyle("l2", fontSize=9, textColor=WHITE, alignment=1)),
        Paragraph("Medios",    ParagraphStyle("l3", fontSize=9, textColor=WHITE, alignment=1)),
        Paragraph("Bajos",     ParagraphStyle("l4", fontSize=9, textColor=WHITE, alignment=1)),
    ]]

    col_w = 4 * cm
    t = Table(data, colWidths=[col_w] * 4, rowHeights=[1.5 * cm, 0.6 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (0, 1), RED),
        ("BACKGROUND",  (1, 0), (1, 1), ORANGE),
        ("BACKGROUND",  (2, 0), (2, 1), YELLOW),
        ("BACKGROUND",  (3, 0), (3, 1), GREEN),
        ("ALIGN",       (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
        ("ROUNDEDCORNERS", [4]),
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


# ── Secciones compartidas ─────────────────────────────────────────────────────

def _cover_page(styles: dict, report_type: str, score_data: dict) -> list:
    """Portada oscura con logo, título y score."""
    elems = []

    # Bloque de portada con fondo oscuro simulado con tabla
    cover_content = [
        [Paragraph("🔒 PgVault", ParagraphStyle(
            "logo", fontSize=22, fontName="Helvetica-Bold",
            textColor=WHITE, alignment=1, spaceAfter=8))],
        [Paragraph(f"<b>{report_type}</b>", ParagraphStyle(
            "ct", fontSize=20, fontName="Helvetica-Bold",
            textColor=WHITE, alignment=1))],
        [Paragraph("Auditoría de base de datos PostgreSQL", ParagraphStyle(
            "cs", fontSize=11, fontName="Helvetica",
            textColor=colors.HexColor("#aaaaaa"), alignment=1, spaceAfter=20))],
        [_score_circle(score_data["score"], score_data["label"])],
        [Paragraph(f"<b>{score_data['label']}</b>", ParagraphStyle(
            "sv", fontSize=14, fontName="Helvetica-Bold",
            textColor=WHITE, alignment=1))],
        [Paragraph(
            f"Total de hallazgos: {score_data['total_findings']}",
            ParagraphStyle("tf", fontSize=10, fontName="Helvetica",
                           textColor=colors.HexColor("#aaaaaa"), alignment=1)
        )],
    ]

    cover_table = Table(cover_content, colWidths=[16 * cm])
    cover_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), DARK_BG),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
        ("ROUNDEDCORNERS", [8]),
    ]))

    elems.append(Spacer(1, 1.5 * cm))
    elems.append(cover_table)
    elems.append(PageBreak())
    return elems


def _section_header(title: str, styles: dict) -> list:
    """Encabezado de sección con línea de color."""
    elems = []
    # Barra de color izquierda simulada con tabla
    header_table = Table(
        [[Paragraph(f"<b>{title}</b>", ParagraphStyle(
            "sh", fontSize=13, fontName="Helvetica-Bold",
            textColor=TEXT_DARK))]],
        colWidths=[15 * cm],
    )
    header_table.setStyle(TableStyle([
        ("LEFTPADDING",  (0, 0), (-1, -1), 12),
        ("TOPPADDING",   (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 6),
        ("LINEBEFORE",   (0, 0), (0, -1), 4, PURPLE),
    ]))
    elems.append(Spacer(1, 0.4 * cm))
    elems.append(header_table)
    elems.append(Spacer(1, 0.2 * cm))
    return elems


# ── Reporte Ejecutivo ─────────────────────────────────────────────────────────

def generate_executive_report(findings: list[dict], output_path: str = None) -> str:
    styles    = _build_styles()
    score_data = calculate_score(findings)

    critical_findings = [f for f in findings if _severity_key(f) == "critical"][:5]
    by_module = {}
    for f in findings:
        mod = f.get("module", "otro")
        by_module.setdefault(mod, []).append(f)

    out  = output_path or str(OUTPUT_DIR / "reporte_ejecutivo.pdf")
    doc  = SimpleDocTemplate(
        out, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=1.5*cm, bottomMargin=1.5*cm,
    )
    elems = []

    # Portada
    elems += _cover_page(styles, "Reporte Ejecutivo de Seguridad", score_data)

    # Resumen general
    elems += _section_header("Resumen general", styles)
    elems.append(_summary_cards_table(score_data["breakdown"]))
    elems.append(Spacer(1, 0.8 * cm))

    # Top riesgos críticos
    if critical_findings:
        elems += _section_header("Top riesgos críticos", styles)
        for f in critical_findings:
            severity = _severity_key(f)
            color = SEVERITY_COLOR.get(severity, GRAY_BORDER)
            regs = format_regulations_inline(f.get("regulation_refs", []))
            if not regs:
                regs = ", ".join(f.get("regulations", []))

            card_data = [
                [_severity_badge_table(severity),
                 Paragraph(f"<b>{f['title']}</b>", styles["body"])],
                ["", Paragraph(f["description"], styles["body_muted"])],
            ]
            if regs:
                card_data.append([
                    "",
                    Paragraph(f"⚖️  {regs}", styles["reg_tag"])
                ])

            card = Table(card_data, colWidths=[2.2*cm, 13.5*cm])
            card.setStyle(TableStyle([
                ("BACKGROUND",    (0, 0), (-1, -1), GRAY_LIGHT),
                ("LINEBEFORE",    (0, 0), (0, -1), 4, color),
                ("VALIGN",        (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING",    (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING",   (0, 0), (-1, -1), 8),
                ("ROUNDEDCORNERS", [4]),
            ]))
            elems.append(card)
            elems.append(Spacer(1, 0.25 * cm))

    # Hallazgos por módulo
    elems.append(Spacer(1, 0.4 * cm))
    elems += _section_header("Hallazgos por módulo", styles)

    module_rows = [["Módulo", "Total", "Críticos", "Altos"]]
    for mod, items in by_module.items():
        crits = sum(1 for i in items if _severity_key(i) == "critical")
        highs = sum(1 for i in items if _severity_key(i) == "high")
        module_rows.append([mod.capitalize(), str(len(items)), str(crits), str(highs)])

    mod_table = Table(module_rows, colWidths=[8*cm, 3*cm, 2.5*cm, 2.5*cm])
    mod_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), DARK_BG),
        ("TEXTCOLOR",     (0, 0), (-1, 0), WHITE),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 10),
        ("ALIGN",         (1, 0), (-1, -1), "CENTER"),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [WHITE, GRAY_LIGHT]),
        ("GRID",          (0, 0), (-1, -1), 0.5, GRAY_BORDER),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    elems.append(mod_table)

    doc.build(elems)
    print(f"✅ Reporte ejecutivo generado: {out}")
    return out


# ── Reporte Técnico ───────────────────────────────────────────────────────────

def generate_technical_report(findings: list[dict], output_path: str = None) -> str:
    styles     = _build_styles()
    score_data = calculate_score(findings)

    # Adjunta detalles regulatorios y ordena por severidad
    for f in findings:
        reg_refs = f.get("regulation_refs", [])
        if reg_refs:
            f["regulation_details"] = enrich_regulation_refs(reg_refs)
        else:
            f["regulation_details"] = [
                {"law": reg, "article": "", "title": reg, "description": "", "url": ""}
                for reg in f.get("regulations", [])
            ]
    severity_order  = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    findings_sorted = sorted(findings,
                             key=lambda f: severity_order.get(_severity_key(f), 4))

    out = output_path or str(OUTPUT_DIR / "reporte_tecnico.pdf")
    doc = SimpleDocTemplate(
        out, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=1.5*cm, bottomMargin=1.5*cm,
    )
    elems = []

    # Portada
    elems += _cover_page(styles, "Reporte Técnico Detallado", score_data)

    # Resumen
    elems += _section_header("Resumen de hallazgos", styles)
    elems.append(_summary_cards_table(score_data["breakdown"]))
    elems.append(Spacer(1, 0.8 * cm))

    # Detalle de cada hallazgo
    elems += _section_header("Detalle de hallazgos", styles)
    elems.append(Paragraph(
        "Ordenados por severidad. Cada hallazgo incluye evidencia y SQL de remediación.",
        styles["body_muted"]
    ))
    elems.append(Spacer(1, 0.3 * cm))

    for i, f in enumerate(findings_sorted, 1):
        severity = _severity_key(f)
        color = SEVERITY_COLOR.get(severity, GRAY_BORDER)

        # Encabezado del hallazgo
        header_data = [[
            _severity_badge_table(severity),
            Paragraph(
                f"<b>[{f.get('id', f'F-{i:03d}')}] {f['title']}</b>",
                ParagraphStyle("fh", fontSize=11, fontName="Helvetica-Bold",
                               textColor=TEXT_DARK)
            ),
        ]]
        header_t = Table(header_data, colWidths=[2.2*cm, 13.5*cm])
        header_t.setStyle(TableStyle([
            ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ]))
        elems.append(header_t)
        elems.append(Spacer(1, 0.15 * cm))

        # Descripción
        elems.append(Paragraph(f["description"], styles["body"]))

        # Evidencia
        if f.get("evidence"):
            elems.append(Paragraph("<b>Evidencia (query ejecutada):</b>",
                                   styles["body_muted"]))
            elems.append(Paragraph(f["evidence"], styles["code"]))

        # Remediación SQL
        if f.get("remediation_sql"):
            elems.append(Paragraph("<b>SQL de remediación:</b>",
                                   styles["body_muted"]))
            elems.append(Paragraph(
                f["remediation_sql"].replace("\n", "<br/>"),
                styles["code"]
            ))

        # Mapeo regulatorio
        if f.get("regulation_details"):
            elems.append(Paragraph("<b>Regulación aplicable:</b>",
                                   styles["body_muted"]))
            for reg in f["regulation_details"]:
                if not reg.get("description"):
                    continue
                reg_data = [[
                    Paragraph(
                        f"<b>{reg['law']} — {reg['article']}: {reg['title']}</b>",
                        ParagraphStyle("rt", fontSize=8, fontName="Helvetica-Bold",
                                       textColor=PURPLE)
                    ),
                ], [
                    Paragraph(reg["description"],
                              ParagraphStyle("rd", fontSize=8, fontName="Helvetica",
                                             textColor=TEXT_MUTED, leading=12)),
                ]]
                reg_table = Table(reg_data, colWidths=[15.5*cm])
                reg_table.setStyle(TableStyle([
                    ("BACKGROUND",    (0, 0), (-1, -1), colors.HexColor("#f5f3ff")),
                    ("LEFTPADDING",   (0, 0), (-1, -1), 10),
                    ("TOPPADDING",    (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("LINEBEFORE",    (0, 0), (0, -1), 3, PURPLE),
                    ("ROUNDEDCORNERS", [3]),
                ]))
                elems.append(reg_table)
                elems.append(Spacer(1, 0.1 * cm))

        # Separador entre hallazgos
        elems.append(HRFlowable(width="100%", thickness=0.5,
                                color=GRAY_BORDER, spaceAfter=10))

    doc.build(elems)
    print(f"✅ Reporte técnico generado: {out}")
    return out


# ── Generar ambos de una llamada ──────────────────────────────────────────────

def generate_all(findings: list[dict]) -> dict:
    """Genera ejecutivo y técnico. Útil para el endpoint del backend."""
    return {
        "executive": generate_executive_report(findings),
        "technical": generate_technical_report(findings),
    }
