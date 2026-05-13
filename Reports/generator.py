# reports/generator.py
# Genera reportes ejecutivo y técnico en PDF usando reportlab

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
from scoring import calculate_score
from regulations_map import enrich_regulation_refs, format_regulations_inline

# Rutas 
OUTPUT_DIR = Path(__file__).parent.parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# Paleta de colores PgVault 
DARK_BG     = colors.HexColor("#0f0f23")
PURPLE      = colors.HexColor("#6366f1")
RED         = colors.HexColor("#ef4444")
ORANGE      = colors.HexColor("#f97316")
YELLOW      = colors.HexColor("#f59e0b")
GREEN       = colors.HexColor("#22c55e")
GRAY_LIGHT  = colors.HexColor("#f9f9f9")
GRAY_BORDER = colors.HexColor("#e5e7eb")
TEXT_DARK   = colors.HexColor("#1a1a2e")
TEXT_MUTED  = colors.HexColor("#6b7280")
WHITE       = colors.white

# Severidad
SEVERITY_COLOR = {
    "CRITICAL": RED,
    "HIGH":     ORANGE,
    "MEDIUM":   YELLOW,
    "LOW":      GREEN,
}
SEVERITY_LABEL = {
    "CRITICAL": "CRÍTICO",
    "HIGH":     "ALTO",
    "MEDIUM":   "MEDIO",
    "LOW":      "BAJO",
}


# Estilos de texto 
def _build_styles() -> dict:
    base   = getSampleStyleSheet()
    styles = {}

    styles["title"] = ParagraphStyle(
        "title", parent=base["Title"],
        fontSize=26, fontName="Helvetica-Bold",
        textColor=WHITE, spaceAfter=6,
    )
    styles["subtitle"] = ParagraphStyle(
        "subtitle", parent=base["Normal"],
        fontSize=12, fontName="Helvetica",
        textColor=colors.HexColor("#aaaaaa"), spaceAfter=4,
    )
    styles["h2"] = ParagraphStyle(
        "h2", parent=base["Heading2"],
        fontSize=14, fontName="Helvetica-Bold",
        textColor=TEXT_DARK, spaceBefore=16, spaceAfter=10,
    )
    styles["body"] = ParagraphStyle(
        "body", parent=base["Normal"],
        fontSize=10, fontName="Helvetica",
        textColor=TEXT_DARK, spaceAfter=4, leading=15,
    )
    styles["body_muted"] = ParagraphStyle(
        "body_muted", parent=base["Normal"],
        fontSize=9, fontName="Helvetica",
        textColor=TEXT_MUTED, spaceAfter=3,
    )
    styles["code"] = ParagraphStyle(
        "code", parent=base["Code"],
        fontSize=8, fontName="Courier",
        textColor=colors.HexColor("#334155"),
        backColor=colors.HexColor("#f1f5f9"),
        borderPad=6, spaceAfter=4, leading=13,
    )
    styles["reg_tag"] = ParagraphStyle(
        "reg_tag", parent=base["Normal"],
        fontSize=8, fontName="Helvetica-Bold",
        textColor=PURPLE, spaceAfter=2,
    )
    return styles


# Helpers visuales 

def _score_circle(score_value: int, label: str) -> Drawing:
    color_map = {
        "Aceptable":       GREEN,
        "Riesgo moderado": YELLOW,
        "Riesgo alto":     ORANGE,
        "Crítico":         RED,
    }
    ring_color = color_map.get(label, PURPLE)
    d = Drawing(160, 160)
    d.add(Circle(80, 80, 70,
                 fillColor=colors.HexColor("#1a1a3e"),
                 strokeColor=ring_color, strokeWidth=6))
    d.add(String(80, 88, str(score_value),
                 fontSize=42, fontName="Helvetica-Bold",
                 fillColor=WHITE, textAnchor="middle"))
    d.add(String(80, 68, "/ 100",
                 fontSize=12, fontName="Helvetica",
                 fillColor=colors.HexColor("#aaaaaa"), textAnchor="middle"))
    return d


def _severity_badge_table(severity: str) -> Table:
    """Badge de severidad — severity debe estar en MAYÚSCULAS."""
    sev   = severity.upper()
    color = SEVERITY_COLOR.get(sev, GRAY_BORDER)
    label = SEVERITY_LABEL.get(sev, sev)
    t = Table([[label]], colWidths=[1.8 * cm], rowHeights=[0.5 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), color),
        ("TEXTCOLOR",  (0, 0), (-1, -1), WHITE),
        ("FONTNAME",   (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 0), (-1, -1), 7),
        ("ALIGN",      (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return t


def _summary_cards_table(breakdown: dict) -> Table:
    """Tarjetas de conteo por severidad — keys en MAYÚSCULAS."""
    def _count_style(name):
        return ParagraphStyle(name, fontSize=28, fontName="Helvetica-Bold",
                              textColor=WHITE, alignment=1)
    def _label_style(name):
        return ParagraphStyle(name, fontSize=9, textColor=WHITE, alignment=1)

    data = [
        [
            Paragraph(f"<b>{breakdown.get('CRITICAL', 0)}</b>", _count_style("c1")),
            Paragraph(f"<b>{breakdown.get('HIGH', 0)}</b>",     _count_style("c2")),
            Paragraph(f"<b>{breakdown.get('MEDIUM', 0)}</b>",   _count_style("c3")),
            Paragraph(f"<b>{breakdown.get('LOW', 0)}</b>",      _count_style("c4")),
        ],
        [
            Paragraph("Críticos", _label_style("l1")),
            Paragraph("Altos",    _label_style("l2")),
            Paragraph("Medios",   _label_style("l3")),
            Paragraph("Bajos",    _label_style("l4")),
        ],
    ]
    col_w = 4 * cm
    t = Table(data, colWidths=[col_w] * 4, rowHeights=[1.5 * cm, 0.6 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 1), RED),
        ("BACKGROUND", (1, 0), (1, 1), ORANGE),
        ("BACKGROUND", (2, 0), (2, 1), YELLOW),
        ("BACKGROUND", (3, 0), (3, 1), GREEN),
        ("ALIGN",      (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


# Secciones compartidas 

def _cover_page(report_type: str, score_data: dict) -> list:
    cover_content = [
        [Paragraph("🔒 PgVault", ParagraphStyle(
            "logo", fontSize=22, fontName="Helvetica-Bold",
            textColor=WHITE, alignment=1))],
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
    ]))
    return [Spacer(1, 1.5 * cm), cover_table, PageBreak()]


def _section_header(title: str) -> list:
    header_table = Table(
        [[Paragraph(f"<b>{title}</b>", ParagraphStyle(
            "sh", fontSize=13, fontName="Helvetica-Bold", textColor=TEXT_DARK))]],
        colWidths=[15 * cm],
    )
    header_table.setStyle(TableStyle([
        ("LEFTPADDING",   (0, 0), (-1, -1), 12),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LINEBEFORE",    (0, 0), (0, -1), 4, PURPLE),
    ]))
    return [Spacer(1, 0.4 * cm), header_table, Spacer(1, 0.2 * cm)]


# Reporte Ejecutivo 

def generate_executive_report(findings: list[dict], output_path: str = None) -> str:
    styles     = _build_styles()
    score_data = calculate_score(findings)

    critical_findings = [
        f for f in findings if f.get("severity", "").upper() == "CRITICAL"
    ][:5]

    by_module: dict[str, list] = {}
    for f in findings:
        mod = f.get("module", "otro")
        by_module.setdefault(mod, []).append(f)

    out = output_path or str(OUTPUT_DIR / "reporte_ejecutivo.pdf")
    doc = SimpleDocTemplate(
        out, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=1.5*cm, bottomMargin=1.5*cm,
    )
    elems = []

    elems += _cover_page("Reporte Ejecutivo de Seguridad", score_data)

    elems += _section_header("Resumen general")
    elems.append(_summary_cards_table(score_data["breakdown"]))
    elems.append(Spacer(1, 0.8 * cm))

    if critical_findings:
        elems += _section_header("Top riesgos críticos")
        for f in critical_findings:
            sev       = f.get("severity", "LOW").upper()
            color     = SEVERITY_COLOR.get(sev, GRAY_BORDER)
            regs_line = format_regulations_inline(f.get("regulation_refs", []))

            card_data = [
                [_severity_badge_table(sev),
                 Paragraph(f"<b>{f.get('title', '')}</b>", styles["body"])],
                ["", Paragraph(f.get("description", ""), styles["body_muted"])],
            ]
            if regs_line:
                card_data.append(["", Paragraph(f"⚖️  {regs_line}", styles["reg_tag"])])

            card = Table(card_data, colWidths=[2.2*cm, 13.5*cm])
            card.setStyle(TableStyle([
                ("BACKGROUND",    (0, 0), (-1, -1), GRAY_LIGHT),
                ("LINEBEFORE",    (0, 0), (0, -1), 4, color),
                ("VALIGN",        (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING",    (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING",   (0, 0), (-1, -1), 8),
            ]))
            elems.append(card)
            elems.append(Spacer(1, 0.25 * cm))

    elems.append(Spacer(1, 0.4 * cm))
    elems += _section_header("Hallazgos por módulo")

    module_rows = [["Módulo", "Total", "Críticos", "Altos"]]
    for mod, items in by_module.items():
        crits = sum(1 for i in items if i.get("severity", "").upper() == "CRITICAL")
        highs = sum(1 for i in items if i.get("severity", "").upper() == "HIGH")
        module_rows.append([mod.capitalize(), str(len(items)), str(crits), str(highs)])

    mod_table = Table(module_rows, colWidths=[8*cm, 3*cm, 2.5*cm, 2.5*cm])
    mod_table.setStyle(TableStyle([
        ("BACKGROUND",     (0, 0), (-1, 0), DARK_BG),
        ("TEXTCOLOR",      (0, 0), (-1, 0), WHITE),
        ("FONTNAME",       (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",       (0, 0), (-1, -1), 10),
        ("ALIGN",          (1, 0), (-1, -1), "CENTER"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, GRAY_LIGHT]),
        ("GRID",           (0, 0), (-1, -1), 0.5, GRAY_BORDER),
        ("TOPPADDING",     (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 8),
    ]))
    elems.append(mod_table)

    doc.build(elems)
    print(f"✅ Reporte ejecutivo generado: {out}")
    return out


# Reporte Técnico 

def generate_technical_report(findings: list[dict], output_path: str = None) -> str:
    styles     = _build_styles()
    score_data = calculate_score(findings)

    severity_order  = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    findings_sorted = sorted(
        findings,
        key=lambda f: severity_order.get(f.get("severity", "LOW").upper(), 4)
    )

    out = output_path or str(OUTPUT_DIR / "reporte_tecnico.pdf")
    doc = SimpleDocTemplate(
        out, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=1.5*cm, bottomMargin=1.5*cm,
    )
    elems = []

    elems += _cover_page("Reporte Técnico Detallado", score_data)

    elems += _section_header("Resumen de hallazgos")
    elems.append(_summary_cards_table(score_data["breakdown"]))
    elems.append(Spacer(1, 0.8 * cm))

    elems += _section_header("Detalle de hallazgos")
    elems.append(Paragraph(
        "Ordenados por severidad. Cada hallazgo incluye evidencia y recomendación.",
        styles["body_muted"]
    ))
    elems.append(Spacer(1, 0.3 * cm))

    for i, f in enumerate(findings_sorted, 1):
        sev        = f.get("severity", "LOW").upper()
        color      = SEVERITY_COLOR.get(sev, GRAY_BORDER)
        finding_id = f.get("id", f"F-{i:03d}")   # "id" según pgvault.models.Finding

        # Encabezado
        header_t = Table([[
            _severity_badge_table(sev),
            Paragraph(
                f"<b>[{finding_id}] {f.get('title', '')}</b>",
                ParagraphStyle("fh", fontSize=11, fontName="Helvetica-Bold",
                               textColor=TEXT_DARK)
            ),
        ]], colWidths=[2.2*cm, 13.5*cm])
        header_t.setStyle(TableStyle([
            ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ]))
        elems.append(header_t)
        elems.append(Spacer(1, 0.15 * cm))

        # Objeto afectado (tabla/columna)
        table_name  = f.get("table_name")
        column_name = f.get("column_name")
        if table_name:
            location = f"{table_name}.{column_name}" if column_name else table_name
            elems.append(Paragraph(
                f"<b>Objeto afectado:</b> <font name='Courier'>{location}</font>",
                styles["body_muted"]
            ))

        # Descripción
        elems.append(Paragraph(f.get("description", ""), styles["body"]))

        # Evidencia
        evidence = f.get("evidence", "")
        if evidence:
            elems.append(Paragraph("<b>Evidencia (query ejecutada):</b>",
                                   styles["body_muted"]))
            elems.append(Paragraph(evidence, styles["code"]))

        # Recomendación (campo recommendation de pgvault.models.Finding)
        recommendation = f.get("recommendation", "")
        if recommendation:
            elems.append(Paragraph("<b>Recomendación:</b>", styles["body_muted"]))
            elems.append(Paragraph(recommendation, styles["body"]))

        # SQL de remediación (campo remediation_sql, puede ser None)
        remediation_sql = f.get("remediation_sql")
        if remediation_sql:
            elems.append(Paragraph("<b>SQL de remediación:</b>", styles["body_muted"]))
            elems.append(Paragraph(
                remediation_sql.replace("\n", "<br/>"),
                styles["code"]
            ))

        # Confianza de detección (solo hallazgos PII por contenido)
        confidence = f.get("confidence_score")
        if confidence is not None:
            elems.append(Paragraph(
                f"<b>Confianza de detección:</b> {int(confidence * 100)}%",
                styles["body_muted"]
            ))

        # Mapeo regulatorio con enrich_regulation_refs
        reg_refs = f.get("regulation_refs", [])
        if reg_refs:
            elems.append(Paragraph("<b>Regulación aplicable:</b>",
                                   styles["body_muted"]))
            for reg in enrich_regulation_refs(reg_refs):
                if not reg.get("description"):
                    continue
                reg_table = Table([
                    [Paragraph(f"<b>{reg['law']} — {reg['article']}</b>",
                               ParagraphStyle("rt", fontSize=8,
                                              fontName="Helvetica-Bold",
                                              textColor=PURPLE))],
                    [Paragraph(reg["description"],
                               ParagraphStyle("rd", fontSize=8,
                                              fontName="Helvetica",
                                              textColor=TEXT_MUTED,
                                              leading=12))],
                ], colWidths=[15.5*cm])
                reg_table.setStyle(TableStyle([
                    ("BACKGROUND",    (0, 0), (-1, -1), colors.HexColor("#f5f3ff")),
                    ("LEFTPADDING",   (0, 0), (-1, -1), 10),
                    ("TOPPADDING",    (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("LINEBEFORE",    (0, 0), (0, -1), 3, PURPLE),
                ]))
                elems.append(reg_table)
                elems.append(Spacer(1, 0.1 * cm))

        elems.append(HRFlowable(width="100%", thickness=0.5,
                                color=GRAY_BORDER, spaceAfter=10))

    doc.build(elems)
    print(f"✅ Reporte técnico generado: {out}")
    return out


# Generar ambos de una llamada 

def generate_all(findings: list[dict]) -> dict:
    """Genera ejecutivo y técnico. Útil para el endpoint del backend."""
    return {
        "executive": generate_executive_report(findings),
        "technical": generate_technical_report(findings),
    }
