-- TimescaleDB initialization script for SEO Platform
-- This script creates hypertables for time-series data

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Create schemas
CREATE SCHEMA IF NOT EXISTS timeseries;
CREATE SCHEMA IF NOT EXISTS metrics;

-- Set default schema
SET search_path TO timeseries, public;

-- Rankings time-series table (more detailed than main rankings table)
CREATE TABLE IF NOT EXISTS ranking_history (
    time TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    project_id UUID NOT NULL,
    keyword_id UUID NOT NULL,
    keyword VARCHAR(500) NOT NULL,
    position INTEGER NOT NULL,
    url TEXT,
    title TEXT,
    page_type VARCHAR(50),
    serp_features TEXT[] DEFAULT '{}',
    location_code INTEGER DEFAULT 2840,
    device VARCHAR(20) DEFAULT 'desktop',
    search_volume INTEGER,
    traffic_estimate INTEGER,
    click_rate DECIMAL(5,4),
    impressions INTEGER,
    clicks INTEGER
);

-- Convert to hypertable (partitioned by time)
SELECT create_hypertable('ranking_history', 'time', if_not_exists => TRUE);

-- Keyword metrics time-series
CREATE TABLE IF NOT EXISTS keyword_metrics (
    time TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    project_id UUID NOT NULL,
    keyword_id UUID NOT NULL,
    keyword VARCHAR(500) NOT NULL,
    search_volume INTEGER,
    difficulty DECIMAL(5,2),
    cpc DECIMAL(10,2),
    competition DECIMAL(5,4),
    trend_direction VARCHAR(20), -- up, down, stable
    volatility_score DECIMAL(5,2),
    opportunity_score DECIMAL(5,2)
);

SELECT create_hypertable('keyword_metrics', 'time', if_not_exists => TRUE);

-- Website traffic metrics
CREATE TABLE IF NOT EXISTS traffic_metrics (
    time TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    project_id UUID NOT NULL,
    source VARCHAR(100) NOT NULL, -- organic, direct, referral, social, etc.
    sessions INTEGER DEFAULT 0,
    users INTEGER DEFAULT 0,
    pageviews INTEGER DEFAULT 0,
    bounce_rate DECIMAL(5,4),
    avg_session_duration INTEGER, -- seconds
    conversion_rate DECIMAL(5,4),
    revenue DECIMAL(12,2)
);

SELECT create_hypertable('traffic_metrics', 'time', if_not_exists => TRUE);

-- Backlink metrics time-series
CREATE TABLE IF NOT EXISTS backlink_metrics (
    time TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    project_id UUID NOT NULL,
    total_backlinks INTEGER DEFAULT 0,
    referring_domains INTEGER DEFAULT 0,
    dofollow_links INTEGER DEFAULT 0,
    nofollow_links INTEGER DEFAULT 0,
    avg_domain_rating DECIMAL(5,2),
    new_links INTEGER DEFAULT 0,
    lost_links INTEGER DEFAULT 0,
    broken_links INTEGER DEFAULT 0
);

SELECT create_hypertable('backlink_metrics', 'time', if_not_exists => TRUE);

-- Technical SEO metrics
CREATE TABLE IF NOT EXISTS technical_metrics (
    time TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    project_id UUID NOT NULL,
    url TEXT NOT NULL,
    page_load_time INTEGER, -- milliseconds
    core_web_vitals JSONB DEFAULT '{}',
    lighthouse_score INTEGER,
    accessibility_score INTEGER,
    seo_score INTEGER,
    mobile_friendly BOOLEAN,
    ssl_valid BOOLEAN,
    crawl_errors INTEGER DEFAULT 0,
    index_status VARCHAR(50)
);

SELECT create_hypertable('technical_metrics', 'time', if_not_exists => TRUE);

-- SERP features tracking
CREATE TABLE IF NOT EXISTS serp_features_history (
    time TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    project_id UUID NOT NULL,
    keyword_id UUID NOT NULL,
    keyword VARCHAR(500) NOT NULL,
    feature_type VARCHAR(100) NOT NULL,
    our_position INTEGER,
    competitor_position INTEGER,
    competitor_domain VARCHAR(255),
    feature_data JSONB DEFAULT '{}'
);

SELECT create_hypertable('serp_features_history', 'time', if_not_exists => TRUE);

-- Content performance metrics
CREATE TABLE IF NOT EXISTS content_metrics (
    time TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    project_id UUID NOT NULL,
    url TEXT NOT NULL,
    page_title VARCHAR(500),
    content_type VARCHAR(100),
    word_count INTEGER,
    organic_traffic INTEGER DEFAULT 0,
    avg_position DECIMAL(8,2),
    impressions INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    ctr DECIMAL(5,4),
    bounce_rate DECIMAL(5,4),
    time_on_page INTEGER -- seconds
);

SELECT create_hypertable('content_metrics', 'time', if_not_exists => TRUE);

-- Competitor metrics tracking
CREATE TABLE IF NOT EXISTS competitor_metrics (
    time TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    project_id UUID NOT NULL,
    competitor_domain VARCHAR(255) NOT NULL,
    visibility_score DECIMAL(8,2),
    avg_position DECIMAL(8,2),
    traffic_share DECIMAL(5,4),
    common_keywords INTEGER,
    keyword_gaps INTEGER,
    backlink_count INTEGER,
    referring_domains INTEGER
);

SELECT create_hypertable('competitor_metrics', 'time', if_not_exists => TRUE);

-- Social media metrics
CREATE TABLE IF NOT EXISTS social_metrics (
    time TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    project_id UUID NOT NULL,
    platform VARCHAR(50) NOT NULL,
    followers INTEGER DEFAULT 0,
    engagement_rate DECIMAL(5,4),
    mentions INTEGER DEFAULT 0,
    sentiment_score DECIMAL(3,2), -- -1 to 1
    reach INTEGER DEFAULT 0,
    shares INTEGER DEFAULT 0
);

SELECT create_hypertable('social_metrics', 'time', if_not_exists => TRUE);

-- Performance alerts and anomalies
CREATE TABLE IF NOT EXISTS performance_alerts (
    time TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    project_id UUID NOT NULL,
    alert_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) DEFAULT 'info',
    metric_name VARCHAR(100) NOT NULL,
    current_value DECIMAL(12,4),
    previous_value DECIMAL(12,4),
    threshold_value DECIMAL(12,4),
    change_percentage DECIMAL(5,2),
    description TEXT,
    is_resolved BOOLEAN DEFAULT FALSE
);

SELECT create_hypertable('performance_alerts', 'time', if_not_exists => TRUE);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_ranking_history_project_keyword ON ranking_history (project_id, keyword_id, time DESC);
CREATE INDEX IF NOT EXISTS idx_ranking_history_keyword ON ranking_history (keyword, time DESC);
CREATE INDEX IF NOT EXISTS idx_ranking_history_position ON ranking_history (position, time DESC);

CREATE INDEX IF NOT EXISTS idx_keyword_metrics_project ON keyword_metrics (project_id, time DESC);
CREATE INDEX IF NOT EXISTS idx_keyword_metrics_keyword ON keyword_metrics (keyword_id, time DESC);

CREATE INDEX IF NOT EXISTS idx_traffic_metrics_project ON traffic_metrics (project_id, time DESC);
CREATE INDEX IF NOT EXISTS idx_traffic_metrics_source ON traffic_metrics (source, time DESC);

CREATE INDEX IF NOT EXISTS idx_backlink_metrics_project ON backlink_metrics (project_id, time DESC);

CREATE INDEX IF NOT EXISTS idx_technical_metrics_project ON technical_metrics (project_id, time DESC);
CREATE INDEX IF NOT EXISTS idx_technical_metrics_url ON technical_metrics (url, time DESC);

CREATE INDEX IF NOT EXISTS idx_serp_features_project ON serp_features_history (project_id, time DESC);
CREATE INDEX IF NOT EXISTS idx_serp_features_keyword ON serp_features_history (keyword_id, feature_type, time DESC);

CREATE INDEX IF NOT EXISTS idx_content_metrics_project ON content_metrics (project_id, time DESC);
CREATE INDEX IF NOT EXISTS idx_content_metrics_url ON content_metrics (url, time DESC);

CREATE INDEX IF NOT EXISTS idx_competitor_metrics_project ON competitor_metrics (project_id, time DESC);
CREATE INDEX IF NOT EXISTS idx_competitor_metrics_domain ON competitor_metrics (competitor_domain, time DESC);

CREATE INDEX IF NOT EXISTS idx_social_metrics_project ON social_metrics (project_id, platform, time DESC);

CREATE INDEX IF NOT EXISTS idx_performance_alerts_project ON performance_alerts (project_id, time DESC);
CREATE INDEX IF NOT EXISTS idx_performance_alerts_type ON performance_alerts (alert_type, severity, time DESC);

-- Create continuous aggregates for common queries
CREATE MATERIALIZED VIEW IF NOT EXISTS ranking_daily_summary
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', time) AS day,
    project_id,
    keyword_id,
    keyword,
    AVG(position) AS avg_position,
    MIN(position) AS best_position,
    MAX(position) AS worst_position,
    COUNT(*) AS measurements,
    STDDEV(position) AS position_volatility
FROM ranking_history
GROUP BY day, project_id, keyword_id, keyword
WITH NO DATA;

-- Refresh the continuous aggregate
SELECT add_continuous_aggregate_policy('ranking_daily_summary',
    start_offset => INTERVAL '3 days',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour',
    if_not_exists => TRUE);

-- Weekly ranking summary
CREATE MATERIALIZED VIEW IF NOT EXISTS ranking_weekly_summary
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('7 days', time) AS week,
    project_id,
    keyword_id,
    keyword,
    AVG(position) AS avg_position,
    MIN(position) AS best_position,
    MAX(position) AS worst_position,
    COUNT(*) AS measurements,
    FIRST(position, time) AS start_position,
    LAST(position, time) AS end_position
FROM ranking_history
GROUP BY week, project_id, keyword_id, keyword
WITH NO DATA;

SELECT add_continuous_aggregate_policy('ranking_weekly_summary',
    start_offset => INTERVAL '3 weeks',
    end_offset => INTERVAL '1 day',
    schedule_interval => INTERVAL '1 day',
    if_not_exists => TRUE);

-- Traffic daily summary
CREATE MATERIALIZED VIEW IF NOT EXISTS traffic_daily_summary
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', time) AS day,
    project_id,
    source,
    SUM(sessions) AS total_sessions,
    SUM(users) AS total_users,
    SUM(pageviews) AS total_pageviews,
    AVG(bounce_rate) AS avg_bounce_rate,
    AVG(avg_session_duration) AS avg_session_duration,
    AVG(conversion_rate) AS avg_conversion_rate,
    SUM(revenue) AS total_revenue
FROM traffic_metrics
GROUP BY day, project_id, source
WITH NO DATA;

SELECT add_continuous_aggregate_policy('traffic_daily_summary',
    start_offset => INTERVAL '3 days',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour',
    if_not_exists => TRUE);

-- Set up data retention policies (keep detailed data for 1 year, summaries longer)
SELECT add_retention_policy('ranking_history', INTERVAL '1 year', if_not_exists => TRUE);
SELECT add_retention_policy('keyword_metrics', INTERVAL '1 year', if_not_exists => TRUE);
SELECT add_retention_policy('traffic_metrics', INTERVAL '2 years', if_not_exists => TRUE);
SELECT add_retention_policy('backlink_metrics', INTERVAL '1 year', if_not_exists => TRUE);
SELECT add_retention_policy('technical_metrics', INTERVAL '6 months', if_not_exists => TRUE);
SELECT add_retention_policy('serp_features_history', INTERVAL '1 year', if_not_exists => TRUE);
SELECT add_retention_policy('content_metrics', INTERVAL '1 year', if_not_exists => TRUE);
SELECT add_retention_policy('competitor_metrics', INTERVAL '1 year', if_not_exists => TRUE);
SELECT add_retention_policy('social_metrics', INTERVAL '1 year', if_not_exists => TRUE);
SELECT add_retention_policy('performance_alerts', INTERVAL '6 months', if_not_exists => TRUE);

-- Keep continuous aggregates for 3 years
SELECT add_retention_policy('ranking_daily_summary', INTERVAL '3 years', if_not_exists => TRUE);
SELECT add_retention_policy('ranking_weekly_summary', INTERVAL '5 years', if_not_exists => TRUE);
SELECT add_retention_policy('traffic_daily_summary', INTERVAL '3 years', if_not_exists => TRUE);

-- Insert sample data for development
INSERT INTO ranking_history (project_id, keyword_id, keyword, position, url, search_volume, traffic_estimate)
VALUES 
    ('550e8400-e29b-41d4-a716-446655440000'::uuid, 
     '550e8400-e29b-41d4-a716-446655440001'::uuid, 
     'seo tools', 15, 'https://example.com/seo-tools', 5000, 150),
    ('550e8400-e29b-41d4-a716-446655440000'::uuid, 
     '550e8400-e29b-41d4-a716-446655440002'::uuid, 
     'keyword research', 8, 'https://example.com/keyword-research', 3000, 300),
    ('550e8400-e29b-41d4-a716-446655440000'::uuid, 
     '550e8400-e29b-41d4-a716-446655440003'::uuid, 
     'backlink analysis', 22, 'https://example.com/backlinks', 1200, 80);

-- Refresh continuous aggregates with initial data
CALL refresh_continuous_aggregate('ranking_daily_summary', NULL, NULL);
CALL refresh_continuous_aggregate('ranking_weekly_summary', NULL, NULL);
CALL refresh_continuous_aggregate('traffic_daily_summary', NULL, NULL);

COMMIT;