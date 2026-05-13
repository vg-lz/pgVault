"""Escáner de configuración y postura de seguridad para PostgreSQL.

Este módulo detecta riesgos de seguridad en roles, privilegios, funciones,
configuración del servidor y reglas de autenticación de PostgreSQL.
"""

from __future__ import annotations

from pgvault.models import Finding, RegulationRef, Severity
from pgvault.modules import ScanContext


class ConfigurationScanner:
    """Escanea la configuración de PostgreSQL para detectar problemas de seguridad y cumplimiento."""

    name = "configuration"

    async def run(self, context: ScanContext) -> list[Finding]:
        """Ejecuta todas las verificaciones de seguridad de configuración y retorna hallazgos."""

        findings: list[Finding] = []

        # Regla 1: Detectar roles SUPERUSER innecesarios
        findings.extend(self._check_superuser_roles(context))

        # Regla 2: Detectar funciones SECURITY DEFINER sin search_path seguro
        findings.extend(self._check_security_definer_functions(context))

        # Regla 3: Detectar configuración de logging insegura
        findings.extend(self._check_logging_configuration(context))

        return findings

    def _check_superuser_roles(self, context: ScanContext) -> list[Finding]:
        """Detecta roles con privilegio SUPERUSER que pueden no necesitarlo."""

        findings: list[Finding] = []
        superusers = [
            role for role in context.snapshot.roles
            if role.is_superuser and role.role_name != "postgres"
        ]

        for role in superusers:
            findings.append(
                Finding(
                    id=f"CFG-001-{role.role_name}",
                    module=self.name,
                    category="roles_privileges",
                    title=f"Rol '{role.role_name}' tiene privilegio SUPERUSER innecesario",
                    description=(
                        f"El rol '{role.role_name}' tiene privilegio SUPERUSER, lo que otorga "
                        "acceso sin restricciones a toda la base de datos. Este privilegio debe "
                        "reservarse solo para tareas administrativas críticas."
                    ),
                    severity=Severity.HIGH,
                    evidence=f"SELECT rolname, rolsuper FROM pg_roles WHERE rolname = '{role.role_name}';",
                    recommendation=(
                        "Revocar SUPERUSER y otorgar solo los privilegios específicos necesarios. "
                        "Usar roles dedicados para distintas funciones operativas."
                    ),
                    remediation_sql=f"ALTER ROLE {role.role_name} NOSUPERUSER;",
                    regulation_refs=[
                        RegulationRef(
                            framework="PCI-DSS",
                            article="Req. 7",
                            description="Restringir acceso a componentes del sistema por necesidad del negocio.",
                        ),
                    ],
                )
            )

        return findings

    def _check_security_definer_functions(self, context: ScanContext) -> list[Finding]:
        """Detecta funciones SECURITY DEFINER sin configuración segura de search_path."""

        findings: list[Finding] = []
        
        # Las funciones SECURITY DEFINER son vulnerables a ataques de search_path
        # si no establecen explícitamente un search_path seguro
        security_definer_funcs = [
            func for func in context.snapshot.functions
            if func.security_definer
        ]

        for func in security_definer_funcs:
            findings.append(
                Finding(
                    id=f"CFG-002-{func.schema_name}-{func.function_name}",
                    module=self.name,
                    category="functions",
                    title=f"Función '{func.schema_name}.{func.function_name}' es SECURITY DEFINER sin search_path seguro",
                    description=(
                        f"La función '{func.schema_name}.{func.function_name}' se ejecuta con "
                        "privilegios del propietario (SECURITY DEFINER) pero puede no tener "
                        "un search_path explícito configurado, lo que la hace vulnerable a ataques "
                        "de inyección de objetos maliciosos en esquemas públicos."
                    ),
                    severity=Severity.CRITICAL,
                    evidence=(
                        f"SELECT proname, prosecdef FROM pg_proc "
                        f"WHERE proname = '{func.function_name}';"
                    ),
                    recommendation=(
                        "Configurar un search_path seguro y explícito para la función, "
                        "preferiblemente solo pg_catalog y el esquema de la función."
                    ),
                    remediation_sql=(
                        f"ALTER FUNCTION {func.schema_name}.{func.function_name}() "
                        f"SET search_path = pg_catalog, {func.schema_name};"
                    ),
                    regulation_refs=[
                        RegulationRef(
                            framework="OWASP",
                            article="A01:2021",
                            description="Broken Access Control - Escalación de privilegios.",
                        ),
                    ],
                    table_schema=func.schema_name,
                )
            )

        return findings

    def _check_logging_configuration(self, context: ScanContext) -> list[Finding]:
        """Detecta configuración de logging insegura o faltante."""

        findings: list[Finding] = []

        # Construir diccionario de configuraciones para acceso rápido
        settings = {s.name: s.setting for s in context.snapshot.settings}

        # Verificar log_connections
        log_connections = settings.get("log_connections", "off")
        if log_connections.lower() == "off":
            findings.append(
                Finding(
                    id="CFG-003-log-connections",
                    module=self.name,
                    category="logging",
                    title="Logging de conexiones está desactivado",
                    description=(
                        "El parámetro log_connections está en 'off', lo que significa que no se "
                        "registran las conexiones entrantes. Esto dificulta la auditoría y la "
                        "detección de accesos no autorizados."
                    ),
                    severity=Severity.HIGH,
                    evidence="SHOW log_connections;",
                    recommendation=(
                        "Activar log_connections para registrar todas las conexiones entrantes. "
                        "Esto es esencial para cumplimiento regulatorio y detección de incidentes."
                    ),
                    remediation_sql=(
                        "ALTER SYSTEM SET log_connections = 'on';\n"
                        "SELECT pg_reload_conf();"
                    ),
                    regulation_refs=[
                        RegulationRef(
                            framework="PCI-DSS",
                            article="Req. 10",
                            description="Registrar y monitorear todos los accesos a recursos del sistema.",
                        ),
                    ],
                )
            )

        # Verificar log_disconnections
        log_disconnections = settings.get("log_disconnections", "off")
        if log_disconnections.lower() == "off":
            findings.append(
                Finding(
                    id="CFG-004-log-disconnections",
                    module=self.name,
                    category="logging",
                    title="Logging de desconexiones está desactivado",
                    description=(
                        "El parámetro log_disconnections está en 'off'. Sin este registro, "
                        "es difícil correlacionar sesiones completas y detectar patrones anómalos."
                    ),
                    severity=Severity.MEDIUM,
                    evidence="SHOW log_disconnections;",
                    recommendation="Activar log_disconnections para tener trazabilidad completa de sesiones.",
                    remediation_sql=(
                        "ALTER SYSTEM SET log_disconnections = 'on';\n"
                        "SELECT pg_reload_conf();"
                    ),
                    regulation_refs=[
                        RegulationRef(
                            framework="PCI-DSS",
                            article="Req. 10",
                            description="Registrar y monitorear todos los accesos.",
                        ),
                    ],
                )
            )

        return findings
