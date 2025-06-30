-- ClickHouse initialization script for SEO Platform
-- This script creates tables optimized for analytics and big data processing

-- Create database
CREATE DATABASE IF NOT EXISTS seo_analytics;
USE seo_analytics;

-- User events table for tracking user interactions
CREATE TABLE IF NOT EXISTS user_events (
    event_time DateTime DEFAULT now(),
    event_date Date DEFAULT toDate(event_time),
    user_id String,
    session_id String,
    org_id String,
    project_id String,
    event_type String,
    event_action String,
    page_url String,
    referrer String,
    user_agent String,
    ip_address String,
    country String,
    city String,
    device_type String,
    browser String,
    os String,
    screen_resolution String,
    properties Map(String, String)
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(event_date)
ORDER BY (event_date, org_id, project_id, user_id, event_time)
TTL event_date + INTERVAL 2 YEAR;

-- SERP data warehouse for large-scale analysis
CREATE TABLE IF NOT EXISTS serp_data (
    recorded_time DateTime DEFAULT now(),
    recorded_date Date DEFAULT toDate(recorded_time),
    project_id String,
    keyword String,
    location_code UInt32,
    device String,
    position UInt16,
    url String,
    title String,
    meta_description String,
    domain String,
    subdomain String,
    path String,
    serp_features Array(String),
    organic_results UInt16,
    ads_count UInt16,
    total_results UInt64,
    search_volume UInt32,
    difficulty Float32,
    cpc Float32,
    competition Float32
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(recorded_date)
ORDER BY (recorded_date, project_id, keyword, position)
TTL recorded_date + INTERVAL 1 YEAR;

-- Keyword research data for analysis
CREATE TABLE IF NOT EXISTS keyword_research_data (
    collected_time DateTime DEFAULT now(),
    collected_date Date DEFAULT toDate(collected_time),
    seed_keyword String,
    related_keyword String,
    search_volume UInt32,
    keyword_difficulty Float32,
    cpc Float32,
    competition Float32,
    trend_direction Enum8('up' = 1, 'down' = -1, 'stable' = 0),
    monthly_searches Array(UInt32),
    related_questions Array(String),
    location_code UInt32,
    language_code String,
    source String -- dataforseo, semrush, etc.
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(collected_date)
ORDER BY (collected_date, seed_keyword, related_keyword)
TTL collected_date + INTERVAL 6 MONTH;

-- Backlink analysis data
CREATE TABLE IF NOT EXISTS backlink_data (
    crawled_time DateTime DEFAULT now(),
    crawled_date Date DEFAULT toDate(crawled_time),
    project_id String,
    target_domain String,
    source_domain String,
    source_url String,
    target_url String,
    anchor_text String,
    link_type Enum8('dofollow' = 1, 'nofollow' = 0),
    domain_rating UInt8,
    url_rating UInt8,
    traffic_estimate UInt32,
    link_position String,
    first_seen Date,
    last_seen Date,
    is_broken Bool,
    redirect_type String,
    link_attributes Array(String)
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(crawled_date)
ORDER BY (crawled_date, project_id, target_domain, source_domain)
TTL crawled_date + INTERVAL 1 YEAR;

-- Content analysis data
CREATE TABLE IF NOT EXISTS content_analysis_data (
    analyzed_time DateTime DEFAULT now(),
    analyzed_date Date DEFAULT toDate(analyzed_time),
    project_id String,
    url String,
    domain String,
    page_type String,
    title String,
    meta_description String,
    h1_tag String,
    h2_tags Array(String),
    h3_tags Array(String),
    word_count UInt32,
    paragraph_count UInt16,
    image_count UInt16,
    internal_links_count UInt16,
    external_links_count UInt16,
    readability_score Float32,
    seo_score Float32,
    load_time_ms UInt32,
    mobile_friendly Bool,
    keywords_density Map(String, Float32),
    top_keywords Array(String),
    language String,
    charset String
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(analyzed_date)
ORDER BY (analyzed_date, project_id, url)
TTL analyzed_date + INTERVAL 1 YEAR;

-- Competitor analysis aggregated data
CREATE TABLE IF NOT EXISTS competitor_analysis (
    analysis_time DateTime DEFAULT now(),
    analysis_date Date DEFAULT toDate(analysis_time),
    project_id String,
    target_domain String,
    competitor_domain String,
    common_keywords UInt32,
    keyword_gaps UInt32,
    content_gaps UInt32,
    backlink_gaps UInt32,
    traffic_comparison Float32,
    visibility_comparison Float32,
    avg_position_diff Float32,
    strength_score UInt8,
    opportunity_score UInt8,
    competitive_density Float32
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(analysis_date)
ORDER BY (analysis_date, project_id, target_domain, competitor_domain)
TTL analysis_date + INTERVAL 1 YEAR;

-- Technical SEO audit data
CREATE TABLE IF NOT EXISTS technical_seo_data (
    audit_time DateTime DEFAULT now(),
    audit_date Date DEFAULT toDate(audit_time),
    project_id String,
    url String,
    domain String,
    page_type String,
    status_code UInt16,
    load_time_ms UInt32,
    page_size_bytes UInt32,
    compression_enabled Bool,
    ssl_enabled Bool,
    mobile_friendly Bool,
    has_amp Bool,
    structured_data Array(String),
    meta_robots String,
    canonical_url String,
    hreflang Array(String),
    images_without_alt UInt16,
    broken_links UInt16,
    redirect_chains UInt8,
    lighthouse_performance UInt8,
    lighthouse_accessibility UInt8,
    lighthouse_seo UInt8,
    core_web_vitals Map(String, Float32)
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(audit_date)
ORDER BY (audit_date, project_id, url)
TTL audit_date + INTERVAL 6 MONTH;

-- Social media metrics for social SEO
CREATE TABLE IF NOT EXISTS social_media_data (
    collected_time DateTime DEFAULT now(),
    collected_date Date DEFAULT toDate(collected_time),
    project_id String,
    platform String,
    url String,
    shares_count UInt32,
    likes_count UInt32,
    comments_count UInt32,
    engagement_rate Float32,
    reach UInt32,
    impressions UInt32,
    mentions_count UInt32,
    sentiment_score Float32,
    hashtags Array(String),
    top_keywords Array(String)
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(collected_date)
ORDER BY (collected_date, project_id, platform, url)
TTL collected_date + INTERVAL 1 YEAR;

-- API usage analytics
CREATE TABLE IF NOT EXISTS api_usage_analytics (
    request_time DateTime DEFAULT now(),
    request_date Date DEFAULT toDate(request_time),
    org_id String,
    user_id String,
    endpoint String,
    method String,
    status_code UInt16,
    response_time_ms UInt32,
    request_size_bytes UInt32,
    response_size_bytes UInt32,
    ip_address String,
    user_agent String,
    api_key_hash String,
    rate_limit_hit Bool,
    error_message String
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(request_date)
ORDER BY (request_date, org_id, endpoint)
TTL request_date + INTERVAL 3 MONTH;

-- Create materialized views for common aggregations
CREATE MATERIALIZED VIEW IF NOT EXISTS daily_keyword_performance
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(recorded_date)
ORDER BY (recorded_date, project_id, keyword)
AS SELECT
    recorded_date,
    project_id,
    keyword,
    location_code,
    device,
    avg(position) as avg_position,
    min(position) as best_position,
    max(position) as worst_position,
    count(*) as measurements,
    max(search_volume) as search_volume,
    max(difficulty) as difficulty,
    max(cpc) as cpc
FROM serp_data
GROUP BY recorded_date, project_id, keyword, location_code, device;

CREATE MATERIALIZED VIEW IF NOT EXISTS daily_backlink_summary
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(crawled_date)
ORDER BY (crawled_date, project_id, target_domain)
AS SELECT
    crawled_date,
    project_id,
    target_domain,
    count(*) as total_backlinks,
    countIf(link_type = 'dofollow') as dofollow_links,
    countIf(link_type = 'nofollow') as nofollow_links,
    countIf(is_broken = 1) as broken_links,
    uniqExact(source_domain) as referring_domains,
    avg(domain_rating) as avg_domain_rating,
    sum(traffic_estimate) as total_traffic_estimate
FROM backlink_data
GROUP BY crawled_date, project_id, target_domain;

CREATE MATERIALIZED VIEW IF NOT EXISTS hourly_user_activity
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(event_date)
ORDER BY (event_date, toHour(event_time), org_id, project_id)
AS SELECT
    event_date,
    toHour(event_time) as hour,
    org_id,
    project_id,
    event_type,
    count(*) as event_count,
    uniqExact(user_id) as unique_users,
    uniqExact(session_id) as unique_sessions
FROM user_events
GROUP BY event_date, hour, org_id, project_id, event_type;

CREATE MATERIALIZED VIEW IF NOT EXISTS daily_technical_summary
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(audit_date)
ORDER BY (audit_date, project_id, domain)
AS SELECT
    audit_date,
    project_id,
    domain,
    count(*) as pages_audited,
    countIf(status_code = 200) as successful_pages,
    countIf(status_code >= 400) as error_pages,
    countIf(mobile_friendly = 1) as mobile_friendly_pages,
    countIf(ssl_enabled = 1) as ssl_enabled_pages,
    avg(load_time_ms) as avg_load_time,
    avg(lighthouse_performance) as avg_performance_score,
    avg(lighthouse_seo) as avg_seo_score,
    sum(images_without_alt) as total_alt_issues,
    sum(broken_links) as total_broken_links
FROM technical_seo_data
GROUP BY audit_date, project_id, domain;

-- Create dictionaries for fast lookups
CREATE DICTIONARY IF NOT EXISTS country_codes (
    code String,
    name String,
    continent String
) PRIMARY KEY code
SOURCE(HTTP(url 'https://raw.githubusercontent.com/hline/country-list/master/data.json' format 'JSONEachRow'))
LAYOUT(HASHED())
LIFETIME(MIN 86400 MAX 86400);

-- Useful functions for SEO analysis
-- Function to extract domain from URL
CREATE FUNCTION IF NOT EXISTS extractDomain AS (url) -> 
    if(position(url, '://') > 0, 
       extract(substring(url, position(url, '://') + 3), '^[^/]+'), 
       extract(url, '^[^/]+'));

-- Function to calculate keyword density
CREATE FUNCTION IF NOT EXISTS keywordDensity AS (content, keyword, total_words) ->
    if(total_words > 0, 
       (length(content) - length(replaceAll(lower(content), lower(keyword), ''))) / length(keyword) / total_words * 100,
       0);

-- Function to categorize position ranges
CREATE FUNCTION IF NOT EXISTS positionCategory AS (position) ->
    if(position <= 3, 'Top 3',
       if(position <= 10, 'Top 10',
          if(position <= 20, 'Top 20',
             if(position <= 50, 'Top 50', 'Beyond 50'))));

-- Insert sample data for development and testing
INSERT INTO serp_data VALUES
    (now() - INTERVAL 1 DAY, yesterday(), 'test-project-1', 'seo tools', 2840, 'desktop', 15, 'https://example.com/seo-tools', 'Best SEO Tools 2024', 'Discover the best SEO tools...', 'example.com', 'www', '/seo-tools', ['featured_snippet'], 10, 3, 1234567, 5000, 65.5, 2.50, 0.8),
    (now() - INTERVAL 2 DAY, today() - 2, 'test-project-1', 'keyword research', 2840, 'desktop', 8, 'https://example.com/keyword-research', 'Keyword Research Guide', 'Complete guide to keyword research...', 'example.com', 'www', '/keyword-research', ['people_also_ask'], 10, 2, 987654, 3000, 45.2, 1.80, 0.6),
    (now() - INTERVAL 3 DAY, today() - 3, 'test-project-1', 'backlink analysis', 2840, 'mobile', 22, 'https://example.com/backlinks', 'Backlink Analysis Tool', 'Analyze your backlinks...', 'example.com', 'www', '/backlinks', [], 10, 1, 567890, 1200, 72.1, 3.20, 0.9);

INSERT INTO user_events VALUES
    (now() - INTERVAL 1 HOUR, today(), 'user-123', 'session-456', 'org-789', 'test-project-1', 'page_view', 'view', '/dashboard', '', 'Mozilla/5.0...', '192.168.1.1', 'US', 'New York', 'desktop', 'Chrome', 'Windows', '1920x1080', map('page_title', 'SEO Dashboard')),
    (now() - INTERVAL 2 HOUR, today(), 'user-123', 'session-456', 'org-789', 'test-project-1', 'button_click', 'click', '/keywords', '/dashboard', 'Mozilla/5.0...', '192.168.1.1', 'US', 'New York', 'desktop', 'Chrome', 'Windows', '1920x1080', map('button_name', 'Add Keyword'));

COMMIT;