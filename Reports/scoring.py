# scoring.py

SEVERITY_WEIGHTS = {
    "CRITICAL": 15,
    "HIGH":      8,
    "MEDIUM":    3,
    "LOW":       1,
}

def calculate_score(findings: list[dict]) -> dict:
    """
    Recibe lista de hallazgos, regresa score y desglose.
    """
    deduction = 0
    breakdown = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}

    for f in findings:
        sev = f.get("severity", "LOW").upper()
        deduction += SEVERITY_WEIGHTS.get(sev, 1)
        breakdown[sev] += 1

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
