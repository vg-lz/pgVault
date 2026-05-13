-- =====================================================================
-- FintechDB v1.0 — Seed data (BASE mode)
-- ~80 MB, levanta en ~1-2 min
-- For LARGE mode, see scripts/scale_to_large.sql
-- =====================================================================
-- All RFCs, CURPs, card numbers and CVVs are SYNTHETIC.
-- They follow valid format/regex but DO NOT correspond to real persons.
-- =====================================================================

SET client_min_messages = WARNING;

-- =====================================================================
-- Helper functions for synthetic Mexican PII
-- =====================================================================

-- Generate a synthetic RFC (4 letters + 6 digits + 3 alphanum)
-- Format: XXXX######XXX
CREATE OR REPLACE FUNCTION gen_synthetic_rfc(seed INTEGER) RETURNS VARCHAR AS $$
DECLARE
    letters CHAR(26) := 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
    alphanum CHAR(36) := 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
    result VARCHAR := '';
    i INTEGER;
BEGIN
    -- 4 letters
    FOR i IN 0..3 LOOP
        result := result || substring(letters, 1 + ((seed * (i+1)) % 26)::int, 1);
    END LOOP;
    -- 6 digits (date-like: YYMMDD)
    result := result || lpad(((seed * 7) % 999999)::text, 6, '0');
    -- 3 alphanum
    FOR i IN 0..2 LOOP
        result := result || substring(alphanum, 1 + ((seed * (i+5)) % 36)::int, 1);
    END LOOP;
    RETURN result;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Generate a synthetic CURP (4 letters + 6 digits + H/M + 5 letters + 2 alphanum)
-- Format: XXXX######HXXXXX##
CREATE OR REPLACE FUNCTION gen_synthetic_curp(seed INTEGER) RETURNS VARCHAR AS $$
DECLARE
    letters CHAR(26) := 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
    alphanum CHAR(36) := 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
    result VARCHAR := '';
    i INTEGER;
BEGIN
    -- 4 letters
    FOR i IN 0..3 LOOP
        result := result || substring(letters, 1 + ((seed * (i+1) + 3) % 26)::int, 1);
    END LOOP;
    -- 6 digits
    result := result || lpad(((seed * 11 + 100000) % 999999)::text, 6, '0');
    -- 1 letter (gender H/M)
    result := result || CASE WHEN seed % 2 = 0 THEN 'H' ELSE 'M' END;
    -- 5 letters
    FOR i IN 0..4 LOOP
        result := result || substring(letters, 1 + ((seed * (i+7)) % 26)::int, 1);
    END LOOP;
    -- 2 alphanum
    FOR i IN 0..1 LOOP
        result := result || substring(alphanum, 1 + ((seed * (i+13)) % 36)::int, 1);
    END LOOP;
    RETURN result;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Generate a synthetic PAN (16 digits, Luhn-valid)
-- Starts with 4 (Visa) or 5 (Mastercard)
CREATE OR REPLACE FUNCTION gen_synthetic_pan(seed INTEGER) RETURNS VARCHAR AS $$
DECLARE
    base15 VARCHAR;
    sum_total INTEGER := 0;
    i INTEGER;
    digit INTEGER;
    check_digit INTEGER;
BEGIN
    -- 15 digits: 1 prefix + 14 random-ish
    IF seed % 2 = 0 THEN
        base15 := '4' || lpad(((seed * 13 + 1234567) % 99999999999999)::text, 14, '0');
    ELSE
        base15 := '5' || lpad(((seed * 17 + 7654321) % 99999999999999)::text, 14, '0');
    END IF;

    -- Calculate Luhn check digit
    FOR i IN 0..14 LOOP
        digit := substring(base15, 15 - i, 1)::int;
        IF i % 2 = 0 THEN
            digit := digit * 2;
            IF digit > 9 THEN digit := digit - 9; END IF;
        END IF;
        sum_total := sum_total + digit;
    END LOOP;

    check_digit := (10 - (sum_total % 10)) % 10;

    RETURN base15 || check_digit::text;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Generate a synthetic CLABE (18 digits)
CREATE OR REPLACE FUNCTION gen_synthetic_clabe(seed INTEGER) RETURNS VARCHAR AS $$
BEGIN
    RETURN lpad((((seed * 31 + 100000) % 999) || lpad((seed * 41 % 999999999999999)::text, 15, '0'))::text, 18, '0');
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- =====================================================================
-- internal_users: 25 users (admins, operators)
-- =====================================================================
INSERT INTO internal_users (username, full_name, email, password_plain, role, last_login, created_at)
VALUES
    ('admin', 'System Administrator', 'admin@fintechmx.com', 'admin123', 'admin', NOW() - INTERVAL '1 day', NOW() - INTERVAL '2 years'),
    ('superadmin', 'Super Administrator', 'superadmin@fintechmx.com', 'P@ssw0rd2024', 'admin', NOW() - INTERVAL '3 hours', NOW() - INTERVAL '2 years'),
    ('operator1', 'Maria Lopez', 'maria.lopez@fintechmx.com', 'maria2024', 'operator', NOW() - INTERVAL '2 hours', NOW() - INTERVAL '1 year'),
    ('operator2', 'Juan Garcia', 'juan.garcia@fintechmx.com', 'juangg2024', 'operator', NOW() - INTERVAL '1 day', NOW() - INTERVAL '1 year'),
    ('support1', 'Ana Martinez', 'ana.martinez@fintechmx.com', 'anita123', 'support', NOW() - INTERVAL '5 hours', NOW() - INTERVAL '8 months'),
    ('analyst', 'Carlos Ramirez', 'carlos.ramirez@fintechmx.com', 'analyst99', 'analyst', NOW() - INTERVAL '2 days', NOW() - INTERVAL '6 months');

-- 19 more synthetic operators
INSERT INTO internal_users (username, full_name, email, password_plain, role, last_login, created_at)
SELECT
    'user' || i,
    'Internal User ' || i,
    'user' || i || '@fintechmx.com',
    'pass' || i || '!23',
    (ARRAY['operator', 'support', 'viewer', 'analyst'])[1 + (i % 4)],
    NOW() - (random() * 30 || ' days')::interval,
    NOW() - (random() * 730 || ' days')::interval
FROM generate_series(7, 25) i;

-- =====================================================================
-- customers: 5K customers with synthetic PII
-- =====================================================================
INSERT INTO customers (full_name, rfc, curp, email, phone, birth_date, address, city, state, country, risk_score, is_active, created_at)
SELECT
    (ARRAY['Maria', 'Juan', 'Ana', 'Carlos', 'Luis', 'Sofia', 'Diego', 'Laura', 'Miguel', 'Elena'])[1 + (i % 10)] || ' ' ||
    (ARRAY['Garcia', 'Lopez', 'Martinez', 'Ramirez', 'Torres', 'Flores', 'Hernandez', 'Sanchez', 'Diaz', 'Cruz'])[1 + ((i / 10) % 10)] || ' ' ||
    (ARRAY['Vazquez', 'Morales', 'Castillo', 'Jimenez', 'Mendoza', 'Ruiz', 'Aguilar', 'Ortiz', 'Reyes', 'Romero'])[1 + ((i / 100) % 10)],
    gen_synthetic_rfc(i),
    gen_synthetic_curp(i),
    'customer' || i || '@example.com',
    '+52' || (5500000000 + i)::text,
    DATE '1960-01-01' + (random() * 20000)::int,
    'Calle ' || (random() * 1000)::int || ' #' || (random() * 999)::int,
    (ARRAY['Mexico City', 'Guadalajara', 'Monterrey', 'Queretaro', 'Puebla', 'Tijuana', 'Merida', 'Cancun'])[1 + (i % 8)],
    (ARRAY['CDMX', 'JAL', 'NL', 'QRO', 'PUE', 'BC', 'YUC', 'QROO'])[1 + (i % 8)],
    'MX',
    (random() * 100)::int,
    CASE WHEN i % 50 = 0 THEN FALSE ELSE TRUE END,
    NOW() - (random() * 730 || ' days')::interval
FROM generate_series(1, 5000) i;

-- =====================================================================
-- merchants: 200 merchants with CLABE in bank_account (H19)
-- =====================================================================
INSERT INTO merchants (legal_name, trade_name, rfc, mcc, bank_account, contact_email, onboarded_at, is_active)
SELECT
    'Empresa ' || i || ' S.A. de C.V.',
    'Brand ' || i,
    gen_synthetic_rfc(i + 100000),
    lpad(((4000 + (random() * 5000)::int))::text, 4, '0'),
    gen_synthetic_clabe(i),                          -- H19: CLABE in generic-named col
    'contact@empresa' || i || '.com.mx',
    NOW() - (random() * 1095 || ' days')::interval,
    CASE WHEN i % 30 = 0 THEN FALSE ELSE TRUE END
FROM generate_series(1, 200) i;

-- =====================================================================
-- accounts: 3K bank accounts
-- =====================================================================
INSERT INTO accounts (customer_id, account_number, bank_code, account_type, balance, currency, is_active, created_at)
SELECT
    1 + (i % 5000),
    lpad((random() * 99999999999999999)::bigint::text, 16, '0'),
    (ARRAY['BBVA', 'BANAMEX', 'SANTANDER', 'BANORTE', 'HSBC'])[1 + (i % 5)],
    (ARRAY['savings', 'checking', 'investment'])[1 + (i % 3)],
    (random() * 1000000)::numeric(14, 2),
    'MXN',
    CASE WHEN i % 40 = 0 THEN FALSE ELSE TRUE END,
    NOW() - (random() * 730 || ' days')::interval
FROM generate_series(1, 3000) i;

-- =====================================================================
-- cards: 8K cards with synthetic PANs and CVVs (H14, H15)
-- =====================================================================
INSERT INTO cards (customer_id, pan, cvv, cardholder_name, expiration_date, card_brand, is_active, created_at)
SELECT
    1 + (i % 5000),
    gen_synthetic_pan(i),                            -- H14: full PAN stored
    lpad((random() * 999)::int::text, 3, '0'),       -- H15: CVV stored (PROHIBITED)
    'CARDHOLDER ' || i,
    lpad((1 + (random() * 11)::int)::text, 2, '0') || '/' || (2026 + (random() * 5)::int)::text,
    (ARRAY['visa', 'mastercard', 'amex', 'visa', 'mastercard'])[1 + (i % 5)],
    CASE WHEN i % 25 = 0 THEN FALSE ELSE TRUE END,
    NOW() - (random() * 730 || ' days')::interval
FROM generate_series(1, 8000) i;

-- =====================================================================
-- transactions: 100K authorization attempts
-- =====================================================================
INSERT INTO transactions (merchant_id, customer_id, card_id, amount, currency, auth_code, status, decline_reason, transaction_at, response_time_ms)
SELECT
    1 + (random() * 199)::int,
    1 + (random() * 4999)::int,
    1 + (random() * 7999)::int,
    (random() * 5000 + 50)::numeric(12, 2),
    'MXN',
    upper(substring(md5(random()::text), 1, 8)),
    CASE
        WHEN random() < 0.85 THEN 'approved'
        WHEN random() < 0.95 THEN 'declined'
        ELSE 'pending'
    END,
    CASE WHEN random() < 0.10 THEN
        (ARRAY['insufficient_funds', 'expired_card', 'invalid_cvv', 'fraud_suspected', 'limit_exceeded'])[1 + (random() * 4)::int]
    ELSE NULL END,
    NOW() - (random() * 730 || ' days')::interval,
    (50 + random() * 2000)::int
FROM generate_series(1, 100000) i;

-- =====================================================================
-- payments: 80K completed payments
-- =====================================================================
INSERT INTO payments (transaction_id, merchant_id, amount, fee, settlement_date, status, created_at)
SELECT
    t.id,
    t.merchant_id,
    t.amount,
    (t.amount * 0.029 + 3)::numeric(8, 2),
    (t.transaction_at + INTERVAL '1 day')::date,
    'settled',
    t.transaction_at + INTERVAL '1 day'
FROM transactions t
WHERE t.status = 'approved'
LIMIT 80000;

-- =====================================================================
-- kyc_documents: 5K documents
-- =====================================================================
INSERT INTO kyc_documents (customer_id, doc_type, doc_number, issued_date, expires_date, storage_url, verified_at, verified_by, created_at)
SELECT
    1 + (i % 5000),
    (ARRAY['INE', 'passport', 'address_proof', 'tax_certificate'])[1 + (i % 4)],
    'DOC-' || lpad(i::text, 8, '0'),
    DATE '2015-01-01' + (random() * 3000)::int,
    DATE '2025-01-01' + (random() * 1500)::int,
    'https://kyc-storage.fintechmx.com/docs/' || i || '.pdf',
    NOW() - (random() * 365 || ' days')::interval,
    1 + (random() * 24)::int,
    NOW() - (random() * 730 || ' days')::interval
FROM generate_series(1, 5000) i;

-- =====================================================================
-- customer_notes: 30K notes (some contain hidden CURPs - H17)
-- =====================================================================
-- Most notes are normal
INSERT INTO customer_notes (customer_id, author_id, body, note_type, created_at)
SELECT
    1 + (i % 5000),
    1 + (i % 25),
    (ARRAY[
        'Customer called regarding account balance.',
        'Verified identity via phone call.',
        'Customer requested account update.',
        'Reviewed transaction history with customer.',
        'Customer satisfied with resolution.',
        'Escalated to supervisor for review.',
        'Sent verification email to customer.',
        'Customer reported card lost, blocking issued.',
        'Updated customer contact information.',
        'Reviewed compliance documentation.'
    ])[1 + (i % 10)],
    (ARRAY['call', 'email', 'chat', 'in_person'])[1 + (i % 4)],
    NOW() - (random() * 730 || ' days')::interval
FROM generate_series(1, 27000) i;

-- ~10% of notes contain hidden CURPs/RFCs in free text (H17)
INSERT INTO customer_notes (customer_id, author_id, body, note_type, created_at)
SELECT
    1 + (i % 5000),
    1 + (i % 25),
    'Customer provided ID for verification. CURP: ' || gen_synthetic_curp(i + 50000) ||
    '. Cross-referenced with our records. Status: confirmed.',
    'verification',
    NOW() - (random() * 365 || ' days')::interval
FROM generate_series(1, 2000) i;

INSERT INTO customer_notes (customer_id, author_id, body, note_type, created_at)
SELECT
    1 + (i % 5000),
    1 + (i % 25),
    'Tax info update for invoice processing. RFC: ' || gen_synthetic_rfc(i + 60000) ||
    '. Updated in fiscal records.',
    'tax_update',
    NOW() - (random() * 365 || ' days')::interval
FROM generate_series(1, 1000) i;

-- =====================================================================
-- audit_log: 50K entries with PII in JSONB (H18)
-- =====================================================================

-- Most audit entries are normal
INSERT INTO audit_log (actor_id, actor_type, action, target_table, target_id, details, ip_address, created_at)
SELECT
    1 + (i % 25),
    'internal_user',
    (ARRAY['view', 'update', 'create', 'delete', 'login', 'logout', 'export'])[1 + (i % 7)],
    (ARRAY['customers', 'cards', 'transactions', 'payments', 'merchants'])[1 + (i % 5)],
    1 + (random() * 5000)::int,
    jsonb_build_object('ip', '192.168.' || (random() * 255)::int || '.' || (random() * 255)::int,
                       'session_id', md5(random()::text),
                       'duration_ms', (random() * 5000)::int),
    ('192.168.' || (random() * 255)::int || '.' || (random() * 255)::int)::inet,
    NOW() - (random() * 1095 || ' days')::interval        -- some entries 3 years old
FROM generate_series(1, 45000) i;

-- ~10% of audit entries contain PII in details (H18)
INSERT INTO audit_log (actor_id, actor_type, action, target_table, target_id, details, ip_address, created_at)
SELECT
    1 + (i % 25),
    'internal_user',
    'customer_data_export',
    'customers',
    1 + (i % 5000),
    jsonb_build_object(
        'exported_email', 'customer' || i || '@example.com',
        'exported_pan_last4', lpad((random() * 9999)::int::text, 4, '0'),
        'reason', 'compliance_audit',
        'session_id', md5(random()::text)
    ),
    ('10.0.' || (random() * 255)::int || '.' || (random() * 255)::int)::inet,
    NOW() - (random() * 365 || ' days')::interval
FROM generate_series(1, 5000) i;

-- =====================================================================
-- Update statistics
-- =====================================================================
ANALYZE customers;
ANALYZE merchants;
ANALYZE internal_users;
ANALYZE accounts;
ANALYZE cards;
ANALYZE transactions;
ANALYZE payments;
ANALYZE kyc_documents;
ANALYZE customer_notes;
ANALYZE audit_log;
