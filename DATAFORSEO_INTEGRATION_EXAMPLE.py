#!/usr/bin/env python3
"""
DataForSEO Integration Example
This demonstrates how to use DataForSEO APIs for the SEO platform
"""

import asyncio
import httpx
import json
from typing import Dict, List
import os
from datetime import datetime

class DataForSEOExample:
    def __init__(self, login: str, password: str):
        self.base_url = "https://api.dataforseo.com/v3"
        self.auth = (login, password)
        
    async def example_keyword_research(self, keywords: List[str]):
        """Example: Get keyword data including search volume, CPC, competition"""
        print("\n🔍 KEYWORD RESEARCH EXAMPLE")
        print("=" * 50)
        
        endpoint = f"{self.base_url}/keywords_data/google/search_volume/live"
        
        payload = [{
            "keywords": keywords,
            "location_name": "United States",
            "language_name": "English"
        }]
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                endpoint,
                json=payload,
                auth=self.auth,
                timeout=30.0
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("tasks") and data["tasks"][0].get("result"):
                    for item in data["tasks"][0]["result"]:
                        print(f"\nKeyword: {item['keyword']}")
                        print(f"Search Volume: {item.get('search_volume', 'N/A')}")
                        print(f"Competition: {item.get('competition', 'N/A')}")
                        print(f"CPC: ${item.get('cpc', 0):.2f}")
            else:
                print(f"Error: {response.status_code}")
                
    async def example_serp_analysis(self, keyword: str):
        """Example: Get SERP data for competitive analysis"""
        print("\n📊 SERP ANALYSIS EXAMPLE")
        print("=" * 50)
        
        endpoint = f"{self.base_url}/serp/google/organic/live/advanced"
        
        payload = [{
            "keyword": keyword,
            "location_name": "United States",
            "language_name": "English",
            "device": "desktop",
            "depth": 10  # Top 10 results
        }]
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                endpoint,
                json=payload,
                auth=self.auth,
                timeout=30.0
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("tasks") and data["tasks"][0].get("result"):
                    items = data["tasks"][0]["result"][0].get("items", [])
                    print(f"\nTop 10 Results for '{keyword}':")
                    for i, item in enumerate(items[:10], 1):
                        if item["type"] == "organic":
                            print(f"\n{i}. {item.get('title', 'N/A')}")
                            print(f"   URL: {item.get('url', 'N/A')}")
                            print(f"   Domain: {item.get('domain', 'N/A')}")
            else:
                print(f"Error: {response.status_code}")
                
    async def example_backlink_analysis(self, domain: str):
        """Example: Get backlink data for a domain"""
        print("\n🔗 BACKLINK ANALYSIS EXAMPLE")
        print("=" * 50)
        
        endpoint = f"{self.base_url}/backlinks/summary/live"
        
        payload = [{
            "target": domain,
            "mode": "as_is"
        }]
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                endpoint,
                json=payload,
                auth=self.auth,
                timeout=30.0
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("tasks") and data["tasks"][0].get("result"):
                    result = data["tasks"][0]["result"][0]
                    print(f"\nBacklink Profile for {domain}:")
                    print(f"Total Backlinks: {result.get('backlinks', 0):,}")
                    print(f"Referring Domains: {result.get('referring_domains', 0):,}")
                    print(f"Referring IPs: {result.get('referring_ips', 0):,}")
                    print(f"Broken Backlinks: {result.get('broken_backlinks', 0):,}")
            else:
                print(f"Error: {response.status_code}")
                
    async def example_site_audit(self, domain: str):
        """Example: Get on-page SEO data"""
        print("\n🔍 SITE AUDIT EXAMPLE")
        print("=" * 50)
        
        endpoint = f"{self.base_url}/on_page/summary"
        
        payload = [{
            "target": domain,
            "max_crawl_pages": 100
        }]
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                endpoint,
                json=payload,
                auth=self.auth,
                timeout=30.0
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"\nSite Audit initiated for {domain}")
                print("Task ID:", data.get("tasks", [{}])[0].get("id"))
                print("Note: Site audits run asynchronously. Check task status for results.")
            else:
                print(f"Error: {response.status_code}")

async def main():
    """Run DataForSEO examples"""
    
    # NOTE: Replace with your actual DataForSEO credentials
    LOGIN = os.getenv("DATAFORSEO_LOGIN", "your_login_here")
    PASSWORD = os.getenv("DATAFORSEO_PASSWORD", "your_password_here")
    
    if LOGIN == "your_login_here":
        print("⚠️  Please set your DataForSEO credentials in the environment variables:")
        print("export DATAFORSEO_LOGIN='your_login'")
        print("export DATAFORSEO_PASSWORD='your_password'")
        return
    
    client = DataForSEOExample(LOGIN, PASSWORD)
    
    print("🚀 DataForSEO Integration Examples")
    print("=" * 50)
    
    # Example 1: Keyword Research
    keywords = ["seo tools", "keyword research", "backlink analysis"]
    await client.example_keyword_research(keywords)
    
    # Example 2: SERP Analysis
    await client.example_serp_analysis("best seo tools")
    
    # Example 3: Backlink Analysis
    await client.example_backlink_analysis("ahrefs.com")
    
    # Example 4: Site Audit
    await client.example_site_audit("example.com")
    
    print("\n\n✅ Examples completed!")
    print("\nIntegration Ideas for SEO Platform:")
    print("1. Cache frequently requested data in Redis")
    print("2. Use Celery for async processing of bulk requests")
    print("3. Store historical data in TimescaleDB for trends")
    print("4. Implement rate limiting to manage API costs")
    print("5. Build ML models on top of collected data")

if __name__ == "__main__":
    asyncio.run(main())