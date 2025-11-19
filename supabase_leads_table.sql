-- ============================================
-- Leads Table for Comprehensive Lead Storage
-- ============================================
-- This table stores all leads scraped from Google Maps and JobSpy
-- with automatic deduplication and indexing for fast queries

-- Drop table if exists (BE CAREFUL IN PRODUCTION!)
-- DROP TABLE IF EXISTS leads;

-- Create leads table
CREATE TABLE IF NOT EXISTS leads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lead_hash TEXT UNIQUE NOT NULL,  -- For deduplication (MD5 of company_name + city + source)
    company_name TEXT NOT NULL,
    city TEXT,
    country TEXT,
    address TEXT,
    phone TEXT,
    email TEXT,
    website TEXT,
    rating FLOAT,
    reviews_count INTEGER,
    place_id TEXT,  -- Google Maps place_id for reference
    search_query TEXT,  -- Original search query that found this lead
    source TEXT NOT NULL,  -- 'google_maps' or 'jobspy'
    raw_data JSONB,  -- Full API response for future reference
    client_id TEXT NOT NULL,  -- Which client this lead belongs to
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_leads_hash ON leads(lead_hash);
CREATE INDEX IF NOT EXISTS idx_leads_client ON leads(client_id);
CREATE INDEX IF NOT EXISTS idx_leads_source ON leads(source);
CREATE INDEX IF NOT EXISTS idx_leads_city ON leads(city);
CREATE INDEX IF NOT EXISTS idx_leads_country ON leads(country);
CREATE INDEX IF NOT EXISTS idx_leads_company_name ON leads(company_name);
CREATE INDEX IF NOT EXISTS idx_leads_created_at ON leads(created_at);

-- Create compound index for common queries
CREATE INDEX IF NOT EXISTS idx_leads_client_source ON leads(client_id, source);
CREATE INDEX IF NOT EXISTS idx_leads_client_city ON leads(client_id, city);

-- Add Row Level Security (RLS) policies
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;

-- Policy: Service role can do everything
CREATE POLICY "Service role has full access to leads"
ON leads
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- Policy: Authenticated users can read their own client's leads
CREATE POLICY "Users can read their client leads"
ON leads
FOR SELECT
TO authenticated
USING (client_id = current_setting('app.current_client_id', true));

-- Optional: Add trigger to auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_leads_updated_at
BEFORE UPDATE ON leads
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- Useful Queries
-- ============================================

-- Count total leads by source
-- SELECT source, COUNT(*) as count
-- FROM leads
-- WHERE client_id = 'kaleads'
-- GROUP BY source;

-- Count leads by city (top 10)
-- SELECT city, COUNT(*) as count
-- FROM leads
-- WHERE client_id = 'kaleads'
-- GROUP BY city
-- ORDER BY count DESC
-- LIMIT 10;

-- Get recent leads
-- SELECT company_name, city, source, created_at
-- FROM leads
-- WHERE client_id = 'kaleads'
-- ORDER BY created_at DESC
-- LIMIT 100;

-- Check for duplicates
-- SELECT lead_hash, COUNT(*) as count
-- FROM leads
-- GROUP BY lead_hash
-- HAVING COUNT(*) > 1;
