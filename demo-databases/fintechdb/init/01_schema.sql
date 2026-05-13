-- =====================================================================
-- FintechDB v1.0 — Schema base
-- Mexican fintech demo database for PgVault project (SIS2404)
-- =====================================================================
-- Schema in English. Designed to support all 22 planted problems
-- including PII discovery, role/privilege misconfigs, and audit issues.
--
-- WARNING: This DB intentionally contains insecure practices for
-- pedagogical purposes. NEVER use this configuration in production.
-- =====================================================================

-- Drop in correct order if re-running
DROP TABLE IF EXISTS audit_log CASCADE;
DROP TABLE IF EXISTS customer_notes CASCADE;
DROP TABLE IF EXISTS kyc_documents CASCADE;
DROP TABLE IF EXISTS payments CASCADE;
DROP TABLE IF EXISTS transactions CASCADE;
DROP TABLE IF EXISTS cards CASCADE;
DROP TABLE IF EXISTS accounts CASCADE;
DROP TABLE IF EXISTS internal_users CASCADE;
DROP TABLE IF EXISTS merchants CASCADE;
DROP TABLE IF EXISTS customers CASCADE;

-- Drop functions if they exist
DROP FUNCTION IF EXISTS get_customer_full_data(INTEGER);

-- Drop roles if they exist (clean slate)
DROP ROLE IF EXISTS app_legacy;
DROP ROLE IF EXISTS analyst_user;
DROP ROLE IF EXISTS reports_user;
DROP ROLE IF EXISTS app_admin;

-- =====================================================================
-- customers — end customers (contains PII: H11, H12, H13)
-- =====================================================================
CREATE TABLE customers (
    id              SERIAL PRIMARY KEY,
    full_name       VARCHAR(200) NOT NULL,
    rfc             VARCHAR(13),                    -- H11: Mexican tax ID, sensitive
    curp            VARCHAR(18),                    -- H12: Mexican unique ID, sensitive
    email           VARCHAR(200) NOT NULL,          -- H13: PII
    phone           VARCHAR(20),
    birth_date      DATE,
    address         TEXT,
    city            VARCHAR(100),
    state           VARCHAR(100),
    country         VARCHAR(50) DEFAULT 'MX',
    risk_score      INTEGER DEFAULT 0,
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);

-- =====================================================================
-- merchants — affiliated businesses
-- bank_account contains CLABE numbers (H19: PII by content)
-- =====================================================================
CREATE TABLE merchants (
    id              SERIAL PRIMARY KEY,
    legal_name      VARCHAR(250) NOT NULL,
    trade_name      VARCHAR(250),
    rfc             VARCHAR(13),
    mcc             VARCHAR(10),                    -- Merchant category code
    bank_account    VARCHAR(50),                    -- H19: CLABE in generic-named col
    contact_email   VARCHAR(200),
    onboarded_at    TIMESTAMP DEFAULT NOW(),
    is_active       BOOLEAN DEFAULT TRUE
);

-- =====================================================================
-- internal_users — system operators (H16: passwords in plain text)
-- =====================================================================
CREATE TABLE internal_users (
    id              SERIAL PRIMARY KEY,
    username        VARCHAR(50) UNIQUE NOT NULL,
    full_name       VARCHAR(200),
    email           VARCHAR(200),
    password_plain  VARCHAR(100),                   -- H16: PROHIBITED, plain passwords
    role            VARCHAR(50),
    last_login      TIMESTAMP,
    created_at      TIMESTAMP DEFAULT NOW(),
    is_active       BOOLEAN DEFAULT TRUE
);

-- =====================================================================
-- accounts — customer bank accounts
-- =====================================================================
CREATE TABLE accounts (
    id              SERIAL PRIMARY KEY,
    customer_id     INTEGER NOT NULL REFERENCES customers(id),
    account_number  VARCHAR(20),
    bank_code       VARCHAR(10),
    account_type    VARCHAR(20),
    balance         NUMERIC(14, 2) DEFAULT 0,
    currency        VARCHAR(3) DEFAULT 'MXN',
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT NOW()
);

-- =====================================================================
-- cards — registered cards (PCI VIOLATIONS planted: H14, H15)
-- =====================================================================
CREATE TABLE cards (
    id              SERIAL PRIMARY KEY,
    customer_id     INTEGER NOT NULL REFERENCES customers(id),
    pan             VARCHAR(20) NOT NULL,           -- H14: full PAN, PCI violation
    cvv             VARCHAR(4),                     -- H15: CVV stored, ULTRA prohibited
    cardholder_name VARCHAR(200),
    expiration_date VARCHAR(7),                     -- MM/YYYY
    card_brand      VARCHAR(20),                    -- visa, mastercard, amex, etc.
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT NOW()
);

-- =====================================================================
-- transactions — authorization requests (high volume)
-- =====================================================================
CREATE TABLE transactions (
    id              BIGSERIAL PRIMARY KEY,
    merchant_id     INTEGER REFERENCES merchants(id),
    customer_id     INTEGER REFERENCES customers(id),
    card_id         INTEGER REFERENCES cards(id),
    amount          NUMERIC(12, 2) NOT NULL,
    currency        VARCHAR(3) DEFAULT 'MXN',
    auth_code       VARCHAR(20),
    status          VARCHAR(20),                    -- approved, declined, pending
    decline_reason  TEXT,
    transaction_at  TIMESTAMP DEFAULT NOW(),
    response_time_ms INTEGER
);

-- =====================================================================
-- payments — completed payments
-- =====================================================================
CREATE TABLE payments (
    id              BIGSERIAL PRIMARY KEY,
    transaction_id  BIGINT REFERENCES transactions(id),
    merchant_id     INTEGER REFERENCES merchants(id),
    amount          NUMERIC(12, 2) NOT NULL,
    fee             NUMERIC(8, 2) DEFAULT 0,
    settlement_date DATE,
    status          VARCHAR(20),
    created_at      TIMESTAMP DEFAULT NOW()
);

-- =====================================================================
-- kyc_documents — KYC document metadata
-- =====================================================================
CREATE TABLE kyc_documents (
    id              SERIAL PRIMARY KEY,
    customer_id     INTEGER NOT NULL REFERENCES customers(id),
    doc_type        VARCHAR(50),                    -- INE, passport, address_proof
    doc_number      VARCHAR(50),
    issued_date     DATE,
    expires_date    DATE,
    storage_url     TEXT,
    verified_at     TIMESTAMP,
    verified_by     INTEGER REFERENCES internal_users(id),
    created_at      TIMESTAMP DEFAULT NOW()
);

-- =====================================================================
-- customer_notes — free-text notes from support
-- body field can contain hidden PII (H17 by content)
-- =====================================================================
CREATE TABLE customer_notes (
    id              SERIAL PRIMARY KEY,
    customer_id     INTEGER NOT NULL REFERENCES customers(id),
    author_id       INTEGER REFERENCES internal_users(id),
    body            TEXT,                           -- H17: free text with hidden CURPs
    note_type       VARCHAR(50),
    created_at      TIMESTAMP DEFAULT NOW()
);

-- =====================================================================
-- audit_log — audit trail (H18: PII in JSONB; H21: not append-only)
-- =====================================================================
CREATE TABLE audit_log (
    id              BIGSERIAL PRIMARY KEY,
    actor_id        INTEGER,
    actor_type      VARCHAR(20),                    -- internal_user, customer, system
    action          VARCHAR(100),
    target_table    VARCHAR(100),
    target_id       BIGINT,
    details         JSONB,                          -- H18: contains hidden PII
    ip_address      INET,
    created_at      TIMESTAMP DEFAULT NOW()
);

-- =====================================================================
-- "Legitimate" indexes
-- =====================================================================
CREATE INDEX idx_customers_email ON customers(email);
CREATE INDEX idx_customers_rfc ON customers(rfc);
CREATE INDEX idx_accounts_customer_id ON accounts(customer_id);
CREATE INDEX idx_cards_customer_id ON cards(customer_id);
CREATE INDEX idx_transactions_customer_id ON transactions(customer_id);
CREATE INDEX idx_transactions_merchant_id ON transactions(merchant_id);
CREATE INDEX idx_transactions_at ON transactions(transaction_at);
CREATE INDEX idx_payments_transaction_id ON payments(transaction_id);
CREATE INDEX idx_kyc_customer_id ON kyc_documents(customer_id);
CREATE INDEX idx_notes_customer_id ON customer_notes(customer_id);
CREATE INDEX idx_audit_log_created_at ON audit_log(created_at);

-- =====================================================================
-- Comments for documentation
-- =====================================================================
COMMENT ON TABLE customers IS 'End customer master data';
COMMENT ON TABLE cards IS 'Registered payment cards';
COMMENT ON TABLE transactions IS 'Authorization requests';
COMMENT ON TABLE payments IS 'Completed settlements';
COMMENT ON TABLE merchants IS 'Affiliated businesses';
COMMENT ON TABLE internal_users IS 'System operators and admins';
COMMENT ON TABLE audit_log IS 'System audit trail';
COMMENT ON TABLE kyc_documents IS 'KYC document metadata';
COMMENT ON TABLE customer_notes IS 'Free-text customer support notes';
COMMENT ON TABLE accounts IS 'Customer bank accounts';
