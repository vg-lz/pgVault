import re
from dataclasses import dataclass

from pgvault.models import ColumnMeta, RegulationRef

REGULATION_LFPDPPP = RegulationRef(
    framework="LFPDPPP",
    article="Art. 3",
    description="Datos personales que identifiquen o hagan identificable a una persona.",
)
REGULATION_PCI_REQ3 = RegulationRef(
    framework="PCI-DSS",
    article="Req. 3",
    description="Proteger los datos de titulares de tarjetas almacenados.",
)
REGULATION_PCI_REQ32 = RegulationRef(
    framework="PCI-DSS",
    article="Req. 3.2",
    description="No almacenar datos de autenticación confidenciales tras la autorización.",
)
REGULATION_CNBV = RegulationRef(
    framework="CNBV",
    article="Disposición 6a",
    description="Seguridad de la información en entidades financieras.",
)


@dataclass(frozen=True)
class NamePattern:
    data_type: str
    pattern: re.Pattern
    name_score: float
    severity_hint: str
    regulation_refs: tuple
    recommendation: str


NAME_PATTERNS: list[NamePattern] = [
    NamePattern(
        data_type="CVV",
        pattern=re.compile(r"\b(cvv|cvc|cvv2|cvc2|card_?verification)\b", re.I),
        name_score=0.50,
        severity_hint="CRITICAL",
        regulation_refs=(REGULATION_PCI_REQ32,),
        recommendation="Eliminar columna. PCI-DSS prohíbe almacenar CVV tras la autorización.",
    ),
    NamePattern(
        data_type="CARD_NUMBER",
        pattern=re.compile(r"\b(card_?num(ber)?|pan|tarjeta|numero_?tarjeta|card_?no)\b", re.I),
        name_score=0.45,
        severity_hint="CRITICAL",
        regulation_refs=(REGULATION_PCI_REQ3,),
        recommendation="Aplicar tokenización. Solo almacenar últimos 4 dígitos.",
    ),
    NamePattern(
        data_type="PASSWORD",
        pattern=re.compile(r"\b(password|passwd|pwd|contrase[nñ]a|clave_?acceso)\b", re.I),
        name_score=0.50,
        severity_hint="CRITICAL",
        regulation_refs=(REGULATION_LFPDPPP,),
        recommendation="Nunca almacenar contraseñas en texto plano. Usar pgcrypto bcrypt.",
    ),
    NamePattern(
        data_type="CURP",
        pattern=re.compile(r"\b(curp|clave_?unica|registro_?poblacion)\b", re.I),
        name_score=0.50,
        severity_hint="HIGH",
        regulation_refs=(REGULATION_LFPDPPP,),
        recommendation="CURP es dato personal sensible. Cifrar con pgcrypto o aplicar RLS.",
    ),
    NamePattern(
        data_type="RFC",
        pattern=re.compile(r"\b(rfc|registro_?fiscal|tax_?id|fiscal_?id)\b", re.I),
        name_score=0.45,
        severity_hint="HIGH",
        regulation_refs=(REGULATION_LFPDPPP,),
        recommendation="RFC es dato personal identificable. Aplicar RLS o cifrado.",
    ),
    NamePattern(
        data_type="EMAIL",
        pattern=re.compile(r"\b(email|correo|e_?mail|mail_?address|email_?addr)\b", re.I),
        name_score=0.40,
        severity_hint="MEDIUM",
        regulation_refs=(REGULATION_LFPDPPP,),
        recommendation="Email es dato personal. Restringir acceso con RLS.",
    ),
    NamePattern(
        data_type="PHONE",
        pattern=re.compile(r"\b(phone|tel[ef]?[ef]?ono?|celular|movil|mobile|phone_?num(ber)?)\b", re.I),
        name_score=0.40,
        severity_hint="MEDIUM",
        regulation_refs=(REGULATION_LFPDPPP,),
        recommendation="Teléfono es dato personal. Registrar consultas en auditoría.",
    ),
    NamePattern(
        data_type="TOKEN",
        pattern=re.compile(r"\b(token|api_?key|secret_?key|bearer|access_?token|refresh_?token|jwt)\b", re.I),
        name_score=0.50,
        severity_hint="CRITICAL",
        regulation_refs=(REGULATION_CNBV,),
        recommendation="Tokens nunca en texto plano. Usar HMAC o vault externo.",
    ),
    NamePattern(
        data_type="CLABE",
        pattern=re.compile(r"\b(clabe|cuenta_?interbancaria|interbank_?account)\b", re.I),
        name_score=0.45,
        severity_hint="HIGH",
        regulation_refs=(REGULATION_CNBV, REGULATION_PCI_REQ3),
        recommendation="CLABE es dato bancario regulado por CNBV. Cifrar en reposo.",
    ),
    NamePattern(
        data_type="DATE_OF_BIRTH",
        pattern=re.compile(r"\b(fecha_?nac(imiento)?|birth_?date|dob|date_?of_?birth|f_?nac)\b", re.I),
        name_score=0.35,
        severity_hint="MEDIUM",
        regulation_refs=(REGULATION_LFPDPPP,),
        recommendation="Fecha de nacimiento es dato personal. Evaluar si se necesita fecha exacta.",
    ),
    NamePattern(
        data_type="SSN",
        pattern=re.compile(r"\b(ssn|social_?security|nss|num_?seg_?social|imss)\b", re.I),
        name_score=0.45,
        severity_hint="HIGH",
        regulation_refs=(REGULATION_LFPDPPP,),
        recommendation="NSS es dato personal sensible. Cifrar y controlar acceso.",
    ),
    NamePattern(
        data_type="FULL_NAME",
        pattern=re.compile(r"\b(nombre_?completo|full_?name|first_?name|last_?name|apellido|nombre_?titular)\b", re.I),
        name_score=0.30,
        severity_hint="LOW",
        regulation_refs=(REGULATION_LFPDPPP,),
        recommendation="Nombre es dato personal. Verificar que acceso esté limitado.",
    ),
]

COLUMN_WHITELIST = frozenset({
    "id", "uuid", "created_at", "updated_at", "deleted_at",
    "status", "type", "code", "version", "order", "rank",
    "is_active", "is_deleted", "is_enabled", "flag",
    "count", "total", "amount", "price", "quantity",
})


@dataclass
class NameMatch:
    column: ColumnMeta
    data_type: str
    name_score: float
    severity_hint: str
    regulation_refs: tuple
    recommendation: str
    matched_pattern: str


def scan_by_name(columns: list[ColumnMeta]) -> list[NameMatch]:
    matches: list[NameMatch] = []
    for col in columns:
        col_name_lower = col.column_name.lower()
        if col_name_lower in COLUMN_WHITELIST:
            continue
        for pattern in NAME_PATTERNS:
            if pattern.pattern.search(col_name_lower):
                matches.append(NameMatch(
                    column=col,
                    data_type=pattern.data_type,
                    name_score=pattern.name_score,
                    severity_hint=pattern.severity_hint,
                    regulation_refs=pattern.regulation_refs,
                    recommendation=pattern.recommendation,
                    matched_pattern=pattern.pattern.pattern,
                ))
                break
    return matches
