"""Report generation endpoints for PgVault web interface.
Se integra con web.py agregando dos endpoints:
    POST /api/reports/executive
    POST /api/reports/technical

Los findings llegan como lista de dicts serializados desde ScanResult.model_dump().
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse
from pydantic import BaseModel

# Importa el generador de tu módulo de reportes
import sys
sys.path.append(str(Path(__file__).parent.parent / "reports"))
from generator import generate_executive_report, generate_technical_report

router = APIRouter(prefix="/api/reports", tags=["reports"])

# Directorio temporal para los PDFs generados
# En Docker usa el tmpfs montado en /app/data
_PDF_DIR = Path("/app/data")
if not _PDF_DIR.exists():
    # Fallback local para desarrollo fuera de Docker
    _PDF_DIR = Path(tempfile.gettempdir()) / "pgvault_reports"
    _PDF_DIR.mkdir(parents=True, exist_ok=True)


class ReportRequest(BaseModel):
    """Payload que recibe cada endpoint de reporte.

    findings: la lista findings de ScanResult.model_dump(mode='json')
    database: nombre de la BD escaneada (para el nombre del archivo)
    """
    findings: list[dict]
    database: str = "pgvault"


@router.post("/executive")
async def get_executive_report(payload: ReportRequest) -> FileResponse:
    """Genera y descarga el reporte ejecutivo en PDF."""
    if not payload.findings:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="No hay hallazgos para generar el reporte.")

    out_path = str(_PDF_DIR / f"reporte_ejecutivo_{payload.database}.pdf")
    generate_executive_report(payload.findings, output_path=out_path)

    return FileResponse(
        path=out_path,
        media_type="application/pdf",
        filename=f"PgVault_Ejecutivo_{payload.database}.pdf",
    )


@router.post("/technical")
async def get_technical_report(payload: ReportRequest) -> FileResponse:
    """Genera y descarga el reporte técnico en PDF."""
    if not payload.findings:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="No hay hallazgos para generar el reporte.")

    out_path = str(_PDF_DIR / f"reporte_tecnico_{payload.database}.pdf")
    generate_technical_report(payload.findings, output_path=out_path)

    return FileResponse(
        path=out_path,
        media_type="application/pdf",
        filename=f"PgVault_Tecnico_{payload.database}.pdf",
    )
