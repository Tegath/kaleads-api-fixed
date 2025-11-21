-- Migration: Add qualification columns to leads table
-- Date: 2025-11-20
-- Purpose: Enable progressive lead qualification workflow

-- Add qualification columns
ALTER TABLE leads
ADD COLUMN IF NOT EXISTS stage TEXT DEFAULT 'new',
ADD COLUMN IF NOT EXISTS score INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS pci_match JSONB,
ADD COLUMN IF NOT EXISTS website_content TEXT,
ADD COLUMN IF NOT EXISTS qualified_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS monthly_batch TEXT,
ADD COLUMN IF NOT EXISTS qualification_reasons TEXT[];

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_leads_stage ON leads(stage);
CREATE INDEX IF NOT EXISTS idx_leads_score ON leads(score DESC);
CREATE INDEX IF NOT EXISTS idx_leads_qualified_at ON leads(qualified_at DESC);
CREATE INDEX IF NOT EXISTS idx_leads_monthly_batch ON leads(monthly_batch);

-- Add comments for documentation
COMMENT ON COLUMN leads.stage IS 'Lead qualification stage: new, qualifying, qualified_high, qualified_medium, qualified_low, enriching, enriched, contacted, no_site';
COMMENT ON COLUMN leads.score IS 'PCI match score 0-100, higher = better match';
COMMENT ON COLUMN leads.pci_match IS 'Full PCI qualification result from API';
COMMENT ON COLUMN leads.website_content IS 'Scraped website content for analysis';
COMMENT ON COLUMN leads.qualified_at IS 'Timestamp when lead was qualified';
COMMENT ON COLUMN leads.monthly_batch IS 'Monthly batch identifier (YYYY-MM) for rate limiting';
COMMENT ON COLUMN leads.qualification_reasons IS 'Array of reasons why lead qualified/disqualified';
