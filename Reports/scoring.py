# scoring.py

SEVERITY_WEIGHTS = {
    "critical": 15,
    "high":      8,
    "medium":    3,
    "low":       1,
}

def calculate_score(findings: list[dict]) -> dict:
    """
    Recibe lista de hallazgos, regresa score y desglose.
    """
    deduction = 0
    breakdown = {"critical": 0, "high": 0, "medium": 0, "low": 0}

    for f in findings:
        sev = str(f.get("severity", "low")).lower()
        deduction += SEVERITY_WEIGHTS.get(sev, 1)
        breakdown[sev if sev in breakdown else "low"] += 1

    score = max(0, 100 - deduction)

    # Etiqueta cualitativa para el reporte ejecutivo
    if score >= 80:
        label = "Aceptable"
    elif score >= 60:
        label = "Riesgo moderado"
    elif score >= 40:
        label = "Riesgo alto"
    else:
        label = "Crítico"

    return {
        "score": score,
        "label": label,
        "breakdown": breakdown,
        "total_findings": len(findings),
    }
