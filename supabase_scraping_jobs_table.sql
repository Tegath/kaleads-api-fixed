-- ============================================
-- Scraping Jobs Table - Track Background Jobs
-- ============================================
-- This table tracks long-running scraping jobs with resume capability

CREATE TABLE IF NOT EXISTS scraping_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_type TEXT NOT NULL,  -- 'google_maps' or 'jobspy'
    status TEXT NOT NULL,  -- 'pending', 'running', 'completed', 'failed', 'paused'
    client_id TEXT NOT NULL,

    -- Job parameters
    query TEXT NOT NULL,
    country TEXT,
    search_params JSONB,  -- Full search parameters

    -- Progress tracking
    total_cities INTEGER,
    cities_completed INTEGER DEFAULT 0,
    cities_remaining TEXT[],  -- Array of cities not yet processed
    current_city TEXT,

    -- Results tracking
    total_leads_found INTEGER DEFAULT 0,
    total_api_calls INTEGER DEFAULT 0,
    estimated_cost_usd FLOAT DEFAULT 0,

    -- Error handling
    errors JSONB[],  -- Array of error objects
    last_error TEXT,
    retry_count INTEGER DEFAULT 0,

    -- Timing
    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Resume capability
    last_checkpoint JSONB,  -- Save state for resume
    can_resume BOOLEAN DEFAULT true
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_scraping_jobs_status ON scraping_jobs(status);
CREATE INDEX IF NOT EXISTS idx_scraping_jobs_client ON scraping_jobs(client_id);
CREATE INDEX IF NOT EXISTS idx_scraping_jobs_type ON scraping_jobs(job_type);
CREATE INDEX IF NOT EXISTS idx_scraping_jobs_created ON scraping_jobs(created_at);

-- Auto-update updated_at
CREATE TRIGGER update_scraping_jobs_updated_at
BEFORE UPDATE ON scraping_jobs
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- City Strategy Table - Population-based strategy
-- ============================================

CREATE TABLE IF NOT EXISTS city_strategy (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    city_name TEXT NOT NULL,
    department TEXT,
    code_geo TEXT,
    population INTEGER,

    -- Scraping strategy
    max_pages INTEGER,  -- Max pages to scrape for this city
    priority INTEGER,  -- 1=high, 2=medium, 3=low
    should_scrape BOOLEAN DEFAULT true,  -- Skip cities with pop < threshold

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_city_strategy_name ON city_strategy(city_name);
CREATE INDEX IF NOT EXISTS idx_city_strategy_dept ON city_strategy(department);
CREATE INDEX IF NOT EXISTS idx_city_strategy_priority ON city_strategy(priority);

-- ============================================
-- Useful Queries
-- ============================================

-- Get all running jobs
-- SELECT id, job_type, query, cities_completed, total_cities, total_leads_found
-- FROM scraping_jobs
-- WHERE status = 'running'
-- ORDER BY created_at DESC;

-- Get job progress percentage
-- SELECT
--   id,
--   query,
--   ROUND((cities_completed::float / total_cities::float) * 100, 2) as progress_pct,
--   total_leads_found,
--   estimated_cost_usd
-- FROM scraping_jobs
-- WHERE status = 'running';

-- Resume a failed job
-- UPDATE scraping_jobs
-- SET status = 'pending', retry_count = retry_count + 1
-- WHERE id = 'job-uuid-here' AND can_resume = true;
