"""Escáner de configuración y postura de seguridad para PostgreSQL.

Este módulo detecta riesgos de seguridad en roles, privilegios, funciones,
configuración del servidor y reglas de autenticación de PostgreSQL.
"""

from __future__ import annotations

from pgvault.db import quote_identifier
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

        # Regla 4: Detectar reglas pg_hba.conf inseguras (trust desde red)
        findings.extend(self._check_hba_trust_rules(context))

        # Regla 5: Detectar credenciales débiles por nombre de rol
        findings.extend(self._check_weak_credentials(context))

        # Regla 6: Detectar extensiones peligrosas instaladas
        findings.extend(self._check_dangerous_extensions(context))

        # Regla 7: Detectar roles sin contraseña configurada (requiere pg_authid)
        findings.extend(await self._check_no_password_roles(context))

        # Regla 8: Detectar archive_mode desactivado — sin PITR
        findings.extend(self._check_archive_mode(context))

        # Regla 9: Detectar privilegios excesivos sobre tablas PCI
        findings.extend(self._check_pci_table_grants(context))

        # Regla 10: Detectar grants SELECT a PUBLIC sobre tablas
        findings.extend(self._check_public_table_grants(context))

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
                    remediation_sql=f"ALTER ROLE {quote_identifier(role.role_name)} NOSUPERUSER;",
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
                    title=f"Función '{func.schema_name}.{func.function_name}' es SECURITY DEFINER - requiere verificación manual de search_path",
                    description=(
                        f"La función '{func.schema_name}.{func.function_name}' se ejecuta con "
                        "privilegios del propietario (SECURITY DEFINER). Este scanner NO puede verificar automáticamente "
                        "si tiene un search_path seguro configurado (requiere acceso a pg_proc.proconfig). "
                        "Se recomienda verificación manual para evitar ataques de inyección de objetos maliciosos."
                    ),
                    severity=Severity.MEDIUM,
                    evidence=(
                        f"SELECT proname, prosecdef FROM pg_proc "
                        f"WHERE proname = '{func.function_name}';"
                    ),
                    recommendation=(
                        "Configurar un search_path seguro y explícito para la función, "
                        "preferiblemente solo pg_catalog y el esquema de la función."
                    ),
                    remediation_sql=(
                        f"ALTER FUNCTION {quote_identifier(func.schema_name)}.{quote_identifier(func.function_name)}() "
                        f"SET search_path = pg_catalog, {quote_identifier(func.schema_name)};"
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

    def _check_hba_trust_rules(self, context: ScanContext) -> list[Finding]:
        """Detecta reglas pg_hba.conf con autenticación 'trust' desde redes externas."""

        findings: list[Finding] = []

        # Buscar reglas con método de autenticación 'trust'
        trust_rules = [
            rule for rule in context.snapshot.hba_rules
            if rule.auth_method and rule.auth_method.lower() == "trust"
        ]

        for rule in trust_rules:
            # Determinar si la regla permite acceso desde red (no local)
            is_network_rule = False
            address_display = "local"
            
            if rule.address:
                address_display = rule.address
                # Reglas peligrosas: 0.0.0.0/0, ::/0, o cualquier CIDR amplio
                if rule.address in ("0.0.0.0/0", "0.0.0.0", "::/0", "::") or \
                   rule.address.startswith("0.0.0.0") or \
                   (rule.address.startswith("::") and not rule.address == "::1"):
                    is_network_rule = True
            
            # Si no tiene address pero el tipo es 'host', también es red
            if rule.rule_type == "host" and not rule.address:
                is_network_rule = True

            # Determinar severidad basada en alcance
            severity = Severity.CRITICAL if is_network_rule else Severity.HIGH

            # Construir detalles de usuarios y bases afectadas
            users_str = ", ".join(rule.user) if rule.user else "todos"
            databases_str = ", ".join(rule.database) if rule.database else "todas"

            findings.append(
                Finding(
                    id=f"CFG-005-hba-line-{rule.line_number}" if rule.line_number else "CFG-005-hba-trust",
                    module=self.name,
                    category="authentication",
                    title=f"pg_hba.conf permite autenticación 'trust' desde {address_display}",
                    description=(
                        f"El archivo pg_hba.conf contiene una regla que permite autenticación sin contraseña "
                        f"(método 'trust') para usuarios '{users_str}' en bases '{databases_str}' "
                        f"desde '{address_display}'. Esto significa que cualquier conexión desde esa red "
                        f"puede acceder sin credenciales, representando un riesgo crítico de seguridad."
                    ),
                    severity=severity,
                    evidence=(
                        f"SELECT * FROM pg_hba_file_rules WHERE line_number = {rule.line_number};"
                        if rule.line_number else
                        "SELECT * FROM pg_hba_file_rules WHERE auth_method = 'trust';"
                    ),
                    recommendation=(
                        "Eliminar la línea de pg_hba.conf que permite 'trust'. "
                        "Usar métodos de autenticación seguros como 'scram-sha-256' o 'md5', "
                        "preferiblemente con SSL/TLS (hostssl en lugar de host)."
                    ),
                    remediation_sql=(
                        "-- Editar pg_hba.conf manualmente y reemplazar la línea:\n"
                        f"-- Línea {rule.line_number}: ... trust\n"
                        "-- Por:\n"
                        f"-- hostssl {databases_str} {users_str} {address_display if address_display != 'local' else '127.0.0.1/32'} scram-sha-256\n"
                        "-- Luego recargar configuración:\n"
                        "SELECT pg_reload_conf();"
                    ),
                    regulation_refs=[
                        RegulationRef(
                            framework="PCI-DSS",
                            article="Req. 8.2",
                            description="Asegurar autenticación de usuarios con credenciales únicas.",
                        ),
                        RegulationRef(
                            framework="OWASP",
                            article="A07:2021",
                            description="Identification and Authentication Failures.",
                        ),
                    ],
                )
            )

        return findings

    def _check_weak_credentials(self, context: ScanContext) -> list[Finding]:
        """Detecta roles con nombres que sugieren credenciales débiles o por defecto."""

        findings: list[Finding] = []

        # Lista de nombres de roles sospechosos comúnmente asociados con passwords débiles
        suspicious_role_names = {
            "admin", "administrator", "superadmin", "root", "sa",
            "test", "demo", "guest", "user", "default"
        }

        suspicious_roles = [
            role for role in context.snapshot.roles
            if role.role_name.lower() in suspicious_role_names and role.can_login
        ]

        for role in suspicious_roles:
            findings.append(
                Finding(
                    id=f"CFG-006-{role.role_name}",
                    module=self.name,
                    category="credentials",
                    title=f"Rol '{role.role_name}' tiene nombre sospechoso asociado con credenciales débiles",
                    description=(
                        f"El rol '{role.role_name}' utiliza un nombre común que frecuentemente se asocia "
                        "con contraseñas débiles o por defecto (admin/admin, admin/admin123, etc.). "
                        "Estos roles son objetivos principales de ataques de fuerza bruta y diccionario."
                    ),
                    severity=Severity.HIGH,
                    evidence=f"SELECT rolname, rolcanlogin FROM pg_roles WHERE rolname = '{role.role_name}';",
                    recommendation=(
                        "Implementar política de contraseñas robustas: mínimo 12 caracteres, combinación de "
                        "mayúsculas, minúsculas, números y símbolos. Considerar renombrar el rol a un nombre "
                        "menos obvio y forzar reset de contraseña inmediato. Activar autenticación de dos factores "
                        "si está disponible."
                    ),
                    remediation_sql=(
                        f"-- Forzar cambio de contraseña para '{role.role_name}':\n"
                        f"ALTER ROLE {quote_identifier(role.role_name)} PASSWORD 'nueva_contraseña_robusta';\n"
                        "-- Considerar renombrar el rol:\n"
                        f"ALTER ROLE {quote_identifier(role.role_name)} RENAME TO {quote_identifier(role.role_name + '_produccion')};"
                    ),
                    regulation_refs=[
                        RegulationRef(
                            framework="PCI-DSS",
                            article="Req. 8.2.3",
                            description="Las contraseñas deben cumplir requisitos mínimos de complejidad.",
                        ),
                        RegulationRef(
                            framework="OWASP",
                            article="A07:2021",
                            description="Identification and Authentication Failures - Credenciales débiles.",
                        ),
                    ],
                )
            )

        return findings

    def _check_dangerous_extensions(self, context: ScanContext) -> list[Finding]:
        """Detecta extensiones de PostgreSQL que aumentan la superficie de ataque."""

        findings: list[Finding] = []

        # Extensiones consideradas peligrosas si no se usan con cuidado
        dangerous_extensions = {
            "dblink": (
                "dblink permite conexiones a otras bases de datos y puede ser usada para "
                "escalación de privilegios, exfiltración de datos o ataques de pivoteo."
            ),
            "pg_read_server_files": (
                "pg_read_server_files permite leer archivos del servidor, lo que puede exponer "
                "configuraciones sensibles, logs o datos del sistema operativo."
            ),
            "file_fdw": (
                "file_fdw permite acceso directo al sistema de archivos del servidor y puede "
                "ser usado para leer o escribir archivos sensibles."
            ),
        }

        installed_dangerous = [
            ext for ext in context.snapshot.extensions
            if ext.name in dangerous_extensions
        ]

        for ext in installed_dangerous:
            findings.append(
                Finding(
                    id=f"CFG-007-ext-{ext.name}",
                    module=self.name,
                    category="extensions",
                    title=f"Extensión '{ext.name}' instalada representa riesgo de seguridad",
                    description=(
                        f"La extensión '{ext.name}' está instalada en el servidor. "
                        f"{dangerous_extensions[ext.name]} "
                        "Si esta extensión no se utiliza activamente, debe eliminarse para reducir "
                        "la superficie de ataque."
                    ),
                    severity=Severity.MEDIUM,
                    evidence=f"SELECT extname, extversion FROM pg_extension WHERE extname = '{ext.name}';",
                    recommendation=(
                        f"Verificar si la extensión '{ext.name}' es realmente necesaria. Si no se usa, "
                        "eliminarla inmediatamente. Si se requiere, documentar su uso y restringir acceso "
                        "solo a roles administrativos de confianza."
                    ),
                    remediation_sql=(
                        f"-- Si no se necesita, eliminar la extensión:\n"
                        f"DROP EXTENSION IF EXISTS {quote_identifier(ext.name)};\n"
                        "-- Si se necesita, restringir privilegios:\n"
                        f"REVOKE ALL ON EXTENSION {quote_identifier(ext.name)} FROM PUBLIC;"
                    ),
                    regulation_refs=[
                        RegulationRef(
                            framework="CIS PostgreSQL Benchmark",
                            article="2.3",
                            description="Minimizar extensiones instaladas para reducir superficie de ataque.",
                        ),
                    ],
                )
            )

        return findings

    async def _check_no_password_roles(self, context: ScanContext) -> list[Finding]:
        """Detecta roles con can_login pero sin contraseña configurada (pg_authid)."""

        findings: list[Finding] = []

        try:
            rows = await context.db.fetch(
                "SELECT rolname FROM pg_catalog.pg_authid "
                "WHERE rolpassword IS NULL AND rolcanlogin = true;"
            )
            for row in rows:
                role_name = row["rolname"]
                findings.append(
                    Finding(
                        id=f"CFG-008-{role_name}",
                        module=self.name,
                        category="credentials",
                        title=f"Rol '{role_name}' no tiene contraseña configurada",
                        description=(
                            f"El rol '{role_name}' puede iniciar sesión pero no tiene contraseña "
                            "configurada (pg_authid.rolpassword IS NULL). Cualquier cliente que "
                            "pueda conectarse como este rol se autenticará sin credenciales, "
                            "dependiendo únicamente de las reglas de pg_hba.conf."
                        ),
                        severity=Severity.HIGH,
                        evidence=(
                            "SELECT rolname FROM pg_catalog.pg_authid "
                            "WHERE rolpassword IS NULL AND rolcanlogin = true;"
                        ),
                        recommendation=(
                            f"Asignar una contraseña robusta al rol '{role_name}' o eliminarlo si no se usa. "
                            "Asegurarse también de que pg_hba.conf no permita 'trust' para este rol."
                        ),
                        remediation_sql=(
                            f"-- Asignar contraseña robusta:\n"
                            f"ALTER ROLE {quote_identifier(role_name)} PASSWORD 'contraseña_robusta_aqui';\n"
                            f"-- O si el rol no se usa, eliminarlo:\n"
                            f"DROP ROLE IF EXISTS {quote_identifier(role_name)};"
                        ),
                        regulation_refs=[
                            RegulationRef(
                                framework="PCI-DSS",
                                article="Req. 8.2.1",
                                description="Todos los usuarios deben tener credenciales de autenticación.",
                            ),
                            RegulationRef(
                                framework="OWASP",
                                article="A07:2021",
                                description="Identification and Authentication Failures - cuenta sin contraseña.",
                            ),
                        ],
                    )
                )
        except Exception:
            # pg_authid puede no ser accesible con este usuario — omitir check
            pass

        return findings

    def _check_archive_mode(self, context: ScanContext) -> list[Finding]:
        """Detecta archive_mode desactivado — sin capacidad de Point-In-Time Recovery."""

        findings: list[Finding] = []
        settings = {s.name: s.setting for s in context.snapshot.settings}

        archive_mode = settings.get("archive_mode", "on")  # si no está en el snapshot, asumir on
        if archive_mode.lower() == "off":
            findings.append(
                Finding(
                    id="CFG-009-archive-mode",
                    module=self.name,
                    category="backup",
                    title="archive_mode desactivado — sin Point-In-Time Recovery (PITR)",
                    description=(
                        "El parámetro archive_mode está en 'off'. Sin WAL archiving activo, "
                        "no es posible realizar Point-In-Time Recovery (PITR) ante corrupción "
                        "de datos o desastre. Solo están disponibles backups base, lo que puede "
                        "representar pérdida significativa de datos entre backups."
                    ),
                    severity=Severity.HIGH,
                    evidence="SHOW archive_mode;",
                    recommendation=(
                        "Activar archive_mode con archive_command apropiado para habilitar PITR. "
                        "Documentar la estrategia de backup y retención según regulación aplicable."
                    ),
                    remediation_sql=(
                        "-- Requiere reinicio del servidor PostgreSQL:\n"
                        "ALTER SYSTEM SET archive_mode = 'on';\n"
                        "ALTER SYSTEM SET archive_command = 'cp %p /ruta/wal_archive/%f';\n"
                        "-- Luego reiniciar PostgreSQL para aplicar cambios."
                    ),
                    regulation_refs=[
                        RegulationRef(
                            framework="ISO 27001",
                            article="A.12.3",
                            description="Backup de información — continuidad de negocio.",
                        ),
                        RegulationRef(
                            framework="CNBV",
                            description="Resguardo y recuperación de información financiera.",
                        ),
                    ],
                )
            )

        return findings

    def _check_pci_table_grants(self, context: ScanContext) -> list[Finding]:
        """Detecta roles con SELECT sobre tablas de ámbito PCI (tarjetas, pagos)."""

        findings: list[Finding] = []

        # Tablas cuyo nombre sugiere datos de tarjetas de pago (PCI-DSS scope)
        pci_table_names = frozenset({
            "cards", "credit_cards", "debit_cards", "card_data",
            "payments", "card_transactions", "pan_data",
        })

        # Excluir superusers del reporte (tienen acceso legítimo por naturaleza de su rol)
        superusers = {r.role_name for r in context.snapshot.roles if r.is_superuser}

        for priv in context.snapshot.privileges:
            if (
                priv.object_type == "table"
                and priv.object_name in pci_table_names
                and priv.privilege_type == "SELECT"
                and priv.grantee not in superusers
                and priv.grantee != "PUBLIC"  # PUBLIC se cubre en CFG-011
            ):
                findings.append(
                    Finding(
                        id=f"CFG-010-{priv.object_schema}-{priv.object_name}-{priv.grantee}",
                        module=self.name,
                        category="privileges",
                        title=f"Rol '{priv.grantee}' tiene SELECT sobre tabla PCI '{priv.object_name}'",
                        description=(
                            f"El rol '{priv.grantee}' tiene privilegio SELECT sobre "
                            f"'{priv.object_schema}.{priv.object_name}', que contiene o puede contener "
                            "datos de tarjetas de pago (PANs, CVVs, etc.). Esto viola el principio "
                            "de mínimo privilegio de PCI-DSS y puede exponer datos de titulares de tarjetas."
                        ),
                        severity=Severity.CRITICAL,
                        evidence=(
                            "SELECT grantee, privilege_type "
                            "FROM information_schema.role_table_grants "
                            f"WHERE table_name = '{priv.object_name}';"
                        ),
                        recommendation=(
                            f"Revocar SELECT de '{priv.grantee}' sobre '{priv.object_name}'. "
                            "Solo roles del procesamiento de pagos deben tener acceso. "
                            "Considerar crear vistas enmascaradas (solo últimos 4 dígitos) para reportes."
                        ),
                        remediation_sql=(
                            f"REVOKE SELECT ON "
                            f"{quote_identifier(priv.object_schema)}.{quote_identifier(priv.object_name)} "
                            f"FROM {quote_identifier(priv.grantee)};"
                        ),
                        regulation_refs=[
                            RegulationRef(
                                framework="PCI-DSS",
                                article="Req. 3",
                                description="Protect stored cardholder data.",
                            ),
                            RegulationRef(
                                framework="PCI-DSS",
                                article="Req. 7",
                                description="Restrict access to system components and cardholder data.",
                            ),
                        ],
                        table_schema=priv.object_schema,
                        table_name=priv.object_name,
                    )
                )

        return findings

    def _check_public_table_grants(self, context: ScanContext) -> list[Finding]:
        """Detecta tablas con privilegios SELECT otorgados al rol PUBLIC."""

        findings: list[Finding] = []

        for priv in context.snapshot.privileges:
            if (
                priv.object_type == "table"
                and priv.grantee == "PUBLIC"
                and priv.privilege_type == "SELECT"
            ):
                findings.append(
                    Finding(
                        id=f"CFG-011-public-{priv.object_schema}-{priv.object_name}",
                        module=self.name,
                        category="privileges",
                        title=f"Tabla '{priv.object_name}' tiene SELECT otorgado a PUBLIC",
                        description=(
                            f"La tabla '{priv.object_schema}.{priv.object_name}' tiene SELECT "
                            "otorgado al rol PUBLIC, lo que significa que TODOS los roles actuales "
                            "y futuros pueden leer su contenido sin GRANT explícito. Si contiene "
                            "datos personales o sensibles, esto viola LFPDPPP y otros marcos regulatorios."
                        ),
                        severity=Severity.HIGH,
                        evidence=(
                            "SELECT grantee, privilege_type "
                            "FROM information_schema.role_table_grants "
                            f"WHERE table_name = '{priv.object_name}' AND grantee = 'PUBLIC';"
                        ),
                        recommendation=(
                            f"Revocar SELECT de PUBLIC sobre '{priv.object_name}'. "
                            "Otorgar acceso solo a los roles específicos que realmente lo necesitan."
                        ),
                        remediation_sql=(
                            f"REVOKE SELECT ON "
                            f"{quote_identifier(priv.object_schema)}.{quote_identifier(priv.object_name)} "
                            f"FROM PUBLIC;"
                        ),
                        regulation_refs=[
                            RegulationRef(
                                framework="LFPDPPP",
                                description="Principio de información mínima — datos personales.",
                            ),
                            RegulationRef(
                                framework="PCI-DSS",
                                article="Req. 7",
                                description="Restrict access by need to know.",
                            ),
                        ],
                        table_schema=priv.object_schema,
                        table_name=priv.object_name,
                    )
                )

        return findings

