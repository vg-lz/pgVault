-- =====================================================================
-- FintechDB — Scale to LARGE mode (OPTIONAL)
-- =====================================================================
-- Run this AFTER the base seed has completed if you want a more
-- realistic dataset (~3 GB, 10-15 minutes of seeding).
--
-- Usage:
--   docker exec -i fintechdb psql -U fintech_user -d fintechdb < scripts/scale_to_large.sql
--
-- Targets after scaling:
--   customers       ~200K   (from 5K)
--   cards           ~350K   (from 8K)
--   accounts        ~100K   (from 3K)
--   merchants       ~5K     (from 200)
--   transactions    ~3M     (from 100K)
--   payments        ~2M     (from 80K)
--   internal_users  ~100    (from 25)
--   audit_log       ~1M     (from 50K)
--   kyc_documents   ~200K   (from 5K)
--   customer_notes  ~800K   (from 30K)
-- =====================================================================

SET client_min_messages = WARNING;

-- =====================================================================
-- Scale internal_users: 25 -> 100
-- =====================================================================
INSERT INTO internal_users (username, full_name, email, password_plain, role, last_login, created_at)
SELECT
    'user_l' || i,
    'Internal User Large ' || i,
    'user_l' || i || '@fintechmx.com',
    'pass_l' || i || '!23',
    (ARRAY['operator', 'support', 'viewer', 'analyst'])[1 + (i % 4)],
    NOW() - (random() * 30 || ' days')::interval,
    NOW() - (random() * 730 || ' days')::interval
FROM generate_series(26, 100) i;

-- =====================================================================
-- Scale customers: 5K -> 200K
-- =====================================================================
INSERT INTO customers (full_name, rfc, curp, email, phone, birth_date, address, city, state, country, risk_score, is_active, created_at)
SELECT
    'Customer Large ' || i || ' Lastname',
    gen_synthetic_rfc(i + 100000),
    gen_synthetic_curp(i + 100000),
    'customer_l' || i || '@example.com',
    '+52' || (5500000000 + i + 100000)::text,
    DATE '1960-01-01' + (random() * 20000)::int,
    'Calle ' || (random() * 1000)::int || ' #' || (random() * 999)::int,
    (ARRAY['Mexico City', 'Guadalajara', 'Monterrey', 'Queretaro', 'Puebla'])[1 + (i % 5)],
    (ARRAY['CDMX', 'JAL', 'NL', 'QRO', 'PUE'])[1 + (i % 5)],
    'MX',
    (random() * 100)::int,
    CASE WHEN i % 50 = 0 THEN FALSE ELSE TRUE END,
    NOW() - (random() * 730 || ' days')::interval
FROM generate_series(5001, 200000) i;

-- =====================================================================
-- Scale merchants: 200 -> 5000
-- =====================================================================
INSERT INTO merchants (legal_name, trade_name, rfc, mcc, bank_account, contact_email, onboarded_at, is_active)
SELECT
    'Empresa Large ' || i || ' S.A. de C.V.',
    'Brand Large ' || i,
    gen_synthetic_rfc(i + 200000),
    lpad(((4000 + (random() * 5000)::int))::text, 4, '0'),
    gen_synthetic_clabe(i + 100000),
    'contact@empresa_l' || i || '.com.mx',
    NOW() - (random() * 1095 || ' days')::interval,
    CASE WHEN i % 30 = 0 THEN FALSE ELSE TRUE END
FROM generate_series(201, 5000) i;

-- =====================================================================
-- Scale accounts: 3K -> 100K
-- =====================================================================
INSERT INTO accounts (customer_id, account_number, bank_code, account_type, balance, currency, is_active, created_at)
SELECT
    1 + (i % 200000),
    lpad((random() * 99999999999999999)::bigint::text, 16, '0'),
    (ARRAY['BBVA', 'BANAMEX', 'SANTANDER', 'BANORTE', 'HSBC'])[1 + (i % 5)],
    (ARRAY['savings', 'checking', 'investment'])[1 + (i % 3)],
    (random() * 1000000)::numeric(14, 2),
    'MXN',
    CASE WHEN i % 40 = 0 THEN FALSE ELSE TRUE END,
    NOW() - (random() * 730 || ' days')::interval
FROM generate_series(3001, 100000) i;

-- =====================================================================
-- Scale cards: 8K -> 350K
-- =====================================================================
INSERT INTO cards (customer_id, pan, cvv, cardholder_name, expiration_date, card_brand, is_active, created_at)
SELECT
    1 + (i % 200000),
    gen_synthetic_pan(i + 100000),
    lpad((random() * 999)::int::text, 3, '0'),
    'CARDHOLDER LARGE ' || i,
    lpad((1 + (random() * 11)::int)::text, 2, '0') || '/' || (2026 + (random() * 5)::int)::text,
    (ARRAY['visa', 'mastercard', 'amex', 'visa', 'mastercard'])[1 + (i % 5)],
    CASE WHEN i % 25 = 0 THEN FALSE ELSE TRUE END,
    NOW() - (random() * 730 || ' days')::interval
FROM generate_series(8001, 350000) i;

-- =====================================================================
-- Scale transactions: 100K -> 3M (in batches)
-- =====================================================================
DO $$
DECLARE
    batch INTEGER;
BEGIN
    FOR batch IN 1..29 LOOP
        INSERT INTO transactions (merchant_id, customer_id, card_id, amount, currency, auth_code, status, decline_reason, transaction_at, response_time_ms)
        SELECT
            1 + (random() * 4999)::int,
            1 + (random() * 199999)::int,
            1 + (random() * 349999)::int,
            (random() * 5000 + 50)::numeric(12, 2),
            'MXN',
            upper(substring(md5(random()::text), 1, 8)),
            CASE WHEN random() < 0.85 THEN 'approved'
                 WHEN random() < 0.95 THEN 'declined'
                 ELSE 'pending' END,
            CASE WHEN random() < 0.10 THEN
                (ARRAY['insufficient_funds', 'expired_card', 'invalid_cvv', 'fraud_suspected', 'limit_exceeded'])[1 + (random() * 4)::int]
            ELSE NULL END,
            NOW() - (random() * 730 || ' days')::interval,
            (50 + random() * 2000)::int
        FROM generate_series(1, 100000) i;
        RAISE NOTICE 'transactions batch % done', batch;
    END LOOP;
END $$;

-- =====================================================================
-- Scale payments
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
LEFT JOIN payments p ON p.transaction_id = t.id
WHERE t.status = 'approved' AND p.id IS NULL;

-- =====================================================================
-- Scale kyc_documents: 5K -> 200K
-- =====================================================================
INSERT INTO kyc_documents (customer_id, doc_type, doc_number, issued_date, expires_date, storage_url, verified_at, verified_by, created_at)
SELECT
    1 + (i % 200000),
    (ARRAY['INE', 'passport', 'address_proof', 'tax_certificate'])[1 + (i % 4)],
    'DOC-L-' || lpad(i::text, 8, '0'),
    DATE '2015-01-01' + (random() * 3000)::int,
    DATE '2025-01-01' + (random() * 1500)::int,
    'https://kyc-storage.fintechmx.com/docs/' || i || '.pdf',
    NOW() - (random() * 365 || ' days')::interval,
    1 + (random() * 99)::int,
    NOW() - (random() * 730 || ' days')::interval
FROM generate_series(5001, 200000) i;

-- =====================================================================
-- Scale customer_notes: 30K -> 800K (most are normal, ~10% with PII)
-- =====================================================================
INSERT INTO customer_notes (customer_id, author_id, body, note_type, created_at)
SELECT
    1 + (i % 200000),
    1 + (i % 100),
    (ARRAY[
        'Customer called regarding account.',
        'Identity verified.',
        'Account update requested.',
        'Transaction reviewed.',
        'Compliance check completed.'
    ])[1 + (i % 5)],
    (ARRAY['call', 'email', 'chat', 'in_person'])[1 + (i % 4)],
    NOW() - (random() * 730 || ' days')::interval
FROM generate_series(30001, 750000) i;

-- ~5% additional with hidden CURPs
INSERT INTO customer_notes (customer_id, author_id, body, note_type, created_at)
SELECT
    1 + (i % 200000),
    1 + (i % 100),
    'Verification: CURP ' || gen_synthetic_curp(i + 200000) || '. Confirmed.',
    'verification',
    NOW() - (random() * 365 || ' days')::interval
FROM generate_series(1, 50000) i;

-- =====================================================================
-- Scale audit_log: 50K -> 1M
-- =====================================================================
DO $$
DECLARE
    batch INTEGER;
BEGIN
    FOR batch IN 1..9 LOOP
        INSERT INTO audit_log (actor_id, actor_type, action, target_table, target_id, details, ip_address, created_at)
        SELECT
            1 + (i % 100),
            'internal_user',
            (ARRAY['view', 'update', 'create', 'delete', 'login', 'logout', 'export'])[1 + (i % 7)],
            (ARRAY['customers', 'cards', 'transactions', 'payments', 'merchants'])[1 + (i % 5)],
            1 + (random() * 200000)::int,
            jsonb_build_object('ip', '192.168.' || (random() * 255)::int || '.' || (random() * 255)::int,
                               'session_id', md5(random()::text)),
            ('192.168.' || (random() * 255)::int || '.' || (random() * 255)::int)::inet,
            NOW() - (random() * 1095 || ' days')::interval
        FROM generate_series(1, 100000) i;
        RAISE NOTICE 'audit_log batch % done', batch;
    END LOOP;
END $$;

-- =====================================================================
-- Re-analyze
-- =====================================================================
ANALYZE customers;
ANALYZE cards;
ANALYZE merchants;
ANALYZE internal_users;
ANALYZE accounts;
ANALYZE transactions;
ANALYZE payments;
ANALYZE kyc_documents;
ANALYZE customer_notes;
ANALYZE audit_log;

DO $$
BEGIN
    RAISE NOTICE 'FintechDB scaled to LARGE mode. Planted problems still active.';
END $$;
