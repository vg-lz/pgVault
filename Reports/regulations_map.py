# reports/regulations_map.py

# URLs oficiales por framework 
FRAMEWORK_URLS: dict[str, str] = {
    "LFPDPPP": "https://www.diputados.gob.mx/LeyesBiblio/pdf/LFPDPPP.pdf",
    "PCI-DSS":  "https://www.pcisecuritystandards.org",
    "CNBV":     "https://www.cnbv.gob.mx",
    "OWASP":    "https://owasp.org/www-project-database-security/",
    "CIS":      "https://www.cisecurity.org/benchmark/postgresql",
}

# Descripciones extendidas por framework + artículo 
EXTENDED_DESCRIPTIONS: dict[tuple[str, str], str] = {
    ("LFPDPPP", "ART. 3"): (
        "Datos personales: cualquier información concerniente a una persona "
        "física identificada o identificable. Incluye nombre, CURP, RFC, "
        "correo, teléfono y datos financieros."
    ),
    ("LFPDPPP", "ART. 19"): (
        "El responsable que trate datos personales deberá establecer y "
        "mantener medidas de seguridad administrativas, técnicas y físicas "
        "que permitan protegerlos contra daño, pérdida, alteración, "
        "destrucción o uso no autorizado."
    ),
    ("LFPDPPP", "ART. 20"): (
        "El responsable o terceros que intervengan en cualquier fase del "
        "tratamiento de datos personales deberán guardar confidencialidad "
        "respecto de éstos, obligación que subsistirá aun después de "
        "finalizar sus relaciones con el responsable."
    ),
    ("LFPDPPP", "ART. 48"): (
        "Las infracciones a la presente Ley serán sancionadas con multa "
        "de 100 hasta 320,000 días de salario mínimo general vigente. "
        "Las violaciones graves pueden duplicar la sanción."
    ),
    ("PCI-DSS", "REQ. 3"): (
        "Proteger los datos de titulares de tarjetas almacenados. "
        "Nunca almacenar datos de autenticación confidenciales (CVV, PIN) "
        "tras la autorización de la transacción."
    ),
    ("PCI-DSS", "REQ. 3.2"): (
        "No almacenar datos de autenticación confidenciales tras la "
        "autorización, incluso cifrados. Esto incluye CVV2, CVC2, "
        "datos de banda magnética y PINs."
    ),
    ("PCI-DSS", "REQ. 3.4"): (
        "El PAN (Primary Account Number) debe ser ilegible en cualquier "
        "lugar donde se almacene, usando hash criptográfico fuerte, "
        "truncamiento, index tokens o cifrado fuerte con gestión de claves."
    ),
    ("PCI-DSS", "REQ. 7"): (
        "Restringir el acceso a los componentes del sistema y a los datos "
        "del titular de tarjeta únicamente a las personas cuyo trabajo "
        "requiera dicho acceso (principio de mínimo privilegio)."
    ),
    ("PCI-DSS", "REQ. 8"): (
        "Identificar a los usuarios y autenticar el acceso a los componentes "
        "del sistema. Prohibido el uso de credenciales genéricas o "
        "contraseñas vacías. Requiere autenticación multifactor para acceso "
        "remoto."
    ),
    ("PCI-DSS", "REQ. 10"): (
        "Registrar y monitorear todos los accesos a los componentes del "
        "sistema y a los datos del titular de tarjeta. Los logs deben "
        "protegerse contra modificación y conservarse al menos 12 meses."
    ),
    ("CNBV", "DISPOSICIÓN 6A"): (
        "Las entidades financieras reguladas por la CNBV deben implementar "
        "controles de seguridad de la información que protejan la "
        "confidencialidad, integridad y disponibilidad de los datos "
        "de sus clientes y operaciones."
    ),
}


def enrich_regulation_ref(reg_ref: dict) -> dict:
    """
    Recibe un RegulationRef serializado como dict
    (con keys: framework, article, description)
    y lo regresa con URL y descripción extendida si aplica.

    Retorna un dict listo para usar en el generador de reportes.
    """
    framework   = (reg_ref.get("framework") or "").strip()
    article     = (reg_ref.get("article")   or "").strip()
    description = (reg_ref.get("description") or "").strip()

    # Busca descripción extendida si la del scanner es corta o vacía
    key = (framework.upper(), article.upper())
    extended = EXTENDED_DESCRIPTIONS.get(key, "")
    final_description = description if len(description) > 40 else (extended or description)

    return {
        "law":         framework,
        "article":     article,
        "title":       article,          # RegulationRef no tiene campo title
        "description": final_description,
        "url":         FRAMEWORK_URLS.get(framework, ""),
    }


def enrich_regulation_refs(reg_refs: list[dict]) -> list[dict]:
    """
    Recibe la lista completa de regulation_refs de un Finding
    """
    return [enrich_regulation_ref(r) for r in reg_refs if r]


# Helpers de display 

def format_regulation_short(reg_ref: dict) -> str:
    """
    Versión corta para badges: 'LFPDPPP Art. 19'
    Útil para el reporte ejecutivo donde no hay espacio para la descripción.
    """
    framework = reg_ref.get("framework", "")
    article   = reg_ref.get("article", "")
    if framework and article:
        return f"{framework} {article}"
    return framework or article or "Regulación no especificada"


def format_regulations_inline(reg_refs: list[dict]) -> str:
    """
    Lista de regulaciones en una sola línea separada por comas.
    """
    return ", ".join(format_regulation_short(r) for r in reg_refs if r)
