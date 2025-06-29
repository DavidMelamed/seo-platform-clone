"""
AI Vision Service for Visual SERP Analysis
Uses GPT-4 Vision to analyze screenshots and provide SEO insights
"""

import base64
import httpx
from typing import Dict, List, Optional
from PIL import Image
import io
from openai import AsyncOpenAI
import asyncio
from dataclasses import dataclass
from enum import Enum

@dataclass
class VisualElement:
    """Represents a visual element detected in SERP screenshot"""
    type: str
    position: Dict[str, int]
    content: str
    seo_impact: str
    optimization_suggestion: str

class SERPLayoutPattern(Enum):
    """Common SERP layout patterns"""
    STANDARD = "standard"
    FEATURED_SNIPPET = "featured_snippet"
    LOCAL_PACK = "local_pack"
    KNOWLEDGE_PANEL = "knowledge_panel"
    VIDEO_CAROUSEL = "video_carousel"
    PEOPLE_ALSO_ASK = "people_also_ask"
    IMAGE_PACK = "image_pack"

class AIVisionService:
    def __init__(self, openai_api_key: str):
        self.client = AsyncOpenAI(api_key=openai_api_key)
        
    async def analyze_serp_screenshot(self, image_path: str, keyword: str) -> Dict:
        """Analyze a SERP screenshot using GPT-4 Vision"""
        
        # Encode image to base64
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
        
        # Prepare the prompt
        prompt = f"""
        Analyze this SERP (Search Engine Results Page) screenshot for the keyword "{keyword}".
        
        Please identify and provide insights on:
        1. SERP features present (featured snippets, PAA, local pack, etc.)
        2. Visual hierarchy and layout patterns
        3. Competitor positioning and their visual strategies
        4. Opportunities for optimization
        5. CTR optimization suggestions based on visual elements
        6. Any unique SERP features or anomalies
        
        Format your response as a structured JSON with the following keys:
        - layout_pattern: The dominant SERP layout type
        - serp_features: List of SERP features detected
        - visual_elements: List of key visual elements with positions
        - competitor_analysis: Insights about competitor listings
        - optimization_opportunities: Specific recommendations
        - ctr_suggestions: Click-through rate optimization tips
        - unique_insights: Any special observations
        """
        
        response = await self.client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            max_tokens=2000,
            response_format={"type": "json_object"}
        )
        
        return response.choices[0].message.content
    
    async def analyze_competitor_page_layout(self, screenshot_path: str, competitor_url: str) -> Dict:
        """Analyze competitor page layout for SEO insights"""
        
        with open(screenshot_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
        
        prompt = f"""
        Analyze this competitor webpage screenshot from {competitor_url} for SEO insights.
        
        Focus on:
        1. Content structure and hierarchy (H1, H2, etc.)
        2. Above-the-fold optimization
        3. Call-to-action placement and effectiveness
        4. Visual content usage (images, videos, infographics)
        5. Trust signals and social proof
        6. Mobile responsiveness indicators
        7. Page speed visual indicators
        8. Internal linking patterns
        
        Provide actionable recommendations to outperform this competitor.
        """
        
        response = await self.client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            max_tokens=2000
        )
        
        return {
            "competitor_url": competitor_url,
            "analysis": response.choices[0].message.content,
            "timestamp": asyncio.get_event_loop().time()
        }
    
    async def generate_visual_content_suggestions(self, 
                                                 current_screenshot: str,
                                                 top_competitors: List[str]) -> Dict:
        """Generate visual content suggestions based on SERP analysis"""
        
        # Analyze current page
        current_analysis = await self.analyze_serp_screenshot(
            current_screenshot, 
            "current_page"
        )
        
        # Analyze top competitors
        competitor_insights = []
        for comp_screenshot in top_competitors:
            analysis = await self.analyze_competitor_page_layout(
                comp_screenshot,
                f"competitor_{len(competitor_insights) + 1}"
            )
            competitor_insights.append(analysis)
        
        # Generate recommendations
        recommendations = {
            "visual_elements_to_add": [],
            "layout_improvements": [],
            "content_gaps": [],
            "ctr_optimization": [],
            "mobile_considerations": []
        }
        
        # AI-powered recommendation synthesis
        synthesis_prompt = f"""
        Based on the current page analysis and competitor insights, 
        provide specific visual content recommendations:
        
        Current page: {current_analysis}
        Competitors: {competitor_insights}
        
        Generate actionable visual SEO improvements.
        """
        
        synthesis = await self.client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[{"role": "user", "content": synthesis_prompt}],
            max_tokens=1000
        )
        
        recommendations["ai_synthesis"] = synthesis.choices[0].message.content
        
        return recommendations
    
    async def detect_serp_changes(self, 
                                  previous_screenshot: str,
                                  current_screenshot: str,
                                  keyword: str) -> Dict:
        """Detect changes between SERP screenshots over time"""
        
        # Encode both images
        with open(previous_screenshot, "rb") as f:
            prev_base64 = base64.b64encode(f.read()).decode('utf-8')
        
        with open(current_screenshot, "rb") as f:
            curr_base64 = base64.b64encode(f.read()).decode('utf-8')
        
        prompt = f"""
        Compare these two SERP screenshots for the keyword "{keyword}" and identify:
        
        1. Ranking position changes
        2. New SERP features added/removed
        3. Competitor movements
        4. Visual layout changes
        5. Content updates in snippets
        6. Any algorithm update indicators
        
        Provide a detailed change analysis with SEO implications.
        """
        
        response = await self.client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{prev_base64}",
                                "detail": "high"
                            }
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{curr_base64}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            max_tokens=2000
        )
        
        return {
            "keyword": keyword,
            "changes_detected": response.choices[0].message.content,
            "alert_level": self._determine_alert_level(response.choices[0].message.content)
        }
    
    def _determine_alert_level(self, changes: str) -> str:
        """Determine alert level based on detected changes"""
        # Simple keyword-based alert level detection
        critical_keywords = ["major drop", "lost position", "competitor overtook", "lost snippet"]
        warning_keywords = ["slight drop", "new competitor", "layout change"]
        
        changes_lower = changes.lower()
        
        if any(keyword in changes_lower for keyword in critical_keywords):
            return "critical"
        elif any(keyword in changes_lower for keyword in warning_keywords):
            return "warning"
        else:
            return "info"

# Usage example
async def main():
    service = AIVisionService(openai_api_key="your-api-key")
    
    # Analyze SERP screenshot
    serp_analysis = await service.analyze_serp_screenshot(
        "screenshots/serp_seo_tools.png",
        "seo tools"
    )
    print("SERP Analysis:", serp_analysis)
    
    # Analyze competitor layout
    competitor_analysis = await service.analyze_competitor_page_layout(
        "screenshots/competitor_homepage.png",
        "https://competitor.com"
    )
    print("Competitor Analysis:", competitor_analysis)
    
    # Detect SERP changes
    changes = await service.detect_serp_changes(
        "screenshots/serp_yesterday.png",
        "screenshots/serp_today.png",
        "seo tools"
    )
    print("SERP Changes:", changes)

if __name__ == "__main__":
    asyncio.run(main())