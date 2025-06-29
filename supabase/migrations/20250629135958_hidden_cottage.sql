-- Database initialization script for Drug Interaction Detection System
-- This script sets up the initial database schema and sample data

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For fuzzy text search

-- Create enum types
CREATE TYPE user_role AS ENUM ('user', 'doctor', 'pharmacist', 'admin');
CREATE TYPE severity_level AS ENUM ('minor', 'moderate', 'major', 'critical');
CREATE TYPE processing_status AS ENUM ('pending', 'processing', 'completed', 'failed');

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    date_of_birth DATE,
    emergency_contact TEXT,
    allergies TEXT[],
    medical_conditions TEXT[],
    role user_role DEFAULT 'user',
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE
);

-- Drugs reference table
CREATE TABLE IF NOT EXISTS drugs (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    generic_name VARCHAR(255),
    brand_names TEXT[],
    ndc_numbers TEXT[],
    rxcui VARCHAR(50),
    drug_class VARCHAR(100),
    active_ingredients JSONB,
    contraindications TEXT[],
    side_effects JSONB,
    dosage_forms TEXT[],
    strength_options TEXT[],
    fda_approval_date DATE,
    manufacturer VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Drug interactions reference
CREATE TABLE IF NOT EXISTS drug_interactions (
    id SERIAL PRIMARY KEY,
    drug1_id INTEGER REFERENCES drugs(id),
    drug2_id INTEGER REFERENCES drugs(id),
    severity severity_level NOT NULL,
    interaction_type VARCHAR(50),
    mechanism TEXT,
    clinical_effect TEXT NOT NULL,
    management TEXT,
    evidence_level VARCHAR(20),
    frequency VARCHAR(20),
    onset VARCHAR(20),
    documentation VARCHAR(20),
    source VARCHAR(100),
    source_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT unique_drug_pair UNIQUE(drug1_id, drug2_id)
);

-- User medications
CREATE TABLE IF NOT EXISTS medications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    drug_id INTEGER REFERENCES drugs(id),
    custom_name VARCHAR(255),
    dosage VARCHAR(100),
    frequency VARCHAR(100),
    route VARCHAR(50),
    prescriber VARCHAR(255),
    pharmacy VARCHAR(255),
    prescription_date DATE,
    start_date DATE,
    end_date DATE,
    is_active BOOLEAN DEFAULT TRUE,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Prescription scans
CREATE TABLE IF NOT EXISTS prescription_scans (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    image_path VARCHAR(500),
    image_url VARCHAR(500),
    extracted_text TEXT,
    extracted_data JSONB,
    confidence_score DECIMAL(3,2),
    processing_status processing_status DEFAULT 'pending',
    processing_time_ms INTEGER,
    error_message TEXT,
    medications_detected TEXT[],
    interactions_found INTEGER DEFAULT 0,
    risk_level VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Interaction alerts
CREATE TABLE IF NOT EXISTS interaction_alerts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    interaction_id INTEGER REFERENCES drug_interactions(id),
    medication_ids INTEGER[],
    severity severity_level NOT NULL,
    alert_type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    recommendations TEXT[],
    is_acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    is_dismissed BOOLEAN DEFAULT FALSE,
    dismissed_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Audit log
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id VARCHAR(50),
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_drugs_name ON drugs USING gin(name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_drugs_generic_name ON drugs USING gin(generic_name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_drugs_rxcui ON drugs(rxcui);
CREATE INDEX IF NOT EXISTS idx_drug_interactions_severity ON drug_interactions(severity);
CREATE INDEX IF NOT EXISTS idx_drug_interactions_drugs ON drug_interactions(drug1_id, drug2_id);
CREATE INDEX IF NOT EXISTS idx_medications_user_id ON medications(user_id);
CREATE INDEX IF NOT EXISTS idx_medications_active ON medications(user_id, is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_prescription_scans_user_id ON prescription_scans(user_id);
CREATE INDEX IF NOT EXISTS idx_prescription_scans_status ON prescription_scans(processing_status);
CREATE INDEX IF NOT EXISTS idx_interaction_alerts_user_id ON interaction_alerts(user_id);
CREATE INDEX IF NOT EXISTS idx_interaction_alerts_active ON interaction_alerts(user_id, is_acknowledged, is_dismissed);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_action ON audit_logs(user_id, action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at);

-- Insert sample drug data
INSERT INTO drugs (name, generic_name, drug_class, active_ingredients, contraindications, side_effects) VALUES
('Lisinopril', 'lisinopril', 'ACE Inhibitor', '["lisinopril"]', ARRAY['pregnancy', 'angioedema'], '["cough", "hyperkalemia", "hypotension"]'),
('Metformin', 'metformin hydrochloride', 'Antidiabetic', '["metformin"]', ARRAY['kidney disease', 'metabolic acidosis'], '["nausea", "diarrhea", "lactic acidosis"]'),
('Atorvastatin', 'atorvastatin calcium', 'Statin', '["atorvastatin"]', ARRAY['liver disease', 'pregnancy'], '["myalgia", "elevated liver enzymes"]'),
('Amlodipine', 'amlodipine besylate', 'Calcium Channel Blocker', '["amlodipine"]', ARRAY['severe hypotension'], '["edema", "dizziness", "flushing"]'),
('Omeprazole', 'omeprazole', 'Proton Pump Inhibitor', '["omeprazole"]', ARRAY['hypersensitivity'], '["headache", "nausea", "diarrhea"]'),
('Warfarin', 'warfarin sodium', 'Anticoagulant', '["warfarin"]', ARRAY['bleeding disorders', 'pregnancy'], '["bleeding", "bruising"]'),
('Aspirin', 'acetylsalicylic acid', 'NSAID', '["aspirin"]', ARRAY['bleeding disorders', 'children with viral infections'], '["GI bleeding", "tinnitus"]'),
('Ibuprofen', 'ibuprofen', 'NSAID', '["ibuprofen"]', ARRAY['kidney disease', 'heart failure'], '["GI upset", "kidney problems"]'),
('Simvastatin', 'simvastatin', 'Statin', '["simvastatin"]', ARRAY['liver disease', 'pregnancy'], '["myopathy", "liver problems"]'),
('Digoxin', 'digoxin', 'Cardiac Glycoside', '["digoxin"]', ARRAY['ventricular fibrillation'], '["nausea", "arrhythmias"]');

-- Insert sample drug interactions
INSERT INTO drug_interactions (drug1_id, drug2_id, severity, interaction_type, clinical_effect, management, evidence_level) VALUES
((SELECT id FROM drugs WHERE name = 'Warfarin'), (SELECT id FROM drugs WHERE name = 'Aspirin'), 'critical', 'pharmacodynamic', 'Increased risk of bleeding', 'Avoid combination or monitor INR closely', 'established'),
((SELECT id FROM drugs WHERE name = 'Warfarin'), (SELECT id FROM drugs WHERE name = 'Ibuprofen'), 'major', 'pharmacodynamic', 'Increased bleeding risk', 'Use alternative pain management', 'established'),
((SELECT id FROM drugs WHERE name = 'Simvastatin'), (SELECT id FROM drugs WHERE name = 'Digoxin'), 'moderate', 'pharmacokinetic', 'Possible increased digoxin levels', 'Monitor digoxin levels', 'probable'),
((SELECT id FROM drugs WHERE name = 'Lisinopril'), (SELECT id FROM drugs WHERE name = 'Ibuprofen'), 'moderate', 'pharmacodynamic', 'Reduced antihypertensive effect', 'Monitor blood pressure', 'established'),
((SELECT id FROM drugs WHERE name = 'Metformin'), (SELECT id FROM drugs WHERE name = 'Atorvastatin'), 'minor', 'none', 'Generally safe combination', 'No specific monitoring required', 'established');

-- Create triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_drugs_updated_at BEFORE UPDATE ON drugs FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_drug_interactions_updated_at BEFORE UPDATE ON drug_interactions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_medications_updated_at BEFORE UPDATE ON medications FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create views for common queries
CREATE OR REPLACE VIEW user_active_medications AS
SELECT 
    m.user_id,
    u.name as user_name,
    u.email,
    m.id as medication_id,
    COALESCE(d.name, m.custom_name) as medication_name,
    d.generic_name,
    m.dosage,
    m.frequency,
    m.start_date,
    m.prescriber
FROM medications m
JOIN users u ON m.user_id = u.id
LEFT JOIN drugs d ON m.drug_id = d.id
WHERE m.is_active = TRUE AND u.is_active = TRUE;

CREATE OR REPLACE VIEW critical_interactions AS
SELECT 
    di.id,
    d1.name as drug1_name,
    d2.name as drug2_name,
    di.severity,
    di.clinical_effect,
    di.management,
    di.evidence_level
FROM drug_interactions di
JOIN drugs d1 ON di.drug1_id = d1.id
JOIN drugs d2 ON di.drug2_id = d2.id
WHERE di.severity = 'critical'
ORDER BY d1.name, d2.name;

-- Insert sample admin user (password: admin123)
INSERT INTO users (email, name, password_hash, role, is_active, is_verified) VALUES
('admin@druginteraction.com', 'System Administrator', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LQdHxkd0LHAkCOYz6T', 'admin', TRUE, TRUE);

-- Grant permissions (adjust as needed for your setup)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO drugapp;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO drugapp;