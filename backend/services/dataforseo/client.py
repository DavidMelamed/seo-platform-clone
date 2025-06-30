"""
DataForSEO API Client
Handles all integrations with DataForSEO APIs
"""

import aiohttp
import asyncio
import base64
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
from core.config import settings

logger = logging.getLogger(__name__)

class DataForSEOClient:
    """DataForSEO API client for SEO data retrieval"""
    
    def __init__(self):
        self.base_url = "https://api.dataforseo.com"
        self.login = settings.DATAFORSEO_LOGIN
        self.password = settings.DATAFORSEO_PASSWORD
        self.session = None
        
        # Create auth header
        credentials = f"{self.login}:{self.password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        self.headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/json"
        }
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _make_request(self, endpoint: str, method: str = "GET", data: Optional[Dict] = None) -> Dict:
        """Make HTTP request to DataForSEO API"""
        
        if not self.session:
            self.session = aiohttp.ClientSession(headers=self.headers)
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method == "GET":
                async with self.session.get(url) as response:
                    result = await response.json()
            else:
                async with self.session.post(url, json=data) as response:
                    result = await response.json()
            
            if response.status != 200:
                logger.error(f"DataForSEO API error: {response.status} - {result}")
                return {"status_code": response.status, "error": result}
            
            return result
            
        except Exception as e:
            logger.error(f"DataForSEO request failed: {str(e)}")
            return {"error": str(e)}
    
    # Keyword Research APIs
    async def get_keyword_data(self, keywords: List[str], location_code: int = 2840, language_code: str = "en") -> Dict:
        """Get keyword difficulty, search volume, and CPC data"""
        
        tasks = []
        for keyword in keywords:
            task = {
                "keyword": keyword,
                "location_code": location_code,
                "language_code": language_code,
                "device": "desktop",
                "os": "windows"
            }
            tasks.append(task)
        
        payload = tasks
        return await self._make_request("/v3/keywords_data/google/search_volume/live", "POST", payload)
    
    async def get_keyword_suggestions(self, seed_keyword: str, location_code: int = 2840, limit: int = 100) -> Dict:
        """Get keyword suggestions based on seed keyword"""
        
        payload = [{
            "keyword": seed_keyword,
            "location_code": location_code,
            "language_code": "en",
            "limit": limit,
            "include_serp_info": True,
            "include_clickstream_data": True
        }]
        
        return await self._make_request("/v3/keywords_data/google/keyword_suggestions/live", "POST", payload)
    
    async def get_related_keywords(self, keyword: str, location_code: int = 2840, limit: int = 50) -> Dict:
        """Get related keywords and search suggestions"""
        
        payload = [{
            "keyword": keyword,
            "location_code": location_code,
            "language_code": "en",
            "limit": limit
        }]
        
        return await self._make_request("/v3/keywords_data/google/search_suggestions/live", "POST", payload)
    
    # SERP APIs
    async def get_serp_results(self, keyword: str, location_code: int = 2840, device: str = "desktop") -> Dict:
        """Get search engine results page data"""
        
        payload = [{
            "keyword": keyword,
            "location_code": location_code,
            "language_code": "en",
            "device": device,
            "os": "windows" if device == "desktop" else "android",
            "calculate_rectangles": True
        }]
        
        return await self._make_request("/v3/serp/google/organic/live/advanced", "POST", payload)
    
    async def get_serp_features(self, keyword: str, location_code: int = 2840) -> Dict:
        """Get SERP features for a keyword"""
        
        payload = [{
            "keyword": keyword,
            "location_code": location_code,
            "language_code": "en",
            "device": "desktop"
        }]
        
        return await self._make_request("/v3/serp/google/organic/live/advanced", "POST", payload)
    
    # Competitor Analysis APIs
    async def get_competitor_domains(self, domain: str, limit: int = 100) -> Dict:
        """Get competitor domains for a given domain"""
        
        payload = [{
            "target": domain,
            "location_code": 2840,
            "language_code": "en",
            "limit": limit,
            "include_subdomains": True,
            "filters": [
                ["intersection", ">", 5],  # At least 5 common keywords
                ["keywords_count", ">", 100]  # Competitor has at least 100 keywords
            ]
        }]
        
        return await self._make_request("/v3/domain_analytics/google/competitors_domain/live", "POST", payload)
    
    async def get_domain_keywords(self, domain: str, limit: int = 1000) -> Dict:
        """Get all ranking keywords for a domain"""
        
        payload = [{
            "target": domain,
            "location_code": 2840,
            "language_code": "en",
            "limit": limit,
            "order_by": ["search_volume,desc"],
            "filters": [
                ["search_volume", ">", 10],  # Minimum search volume
                ["keyword_difficulty", "<", 80]  # Maximum difficulty
            ]
        }]
        
        return await self._make_request("/v3/domain_analytics/google/organic/live", "POST", payload)
    
    # Backlink APIs
    async def get_backlinks(self, domain: str, limit: int = 1000) -> Dict:
        """Get backlink data for a domain"""
        
        payload = [{
            "target": domain,
            "limit": limit,
            "order_by": ["rank,desc"],
            "filters": [
                ["dofollow", "=", True],  # Only dofollow links
                ["rank", ">", 30]  # Minimum domain rank
            ]
        }]
        
        return await self._make_request("/v3/backlinks/live", "POST", payload)
    
    async def get_referring_domains(self, domain: str, limit: int = 500) -> Dict:
        """Get referring domains for a domain"""
        
        payload = [{
            "target": domain,
            "limit": limit,
            "order_by": ["rank,desc"],
            "filters": [
                ["rank", ">", 20],  # Minimum domain rank
                ["backlinks_count", ">", 5]  # At least 5 backlinks from domain
            ]
        }]
        
        return await self._make_request("/v3/backlinks/referring_domains/live", "POST", payload)
    
    # Technical SEO APIs
    async def get_lighthouse_data(self, url: str) -> Dict:
        """Get Lighthouse performance data for a URL"""
        
        payload = [{
            "url": url,
            "device": "desktop",
            "categories": ["performance", "accessibility", "best-practices", "seo"]
        }]
        
        return await self._make_request("/v3/on_page/lighthouse/live", "POST", payload)
    
    async def get_page_speed_insights(self, url: str) -> Dict:
        """Get PageSpeed Insights data"""
        
        payload = [{
            "url": url,
            "device": "desktop",
            "strategy": "desktop"
        }]
        
        return await self._make_request("/v3/on_page/page_speed_insights/live", "POST", payload)
    
    async def crawl_website(self, domain: str, limit: int = 100) -> Dict:
        """Crawl website for technical SEO analysis"""
        
        payload = [{
            "target": domain,
            "max_crawl_pages": limit,
            "custom_user_agent": "SEO Platform Bot",
            "respect_robots_txt": True,
            "enable_javascript": True,
            "load_resources": True
        }]
        
        return await self._make_request("/v3/on_page/task_post", "POST", payload)
    
    # App Store / Play Store APIs (if needed)
    async def get_app_keywords(self, app_id: str, platform: str = "app_store") -> Dict:
        """Get app store keywords for mobile app"""
        
        if platform == "app_store":
            endpoint = "/v3/app_data/apple/app_store/search/live"
        else:
            endpoint = "/v3/app_data/google/play_store/search/live"
        
        payload = [{
            "app_id": app_id,
            "location_code": 2840,
            "language_code": "en",
            "depth": 100
        }]
        
        return await self._make_request(endpoint, "POST", payload)
    
    # Business Listings APIs
    async def get_business_listings(self, keyword: str, location: str) -> Dict:
        """Get Google My Business listings for local SEO"""
        
        payload = [{
            "keyword": keyword,
            "location_name": location,
            "language_code": "en",
            "device": "desktop",
            "os": "windows"
        }]
        
        return await self._make_request("/v3/business_data/google/my_business/live", "POST", payload)
    
    # Social Media APIs
    async def get_social_mentions(self, keyword: str, platform: str = "all") -> Dict:
        """Get social media mentions and trends"""
        
        # This would integrate with social media APIs
        # For now, return placeholder structure
        return {
            "tasks": [{
                "result": [{
                    "keyword": keyword,
                    "platform": platform,
                    "mentions_count": 0,
                    "sentiment_score": 0.0,
                    "trending_score": 0.0,
                    "top_posts": []
                }]
            }]
        }
    
    # Utility methods
    async def get_locations(self, country_code: str = "US") -> Dict:
        """Get available locations for API requests"""
        
        return await self._make_request(f"/v3/serp/google/locations?country_iso_code={country_code}")
    
    async def get_languages(self) -> Dict:
        """Get available languages for API requests"""
        
        return await self._make_request("/v3/serp/google/languages")
    
    async def check_account_balance(self) -> Dict:
        """Check DataForSEO account balance and usage"""
        
        return await self._make_request("/v3/user/balance")
    
    # Batch processing methods
    async def batch_keyword_analysis(self, keywords: List[str], location_code: int = 2840) -> Dict:
        """Process multiple keywords in batch"""
        
        # Split into batches of 100 (API limit)
        batch_size = 100
        all_results = []
        
        for i in range(0, len(keywords), batch_size):
            batch = keywords[i:i + batch_size]
            
            # Get keyword data
            keyword_data = await self.get_keyword_data(batch, location_code)
            
            # Get SERP data for each keyword
            serp_tasks = []
            for keyword in batch:
                serp_tasks.append(self.get_serp_results(keyword, location_code))
            
            serp_results = await asyncio.gather(*serp_tasks, return_exceptions=True)
            
            # Combine results
            batch_results = {
                "keywords": batch,
                "keyword_data": keyword_data,
                "serp_data": serp_results
            }
            
            all_results.append(batch_results)
            
            # Rate limiting - wait 1 second between batches
            await asyncio.sleep(1)
        
        return {
            "total_keywords": len(keywords),
            "batches_processed": len(all_results),
            "results": all_results
        }
    
    async def comprehensive_domain_analysis(self, domain: str) -> Dict:
        """Comprehensive analysis of a domain"""
        
        # Run multiple analyses in parallel
        tasks = [
            self.get_domain_keywords(domain),
            self.get_competitor_domains(domain),
            self.get_backlinks(domain),
            self.get_referring_domains(domain),
            self.crawl_website(domain)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            "domain": domain,
            "analyzed_at": datetime.utcnow().isoformat(),
            "domain_keywords": results[0] if not isinstance(results[0], Exception) else None,
            "competitors": results[1] if not isinstance(results[1], Exception) else None,
            "backlinks": results[2] if not isinstance(results[2], Exception) else None,
            "referring_domains": results[3] if not isinstance(results[3], Exception) else None,
            "technical_crawl": results[4] if not isinstance(results[4], Exception) else None,
            "errors": [str(r) for r in results if isinstance(r, Exception)]
        }

# Global client instance
_client_instance = None

async def get_dataforseo_client() -> DataForSEOClient:
    """Get or create DataForSEO client instance"""
    global _client_instance
    
    if _client_instance is None:
        _client_instance = DataForSEOClient()
    
    return _client_instance