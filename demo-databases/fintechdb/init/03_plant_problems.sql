-- =====================================================================
-- FintechDB v1.0 — Planted Problems
-- =====================================================================
-- This script plants 22 problems intentionally for the PgVault project.
-- Each problem is marked with its ID (H01-H22) for evaluation.
--
-- DO NOT share this file with students. The master list is in
-- /docs/HALLAZGOS_v1.md (instructor only).
-- =====================================================================

SET client_min_messages = WARNING;

-- =====================================================================
-- MODULE 1: CONFIGURATION AND SECURITY POSTURE (10 problems)
-- =====================================================================

-- ---------------------------------------------------------------------
-- AUTHENTICATION AND CONNECTIONS (H01-H03)
-- ---------------------------------------------------------------------

-- H01: User 'admin' with weak password
-- Already created in 02_seed_data.sql with password 'admin123'
-- Verify it exists at PG role level too
DO $$
BEGIN
    -- Create matching PG role with weak password
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'admin') THEN
        CREATE ROLE admin WITH LOGIN PASSWORD 'admin123';
    END IF;
END $$;

-- H02: User 'app_legacy' without password (will rely on trust auth in pg_hba)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_legacy') THEN
        CREATE ROLE app_legacy WITH LOGIN;  -- NO PASSWORD
    END IF;
END $$;

-- H03: pg_hba.conf permits trust from 0.0.0.0/0 for app_legacy
-- (configured externally via pg_hba.conf mounted in docker-compose)


-- ---------------------------------------------------------------------
-- ROLES AND PRIVILEGES (H04-H06)
-- ---------------------------------------------------------------------

-- H04: Role 'analyst_user' with SUPERUSER (unnecessary)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'analyst_user') THEN
        CREATE ROLE analyst_user WITH LOGIN SUPERUSER PASSWORD 'analyst_pass';
    ELSE
        ALTER ROLE analyst_user WITH SUPERUSER;
    END IF;
END $$;

-- H05: Role 'reports_user' with SELECT on cards table (PCI violation)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'reports_user') THEN
        CREATE ROLE reports_user WITH LOGIN PASSWORD 'reports_pass';
    END IF;
END $$;
GRANT SELECT ON cards TO reports_user;

-- H06: PUBLIC has SELECT on customers (any new role inherits PII access)
GRANT SELECT ON customers TO PUBLIC;


-- ---------------------------------------------------------------------
-- DANGEROUS FUNCTIONS (H07)
-- ---------------------------------------------------------------------

-- H07: SECURITY DEFINER function with mutable search_path
-- Vulnerable to search_path injection attack
CREATE OR REPLACE FUNCTION get_customer_full_data(cust_id INTEGER)
RETURNS TABLE (
    id INTEGER,
    full_name VARCHAR,
    rfc VARCHAR,
    curp VARCHAR,
    email VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT c.id, c.full_name, c.rfc, c.curp, c.email
    FROM customers c
    WHERE c.id = cust_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
-- NOTE: NO 'SET search_path' is the vulnerability.
-- A malicious schema with shadowed `customers` could be injected.

-- Allow any role to execute it (worsens the issue)
GRANT EXECUTE ON FUNCTION get_customer_full_data(INTEGER) TO PUBLIC;


-- ---------------------------------------------------------------------
-- SERVER CONFIGURATION (H08-H09)
-- ---------------------------------------------------------------------

-- H08: log_statement='none' and log_connections=off
-- (configured externally in postgresql.conf)

-- H09: dblink extension installed without apparent use
CREATE EXTENSION IF NOT EXISTS dblink;


-- ---------------------------------------------------------------------
-- BACKUPS (H10) — Option B: archive_mode = off in config
-- ---------------------------------------------------------------------
-- (configured externally in postgresql.conf via archive_mode=off)


-- =====================================================================
-- MODULE 2: SENSITIVE DATA DISCOVERY (9 problems)
-- =====================================================================
-- H11-H19 are planted by virtue of the schema and seed data:
--   H11: customers.rfc       (regex-detectable by name)
--   H12: customers.curp      (regex-detectable by name)
--   H13: customers.email     (regex-detectable by name)
--   H14: cards.pan           (regex-detectable by name + content)
--   H15: cards.cvv           (regex-detectable by name + critical PCI)
--   H16: internal_users.password_plain (regex-detectable: 'password' in name)
--   H17: customer_notes.body contains synthetic CURPs (content sampling)
--   H18: audit_log.details JSONB has 'exported_email' and 'exported_pan_last4'
--   H19: merchants.bank_account contains CLABE numbers (content sampling)
--
-- All planted in 02_seed_data.sql. No additional setup needed here.


-- =====================================================================
-- MODULE 3: COMPLIANCE AND AUDIT (3 problems)
-- =====================================================================

-- ---------------------------------------------------------------------
-- H20: cards table has NO audit trigger and NO history table
-- (a compliant system should track all access/changes to cards)
-- ---------------------------------------------------------------------
-- Nothing to plant; the absence IS the problem.
-- Detector should:
--   1. Identify cards as containing sensitive data (from H14, H15)
--   2. Verify if there is any trigger on cards that writes to audit
--   3. Verify if there is a history table (cards_history, etc.)
-- All checks should fail, indicating no audit coverage.

-- ---------------------------------------------------------------------
-- H21: audit_log is NOT append-only
-- Anyone with UPDATE privileges can modify historical records
-- ---------------------------------------------------------------------
-- Default behavior: no append-only protection.
-- A compliant audit_log should:
--   - Use REVOKE UPDATE, DELETE FROM PUBLIC
--   - Or have a BEFORE UPDATE trigger that raises exception
-- We grant UPDATE to PUBLIC to make the issue more obvious
GRANT INSERT, SELECT, UPDATE, DELETE ON audit_log TO PUBLIC;
GRANT USAGE ON SEQUENCE audit_log_id_seq TO PUBLIC;

-- ---------------------------------------------------------------------
-- H22: audit_log has no retention policy and contains data 3+ years old
-- ---------------------------------------------------------------------
-- Insert some very old audit entries to demonstrate lack of retention
INSERT INTO audit_log (actor_id, actor_type, action, target_table, target_id, details, ip_address, created_at)
SELECT
    1 + (i % 25),
    'internal_user',
    'view',
    'customers',
    1 + (i % 5000),
    jsonb_build_object('legacy', true, 'note', 'old audit entry'),
    '127.0.0.1'::inet,
    NOW() - INTERVAL '3 years' - (random() * 365 || ' days')::interval
FROM generate_series(1, 1000) i;


-- =====================================================================
-- Final touches
-- =====================================================================
-- Re-analyze tables that grew
ANALYZE audit_log;

-- Summary message
DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'FintechDB v1.0 ready with 22 planted problems';
    RAISE NOTICE 'Master list: /docs/HALLAZGOS_v1.md (instructor only)';
    RAISE NOTICE 'WARNING: This DB contains intentional security flaws';
    RAISE NOTICE '========================================';
END $$;
