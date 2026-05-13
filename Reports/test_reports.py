# test_reports.py
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from generator import generate_executive_report, generate_technical_report

FAKE_FINDINGS = [
    {
        "id": "CFG-001", "module": "configuracion", "category": "roles_privilegios",
        "severity": "CRITICAL", "title": "Usuario con SUPERUSER innecesario",
        "description": "El rol 'app_user' tiene privilegios SUPERUSER sin justificacion operativa.",
        "evidence": "SELECT rolname FROM pg_roles WHERE rolsuper = true;",
        "recommendation": "Remover SUPERUSER de roles que no lo requieran.",
        "remediation_sql": "ALTER ROLE app_user NOSUPERUSER;",
        "regulation_refs": [
            {"framework": "PCI-DSS", "article": "Req. 7", "description": "Restriccion de acceso por necesidad."},
            {"framework": "LFPDPPP", "article": "Art. 19", "description": "Medidas de seguridad tecnicas."},
        ],
        "table_name": None, "column_name": None, "confidence_score": None,
    },
    {
        "id": "CFG-002", "module": "configuracion", "category": "logging",
        "severity": "CRITICAL", "title": "Logging de conexiones desactivado",
        "description": "log_connections = off. No hay rastro de quien accede a la base de datos.",
        "evidence": "SHOW log_connections;",
        "recommendation": "Activar log_connections para cumplir PCI-DSS Req. 10.",
        "remediation_sql": "ALTER SYSTEM SET log_connections = 'on';\nSELECT pg_reload_conf();",
        "regulation_refs": [
            {"framework": "PCI-DSS", "article": "Req. 10", "description": "Registro y monitoreo de accesos."},
        ],
        "table_name": None, "column_name": None, "confidence_score": None,
    },
    {
        "id": "PII-001", "module": "datos_sensibles", "category": "pci",
        "severity": "CRITICAL", "title": "CVV almacenado en texto plano",
        "description": "La columna 'cvv' en la tabla 'tarjetas' contiene datos de verificacion sin cifrado.",
        "evidence": "SELECT column_name FROM information_schema.columns WHERE column_name ILIKE '%cvv%';",
        "recommendation": "Eliminar la columna. PCI-DSS prohibe almacenar CVV tras la autorizacion.",
        "remediation_sql": "ALTER TABLE tarjetas DROP COLUMN cvv;",
        "regulation_refs": [
            {"framework": "PCI-DSS", "article": "Req. 3.2", "description": "No almacenar CVV tras la autorizacion."},
        ],
        "table_name": "tarjetas", "column_name": "cvv", "confidence_score": None,
    },
    {
        "id": "PII-002", "module": "datos_sensibles", "category": "pii_contenido",
        "severity": "HIGH", "title": "Columna generica contiene CURPs",
        "description": "La columna 'data' contiene CURPs en el 87% de los valores muestreados.",
        "evidence": "SELECT data FROM usuarios_extra LIMIT 5;",
        "recommendation": "Renombrar columna, cifrar con pgcrypto y aplicar RLS.",
        "remediation_sql": None,
        "regulation_refs": [
            {"framework": "LFPDPPP", "article": "Art. 3", "description": "CURP es dato personal identificable."},
        ],
        "table_name": "usuarios_extra", "column_name": "data", "confidence_score": 0.87,
    },
    {
        "id": "CFG-003", "module": "configuracion", "category": "autenticacion",
        "severity": "HIGH", "title": "Metodo trust habilitado en pg_hba",
        "description": "pg_hba.conf permite acceso sin contrasena desde rangos de IP amplios.",
        "evidence": "SELECT * FROM pg_hba_file_rules WHERE auth_method = 'trust';",
        "recommendation": "Cambiar trust por scram-sha-256.",
        "remediation_sql": "-- Editar pg_hba.conf y cambiar trust por scram-sha-256",
        "regulation_refs": [
            {"framework": "PCI-DSS", "article": "Req. 8", "description": "Autenticacion de usuarios."},
        ],
        "table_name": None, "column_name": None, "confidence_score": None,
    },
    {
        "id": "PII-003", "module": "datos_sensibles", "category": "pii_nombre",
        "severity": "MEDIUM", "title": "Email accesible por roles sin necesidad",
        "description": "La columna 'email' en 'clientes' es accesible por roles de solo reporte.",
        "evidence": "SELECT grantee FROM information_schema.role_column_grants WHERE column_name = 'email';",
        "recommendation": "Revocar permisos innecesarios y aplicar RLS.",
        "remediation_sql": "REVOKE SELECT ON clientes FROM reporting_user;",
        "regulation_refs": [
            {"framework": "LFPDPPP", "article": "Art. 19", "description": "Medidas de seguridad."},
            {"framework": "LFPDPPP", "article": "Art. 20", "description": "Confidencialidad."},
        ],
        "table_name": "clientes", "column_name": "email", "confidence_score": None,
    },
    {
        "id": "CFG-004", "module": "configuracion", "category": "extensiones",
        "severity": "MEDIUM", "title": "Extension dblink instalada sin uso aparente",
        "description": "La extension 'dblink' esta instalada pero no se usa en ninguna funcion activa.",
        "evidence": "SELECT * FROM pg_extension WHERE extname = 'dblink';",
        "recommendation": "Desinstalar extensiones no utilizadas.",
        "remediation_sql": "DROP EXTENSION IF EXISTS dblink;",
        "regulation_refs": [
            {"framework": "CIS", "article": "Benchmark 3.2", "description": "Remover extensiones innecesarias."},
        ],
        "table_name": None, "column_name": None, "confidence_score": None,
    },
]

if __name__ == "__main__":
    print("Generando reportes de prueba...")
    generate_executive_report(FAKE_FINDINGS)
    generate_technical_report(FAKE_FINDINGS)
    print("\nListo. Revisa la carpeta /output")
