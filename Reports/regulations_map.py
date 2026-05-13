# Ley Federal de Protección de Datos Personales

REGULATIONS = {

    # ── LFPDPPP ──────────────────────────────────────────────────────────────
    "LFPDPPP_ART_19": {
        "law": "LFPDPPP",
        "article": "Artículo 19",
        "title": "Medidas de seguridad",
        "description": (
            "El responsable que trate datos personales deberá establecer y "
            "mantener medidas de seguridad administrativas, técnicas y físicas "
            "que permitan protegerlos contra daño, pérdida, alteración, "
            "destrucción o el uso, acceso o tratamiento no autorizado."
        ),
        "url": "https://www.diputados.gob.mx/LeyesBiblio/pdf/LFPDPPP.pdf",
    },
    "LFPDPPP_ART_20": {
        "law": "LFPDPPP",
        "article": "Artículo 20",
        "title": "Confidencialidad",
        "description": (
            "El responsable o terceros que intervengan en cualquier fase del "
            "tratamiento de datos personales deberán guardar confidencialidad "
            "respecto de éstos."
        ),
        "url": "https://www.diputados.gob.mx/LeyesBiblio/pdf/LFPDPPP.pdf",
    },
    "LFPDPPP_ART_48": {
        "law": "LFPDPPP",
        "article": "Artículo 48",
        "title": "Sanciones económicas",
        "description": (
            "Las infracciones a la presente Ley serán sancionadas con multa "
            "de 100 hasta 320,000 días de salario mínimo general vigente en "
            "el Distrito Federal."
        ),
        "url": "https://www.diputados.gob.mx/LeyesBiblio/pdf/LFPDPPP.pdf",
    },

    # ── PCI-DSS ───────────────────────────────────────────────────────────────
    "PCI_DSS_REQ_3_4": {
        "law": "PCI-DSS v4.0",
        "article": "Requirement 3.4",
        "title": "PAN ilegible en almacenamiento",
        "description": (
            "El PAN (Primary Account Number) debe ser ilegible en cualquier "
            "lugar donde se almacene, usando hash criptográfico, truncamiento, "
            "index tokens o cifrado fuerte."
        ),
        "url": "https://www.pcisecuritystandards.org",
    },
    "PCI_DSS_REQ_7": {
        "law": "PCI-DSS v4.0",
        "article": "Requirement 7",
        "title": "Restricción de acceso por necesidad",
        "description": (
            "El acceso a los componentes del sistema y a los datos del titular "
            "de tarjeta debe estar restringido únicamente a las personas cuyo "
            "trabajo requiera dicho acceso."
        ),
        "url": "https://www.pcisecuritystandards.org",
    },
    "PCI_DSS_REQ_10": {
        "law": "PCI-DSS v4.0",
        "article": "Requirement 10",
        "title": "Registro y monitoreo de accesos",
        "description": (
            "Registrar y monitorear todos los accesos a los componentes del "
            "sistema y a los datos del titular de tarjeta."
        ),
        "url": "https://www.pcisecuritystandards.org",
    },
    "PCI_DSS_REQ_8": {
        "law": "PCI-DSS v4.0",
        "article": "Requirement 8",
        "title": "Identificación y autenticación de usuarios",
        "description": (
            "Identificar a los usuarios y autenticar el acceso a los "
            "componentes del sistema. Prohibido el uso de credenciales "
            "genéricas o contraseñas vacías."
        ),
        "url": "https://www.pcisecuritystandards.org",
    },
}


def get_regulation(code: str) -> dict:
    """Regresa el detalle de una regulación por su código.
    Si no existe, regresa un dict con el código crudo para no romper el reporte.
    """
    return REGULATIONS.get(code, {
        "law": code,
        "article": code,
        "title": "Regulación no mapeada",
        "description": "",
        "url": "",
    })


def get_regulations_for_finding(codes: list[str]) -> list[dict]:
    """Recibe una lista de códigos y regresa los detalles de cada uno."""
    return [get_regulation(c) for c in codes]
