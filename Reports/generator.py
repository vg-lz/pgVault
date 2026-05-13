# reports/generator.py
# Genera reportes ejecutivo y técnico en PDF usando reportlab.

from pathlib import Path

from reportlab.graphics.shapes import Circle, Drawing, String
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

try:
    from .scoring import calculate_score
    from .regulations_map import enrich_regulation_refs, format_regulations_inline
except ImportError:  # Permite ejecutar este archivo directamente.
    from scoring import calculate_score
    from regulations_map import enrich_regulation_refs, format_regulations_inline


OUTPUT_DIR = Path(__file__).parent.parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

DARK_BG = colors.HexColor("#0f0f23")
PURPLE = colors.HexColor("#6366f1")
RED = colors.HexColor("#ef4444")
ORANGE = colors.HexColor("#f97316")
YELLOW = colors.HexColor("#f59e0b")
GREEN = colors.HexColor("#22c55e")
GRAY_LIGHT = colors.HexColor("#f9f9f9")
GRAY_BORDER = colors.HexColor("#e5e7eb")
TEXT_DARK = colors.HexColor("#1a1a2e")
TEXT_MUTED = colors.HexColor("#6b7280")
WHITE = colors.white

SEVERITY_COLOR = {
    "critical": RED,
    "high": ORANGE,
    "medium": YELLOW,
    "low": GREEN,
}

SEVERITY_LABEL = {
    "critical": "CRÍTICO",
    "high": "ALTO",
    "medium": "MEDIO",
    "low": "BAJO",
}


def _severity_key(finding: dict) -> str:
    return str(finding.get("severity", "low")).lower()


def _build_styles() -> dict:
    base = getSampleStyleSheet()
    styles = {}

    styles["title"] = ParagraphStyle(
        "title",
        parent=base["Title"],
        fontSize=26,
        fontName="Helvetica-Bold",
        textColor=WHITE,
        spaceAfter=6,
    )
    styles["subtitle"] = ParagraphStyle(
        "subtitle",
        parent=base["Normal"],
        fontSize=12,
        fontName="Helvetica",
        textColor=colors.HexColor("#aaaaaa"),
        spaceAfter=4,
    )
    styles["h2"] = ParagraphStyle(
        "h2",
        parent=base["Heading2"],
        fontSize=14,
        fontName="Helvetica-Bold",
        textColor=TEXT_DARK,
        spaceBefore=16,
        spaceAfter=10,
    )
    styles["body"] = ParagraphStyle(
        "body",
        parent=base["Normal"],
        fontSize=10,
        fontName="Helvetica",
        textColor=TEXT_DARK,
        spaceAfter=4,
        leading=15,
    )
    styles["body_muted"] = ParagraphStyle(
        "body_muted",
        parent=base["Normal"],
        fontSize=9,
        fontName="Helvetica",
        textColor=TEXT_MUTED,
        spaceAfter=3,
    )
    styles["code"] = ParagraphStyle(
        "code",
        parent=base["Code"],
        fontSize=8,
        fontName="Courier",
        textColor=colors.HexColor("#334155"),
        backColor=colors.HexColor("#f1f5f9"),
        borderPad=6,
        spaceAfter=4,
        leading=13,
    )
    styles["reg_tag"] = ParagraphStyle(
        "reg_tag",
        parent=base["Normal"],
        fontSize=8,
        fontName="Helvetica-Bold",
        textColor=PURPLE,
        spaceAfter=2,
    )
    return styles


def _score_circle(score_value: int, label: str) -> Drawing:
    color_map = {
        "Aceptable": GREEN,
        "Riesgo moderado": YELLOW,
        "Riesgo alto": ORANGE,
        "Crítico": RED,
    }
    ring_color = color_map.get(label, PURPLE)

    d = Drawing(160, 160)
    d.add(
        Circle(
            80,
            80,
            70,
            fillColor=colors.HexColor("#1a1a3e"),
            strokeColor=ring_color,
            strokeWidth=6,
        )
    )
    d.add(
        String(
            80,
            88,
            str(score_value),
            fontSize=42,
            fontName="Helvetica-Bold",
            fillColor=WHITE,
            textAnchor="middle",
        )
    )
    d.add(
        String(
            80,
            68,
            "/ 100",
            fontSize=12,
            fontName="Helvetica",
            fillColor=colors.HexColor("#aaaaaa"),
            textAnchor="middle",
        )
    )
    return d


def _severity_badge_table(severity: str) -> Table:
    severity_key = str(severity or "low").lower()
    color = SEVERITY_COLOR.get(severity_key, GRAY_BORDER)
    label = SEVERITY_LABEL.get(severity_key, severity_key.upper())

    table = Table([[label]], colWidths=[1.8 * cm], rowHeights=[0.5 * cm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), color),
                ("TEXTCOLOR", (0, 0), (-1, -1), WHITE),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 7),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    return table


def _summary_cards_table(breakdown: dict) -> Table:
    def _count_style(name: str) -> ParagraphStyle:
        return ParagraphStyle(
            name,
            fontSize=28,
            fontName="Helvetica-Bold",
            textColor=WHITE,
            alignment=1,
        )

    def _label_style(name: str) -> ParagraphStyle:
        return ParagraphStyle(name, fontSize=9, textColor=WHITE, alignment=1)

    data = [
        [
            Paragraph(f"<b>{breakdown.get('critical', 0)}</b>", _count_style("c1")),
            Paragraph(f"<b>{breakdown.get('high', 0)}</b>", _count_style("c2")),
            Paragraph(f"<b>{breakdown.get('medium', 0)}</b>", _count_style("c3")),
            Paragraph(f"<b>{breakdown.get('low', 0)}</b>", _count_style("c4")),
        ],
        [
            Paragraph("Críticos", _label_style("l1")),
            Paragraph("Altos", _label_style("l2")),
            Paragraph("Medios", _label_style("l3")),
            Paragraph("Bajos", _label_style("l4")),
        ],
    ]

    col_width = 4 * cm
    table = Table(data, colWidths=[col_width] * 4, rowHeights=[1.5 * cm, 0.6 * cm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, 1), RED),
                ("BACKGROUND", (1, 0), (1, 1), ORANGE),
                ("BACKGROUND", (2, 0), (2, 1), YELLOW),
                ("BACKGROUND", (3, 0), (3, 1), GREEN),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


def _cover_page(report_type: str, score_data: dict) -> list:
    cover_content = [
        [
            Paragraph(
                "PgVault",
                ParagraphStyle(
                    "logo",
                    fontSize=22,
                    fontName="Helvetica-Bold",
                    textColor=WHITE,
                    alignment=1,
                    spaceAfter=8,
                ),
            )
        ],
        [
            Paragraph(
                f"<b>{report_type}</b>",
                ParagraphStyle(
                    "ct",
                    fontSize=20,
                    fontName="Helvetica-Bold",
                    textColor=WHITE,
                    alignment=1,
                ),
            )
        ],
        [
            Paragraph(
                "Auditoría de base de datos PostgreSQL",
                ParagraphStyle(
                    "cs",
                    fontSize=11,
                    fontName="Helvetica",
                    textColor=colors.HexColor("#aaaaaa"),
                    alignment=1,
                    spaceAfter=20,
                ),
            )
        ],
        [_score_circle(score_data["score"], score_data["label"])],
        [
            Paragraph(
                f"<b>{score_data['label']}</b>",
                ParagraphStyle(
                    "sv",
                    fontSize=14,
                    fontName="Helvetica-Bold",
                    textColor=WHITE,
                    alignment=1,
                ),
            )
        ],
        [
            Paragraph(
                f"Total de hallazgos: {score_data['total_findings']}",
                ParagraphStyle(
                    "tf",
                    fontSize=10,
                    fontName="Helvetica",
                    textColor=colors.HexColor("#aaaaaa"),
                    alignment=1,
                ),
            )
        ],
    ]

    cover_table = Table(cover_content, colWidths=[16 * cm])
    cover_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), DARK_BG),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 14),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
            ]
        )
    )
    return [Spacer(1, 1.5 * cm), cover_table, PageBreak()]


def _section_header(title: str) -> list:
    header_table = Table(
        [
            [
                Paragraph(
                    f"<b>{title}</b>",
                    ParagraphStyle(
                        "sh",
                        fontSize=13,
                        fontName="Helvetica-Bold",
                        textColor=TEXT_DARK,
                    ),
                )
            ]
        ],
        colWidths=[15 * cm],
    )
    header_table.setStyle(
        TableStyle(
            [
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LINEBEFORE", (0, 0), (0, -1), 4, PURPLE),
            ]
        )
    )
    return [Spacer(1, 0.4 * cm), header_table, Spacer(1, 0.2 * cm)]


def generate_executive_report(findings: list[dict], output_path: str = None) -> str:
    styles = _build_styles()
    score_data = calculate_score(findings)

    critical_findings = [f for f in findings if _severity_key(f) == "critical"][:5]
    by_module: dict[str, list] = {}
    for finding in findings:
        module = finding.get("module", "otro")
        by_module.setdefault(module, []).append(finding)

    output = output_path or str(OUTPUT_DIR / "reporte_ejecutivo.pdf")
    doc = SimpleDocTemplate(
        output,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
    )
    elems = []

    elems += _cover_page("Reporte Ejecutivo de Seguridad", score_data)

    elems += _section_header("Resumen general")
    elems.append(_summary_cards_table(score_data["breakdown"]))
    elems.append(Spacer(1, 0.8 * cm))

    if critical_findings:
        elems += _section_header("Top riesgos críticos")
        for finding in critical_findings:
            severity = _severity_key(finding)
            color = SEVERITY_COLOR.get(severity, GRAY_BORDER)
            regs_line = format_regulations_inline(finding.get("regulation_refs", []))
            if not regs_line:
                regs_line = ", ".join(finding.get("regulations", []))

            card_data = [
                [
                    _severity_badge_table(severity),
                    Paragraph(f"<b>{finding.get('title', '')}</b>", styles["body"]),
                ],
                ["", Paragraph(finding.get("description", ""), styles["body_muted"])],
            ]
            if regs_line:
                card_data.append(["", Paragraph(f"Regulación: {regs_line}", styles["reg_tag"])])

            card = Table(card_data, colWidths=[2.2 * cm, 13.5 * cm])
            card.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), GRAY_LIGHT),
                        ("LINEBEFORE", (0, 0), (0, -1), 4, color),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("TOPPADDING", (0, 0), (-1, -1), 8),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                        ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ]
                )
            )
            elems.append(card)
            elems.append(Spacer(1, 0.25 * cm))

    elems.append(Spacer(1, 0.4 * cm))
    elems += _section_header("Hallazgos por módulo")

    module_rows = [["Módulo", "Total", "Críticos", "Altos"]]
    for module, items in by_module.items():
        critical_count = sum(1 for item in items if _severity_key(item) == "critical")
        high_count = sum(1 for item in items if _severity_key(item) == "high")
        module_rows.append(
            [module.capitalize(), str(len(items)), str(critical_count), str(high_count)]
        )

    module_table = Table(module_rows, colWidths=[8 * cm, 3 * cm, 2.5 * cm, 2.5 * cm])
    module_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), DARK_BG),
                ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, GRAY_LIGHT]),
                ("GRID", (0, 0), (-1, -1), 0.5, GRAY_BORDER),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    elems.append(module_table)

    doc.build(elems)
    print(f"Reporte ejecutivo generado: {output}")
    return output


def generate_technical_report(findings: list[dict], output_path: str = None) -> str:
    styles = _build_styles()
    score_data = calculate_score(findings)

    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    findings_sorted = sorted(
        findings,
        key=lambda finding: severity_order.get(_severity_key(finding), 4),
    )

    output = output_path or str(OUTPUT_DIR / "reporte_tecnico.pdf")
    doc = SimpleDocTemplate(
        output,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
    )
    elems = []

    elems += _cover_page("Reporte Técnico Detallado", score_data)

    elems += _section_header("Resumen de hallazgos")
    elems.append(_summary_cards_table(score_data["breakdown"]))
    elems.append(Spacer(1, 0.8 * cm))

    elems += _section_header("Detalle de hallazgos")
    elems.append(
        Paragraph(
            "Ordenados por severidad. Cada hallazgo incluye evidencia, recomendación y remediación cuando aplica.",
            styles["body_muted"],
        )
    )
    elems.append(Spacer(1, 0.3 * cm))

    for index, finding in enumerate(findings_sorted, 1):
        severity = _severity_key(finding)
        finding_id = finding.get("id", f"F-{index:03d}")

        header_table = Table(
            [
                [
                    _severity_badge_table(severity),
                    Paragraph(
                        f"<b>[{finding_id}] {finding.get('title', '')}</b>",
                        ParagraphStyle(
                            "fh",
                            fontSize=11,
                            fontName="Helvetica-Bold",
                            textColor=TEXT_DARK,
                        ),
                    ),
                ]
            ],
            colWidths=[2.2 * cm, 13.5 * cm],
        )
        header_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ]
            )
        )
        elems.append(header_table)
        elems.append(Spacer(1, 0.15 * cm))

        table_name = finding.get("table_name")
        column_name = finding.get("column_name")
        if table_name:
            location = f"{table_name}.{column_name}" if column_name else table_name
            elems.append(
                Paragraph(
                    f"<b>Objeto afectado:</b> <font name='Courier'>{location}</font>",
                    styles["body_muted"],
                )
            )

        elems.append(Paragraph(finding.get("description", ""), styles["body"]))

        evidence = finding.get("evidence", "")
        if evidence:
            elems.append(Paragraph("<b>Evidencia:</b>", styles["body_muted"]))
            elems.append(Paragraph(evidence, styles["code"]))

        recommendation = finding.get("recommendation", "")
        if recommendation:
            elems.append(Paragraph("<b>Recomendación:</b>", styles["body_muted"]))
            elems.append(Paragraph(recommendation, styles["body"]))

        remediation_sql = finding.get("remediation_sql")
        if remediation_sql:
            elems.append(Paragraph("<b>SQL de remediación:</b>", styles["body_muted"]))
            elems.append(Paragraph(remediation_sql.replace("\n", "<br/>"), styles["code"]))

        confidence = finding.get("confidence_score")
        if confidence is not None:
            elems.append(
                Paragraph(
                    f"<b>Confianza de detección:</b> {int(confidence * 100)}%",
                    styles["body_muted"],
                )
            )

        reg_refs = finding.get("regulation_refs", [])
        reg_details = finding.get("regulation_details") or enrich_regulation_refs(reg_refs)
        if not reg_details and finding.get("regulations"):
            reg_details = [
                {"law": reg, "article": "", "title": reg, "description": "", "url": ""}
                for reg in finding.get("regulations", [])
            ]

        if reg_details:
            elems.append(Paragraph("<b>Regulación aplicable:</b>", styles["body_muted"]))
            for reg in reg_details:
                description = reg.get("description", "")
                if not description:
                    continue

                title_parts = [reg.get("law", ""), reg.get("article", "")]
                title = " - ".join(part for part in title_parts if part)
                if reg.get("title") and reg.get("title") != reg.get("article"):
                    title = f"{title}: {reg['title']}" if title else reg["title"]

                reg_table = Table(
                    [
                        [
                            Paragraph(
                                f"<b>{title}</b>",
                                ParagraphStyle(
                                    "rt",
                                    fontSize=8,
                                    fontName="Helvetica-Bold",
                                    textColor=PURPLE,
                                ),
                            )
                        ],
                        [
                            Paragraph(
                                description,
                                ParagraphStyle(
                                    "rd",
                                    fontSize=8,
                                    fontName="Helvetica",
                                    textColor=TEXT_MUTED,
                                    leading=12,
                                ),
                            )
                        ],
                    ],
                    colWidths=[15.5 * cm],
                )
                reg_table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f5f3ff")),
                            ("LEFTPADDING", (0, 0), (-1, -1), 10),
                            ("TOPPADDING", (0, 0), (-1, -1), 5),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                            ("LINEBEFORE", (0, 0), (0, -1), 3, PURPLE),
                        ]
                    )
                )
                elems.append(reg_table)
                elems.append(Spacer(1, 0.1 * cm))

        elems.append(HRFlowable(width="100%", thickness=0.5, color=GRAY_BORDER, spaceAfter=10))

    doc.build(elems)
    print(f"Reporte técnico generado: {output}")
    return output


def generate_all(findings: list[dict]) -> dict:
    return {
        "executive": generate_executive_report(findings),
        "technical": generate_technical_report(findings),
    }
