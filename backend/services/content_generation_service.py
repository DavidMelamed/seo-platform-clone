"""
Content Generation Service
AI-powered content generation for SEO optimization
"""

import openai
import asyncio
import re
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import logging
from core.config import settings
from core.redis_client import redis_client

logger = logging.getLogger(__name__)

class ContentGenerationService:
    """AI-powered content generation for SEO"""
    
    def __init__(self):
        self.openai_client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "gpt-4"
        self.max_tokens = 2048
    
    async def generate_blog_post(
        self, 
        topic: str, 
        keywords: List[str], 
        tone: str = "professional",
        length: str = "medium",
        audience: str = "general"
    ) -> Dict[str, Any]:
        """Generate SEO-optimized blog post"""
        
        # Determine word count based on length
        word_counts = {
            "short": "800-1200",
            "medium": "1500-2000", 
            "long": "2500-3500"
        }
        word_count = word_counts.get(length, "1500-2000")
        
        # Create primary and secondary keywords
        primary_keyword = keywords[0] if keywords else topic
        secondary_keywords = keywords[1:6] if len(keywords) > 1 else []
        
        prompt = f"""
        Write a comprehensive, SEO-optimized blog post about "{topic}".
        
        Requirements:
        - Target word count: {word_count} words
        - Tone: {tone}
        - Target audience: {audience}
        - Primary keyword: "{primary_keyword}" (use 3-5 times naturally)
        - Secondary keywords: {', '.join(secondary_keywords)} (use each 1-2 times)
        - Include H1, H2, and H3 headings
        - Include a meta description (150-160 characters)
        - Include a compelling introduction and conclusion
        - Use bullet points or numbered lists where appropriate
        - Include internal linking suggestions (marked with [INTERNAL_LINK: suggestion])
        - Include external linking opportunities (marked with [EXTERNAL_LINK: suggestion])
        
        Structure the response as:
        TITLE: [SEO-optimized title]
        META_DESCRIPTION: [150-160 character meta description]
        CONTENT: [Full blog post content with markdown formatting]
        KEYWORDS_USED: [List of how many times each keyword was used]
        """
        
        try:
            response = await self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert SEO content writer with 10+ years of experience creating high-ranking blog posts."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=3000,
                temperature=0.7
            )
            
            content = response.choices[0].message.content
            
            # Parse the response
            sections = self._parse_blog_post_response(content)
            
            return {
                "content_type": "blog_post",
                "title": sections.get("title", ""),
                "meta_description": sections.get("meta_description", ""),
                "content": sections.get("content", ""),
                "keywords_used": sections.get("keywords_used", {}),
                "word_count": len(sections.get("content", "").split()),
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Blog post generation failed: {str(e)}")
            return {"error": str(e)}
    
    async def generate_meta_description(self, topic: str, keywords: List[str]) -> Dict[str, Any]:
        """Generate SEO-optimized meta description"""
        
        primary_keyword = keywords[0] if keywords else topic
        
        prompt = f"""
        Write 3 different SEO-optimized meta descriptions for a page about "{topic}".
        
        Requirements:
        - Each must be 150-160 characters long
        - Include the primary keyword: "{primary_keyword}"
        - Include a call-to-action
        - Be compelling and click-worthy
        - Match search intent
        
        Format as:
        OPTION_1: [meta description]
        OPTION_2: [meta description]
        OPTION_3: [meta description]
        """
        
        try:
            response = await self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert SEO copywriter specializing in meta descriptions that drive clicks."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.8
            )
            
            content = response.choices[0].message.content
            options = self._parse_meta_description_options(content)
            
            return {
                "content_type": "meta_description",
                "options": options,
                "primary_keyword": primary_keyword,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Meta description generation failed: {str(e)}")
            return {"error": str(e)}
    
    async def generate_titles(self, topic: str, keywords: List[str], count: int = 10) -> Dict[str, Any]:
        """Generate SEO-optimized title variations"""
        
        primary_keyword = keywords[0] if keywords else topic
        
        prompt = f"""
        Generate {count} SEO-optimized title variations for content about "{topic}".
        
        Requirements:
        - Include the primary keyword: "{primary_keyword}"
        - Titles should be 50-60 characters long
        - Mix different title formats: how-to, lists, questions, benefits, etc.
        - Make them compelling and click-worthy
        - Include power words and emotional triggers
        
        Format as a numbered list:
        1. [title]
        2. [title]
        etc.
        """
        
        try:
            response = await self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert SEO copywriter who creates titles that rank #1 on Google."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.9
            )
            
            content = response.choices[0].message.content
            titles = self._parse_title_list(content)
            
            return {
                "content_type": "titles",
                "titles": titles,
                "count": len(titles),
                "primary_keyword": primary_keyword,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Title generation failed: {str(e)}")
            return {"error": str(e)}
    
    async def generate_product_description(
        self, 
        topic: str, 
        keywords: List[str], 
        tone: str = "persuasive"
    ) -> Dict[str, Any]:
        """Generate SEO-optimized product description"""
        
        primary_keyword = keywords[0] if keywords else topic
        secondary_keywords = keywords[1:4] if len(keywords) > 1 else []
        
        prompt = f"""
        Write an SEO-optimized product description for "{topic}".
        
        Requirements:
        - Tone: {tone}
        - Length: 150-300 words
        - Primary keyword: "{primary_keyword}" (use 2-3 times)
        - Secondary keywords: {', '.join(secondary_keywords)} (use naturally)
        - Include key benefits and features
        - Include a compelling call-to-action
        - Format with bullet points for features
        - Include technical specifications if relevant
        
        Structure:
        TITLE: [Product title with primary keyword]
        DESCRIPTION: [Main product description]
        FEATURES: [Bullet points of key features]
        CTA: [Call-to-action]
        """
        
        try:
            response = await self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert e-commerce copywriter who writes product descriptions that convert visitors into customers."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            content = response.choices[0].message.content
            sections = self._parse_product_description_response(content)
            
            return {
                "content_type": "product_description",
                "title": sections.get("title", ""),
                "description": sections.get("description", ""),
                "features": sections.get("features", []),
                "cta": sections.get("cta", ""),
                "word_count": len(sections.get("description", "").split()),
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Product description generation failed: {str(e)}")
            return {"error": str(e)}
    
    async def analyze_seo_score(self, content: str, target_keywords: List[str]) -> Dict[str, Any]:
        """Analyze SEO score of content"""
        
        try:
            # Basic SEO analysis
            word_count = len(content.split())
            
            # Keyword density analysis
            keyword_density = {}
            content_lower = content.lower()
            
            for keyword in target_keywords:
                keyword_lower = keyword.lower()
                count = content_lower.count(keyword_lower)
                density = (count / word_count) * 100 if word_count > 0 else 0
                keyword_density[keyword] = {
                    "count": count,
                    "density": round(density, 2)
                }
            
            # Check for headings
            h1_count = len(re.findall(r'#\s+', content))
            h2_count = len(re.findall(r'##\s+', content))
            h3_count = len(re.findall(r'###\s+', content))
            
            # Calculate base score
            score = 50  # Start with base score
            
            # Word count scoring
            if 800 <= word_count <= 3000:
                score += 20
            elif word_count > 300:
                score += 10
            
            # Keyword density scoring
            primary_keyword = target_keywords[0] if target_keywords else None
            if primary_keyword and primary_keyword in keyword_density:
                density = keyword_density[primary_keyword]["density"]
                if 1 <= density <= 3:
                    score += 20
                elif 0.5 <= density <= 5:
                    score += 10
            
            # Heading structure scoring
            if h1_count >= 1:
                score += 10
            if h2_count >= 2:
                score += 10
            if h3_count >= 1:
                score += 5
            
            # Cap score at 100
            score = min(score, 100)
            
            # Generate suggestions
            suggestions = []
            if word_count < 300:
                suggestions.append("Content is too short. Aim for at least 300 words.")
            if primary_keyword and keyword_density.get(primary_keyword, {}).get("density", 0) < 0.5:
                suggestions.append(f"Increase usage of primary keyword '{primary_keyword}'")
            if h1_count == 0:
                suggestions.append("Add at least one H1 heading")
            if h2_count < 2:
                suggestions.append("Add more H2 headings to improve content structure")
            
            return {
                "score": score,
                "word_count": word_count,
                "keyword_density": keyword_density,
                "headings": {
                    "h1": h1_count,
                    "h2": h2_count,
                    "h3": h3_count
                },
                "suggestions": suggestions,
                "analyzed_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"SEO analysis failed: {str(e)}")
            return {"error": str(e)}
    
    async def generate_chat_response(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI chat response for SEO assistance"""
        
        # Build context for the SEO assistant
        conversation_history = context.get("conversation_history", [])
        user_context = context.get("user_context", {})
        
        # Create system prompt for SEO assistant
        system_prompt = """
        You are an expert SEO consultant with 15+ years of experience. You help users with:
        - Keyword research and strategy
        - Content optimization
        - Technical SEO issues
        - Competitor analysis
        - Link building strategies
        - Local SEO
        - E-commerce SEO
        - SEO audits and recommendations
        
        Provide actionable, specific advice. Include step-by-step instructions when helpful.
        Always consider current SEO best practices and Google algorithm updates.
        Be conversational but professional.
        """
        
        # Build conversation context
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add recent conversation history
        for msg in conversation_history[-5:]:  # Last 5 messages
            role = "assistant" if msg["role"] == "assistant" else "user"
            messages.append({"role": role, "content": msg["message"]})
        
        # Add current message
        messages.append({"role": "user", "content": message})
        
        try:
            response = await self.openai_client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=1000,
                temperature=0.7
            )
            
            ai_response = response.choices[0].message.content
            
            # Generate follow-up suggestions based on the response
            suggestions = await self._generate_follow_up_suggestions(message, ai_response)
            
            return {
                "response": ai_response,
                "suggestions": suggestions,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Chat response generation failed: {str(e)}")
            return {
                "response": "I apologize, but I'm having trouble generating a response right now. Please try again in a moment.",
                "suggestions": [],
                "error": str(e)
            }
    
    async def audit_content(self, url: str) -> Dict[str, Any]:
        """Audit existing content for SEO optimization"""
        
        # This would integrate with web scraping to fetch content
        # For now, return a mock audit structure
        
        return {
            "url": url,
            "seo_score": 75,
            "issues": [
                "Missing meta description",
                "H1 tag not optimized",
                "Image alt tags missing"
            ],
            "recommendations": [
                "Add compelling meta description with target keyword",
                "Optimize H1 tag to include primary keyword",
                "Add descriptive alt text to all images"
            ],
            "keyword_opportunities": [
                "best practices",
                "how to guide",
                "expert tips"
            ],
            "technical_issues": [
                "Page load time: 3.2s (should be < 2s)",
                "No schema markup detected"
            ],
            "content_analysis": {
                "word_count": 850,
                "readability_score": 68,
                "keyword_density": 2.1
            },
            "audited_at": datetime.utcnow().isoformat()
        }
    
    # Helper methods for parsing responses
    def _parse_blog_post_response(self, content: str) -> Dict[str, Any]:
        """Parse blog post generation response"""
        
        sections = {}
        
        # Extract title
        title_match = re.search(r'TITLE:\s*(.+)', content)
        sections["title"] = title_match.group(1).strip() if title_match else ""
        
        # Extract meta description
        meta_match = re.search(r'META_DESCRIPTION:\s*(.+)', content)
        sections["meta_description"] = meta_match.group(1).strip() if meta_match else ""
        
        # Extract main content
        content_match = re.search(r'CONTENT:\s*(.*?)(?=KEYWORDS_USED:|$)', content, re.DOTALL)
        sections["content"] = content_match.group(1).strip() if content_match else ""
        
        # Extract keywords used
        keywords_match = re.search(r'KEYWORDS_USED:\s*(.+)', content)
        if keywords_match:
            try:
                keywords_text = keywords_match.group(1).strip()
                # Parse keyword usage (simplified)
                sections["keywords_used"] = {"parsed": keywords_text}
            except:
                sections["keywords_used"] = {}
        
        return sections
    
    def _parse_meta_description_options(self, content: str) -> List[Dict[str, Any]]:
        """Parse meta description options"""
        
        options = []
        
        for i in range(1, 4):
            pattern = f'OPTION_{i}:\\s*(.+)'
            match = re.search(pattern, content)
            if match:
                desc = match.group(1).strip()
                options.append({
                    "text": desc,
                    "length": len(desc),
                    "option_number": i
                })
        
        return options
    
    def _parse_title_list(self, content: str) -> List[Dict[str, Any]]:
        """Parse title list from response"""
        
        titles = []
        
        # Extract numbered list items
        for match in re.finditer(r'(\d+)\.\s*(.+)', content):
            title_text = match.group(2).strip()
            titles.append({
                "text": title_text,
                "length": len(title_text),
                "number": int(match.group(1))
            })
        
        return titles
    
    def _parse_product_description_response(self, content: str) -> Dict[str, Any]:
        """Parse product description response"""
        
        sections = {}
        
        # Extract title
        title_match = re.search(r'TITLE:\s*(.+)', content)
        sections["title"] = title_match.group(1).strip() if title_match else ""
        
        # Extract description
        desc_match = re.search(r'DESCRIPTION:\s*(.*?)(?=FEATURES:|$)', content, re.DOTALL)
        sections["description"] = desc_match.group(1).strip() if desc_match else ""
        
        # Extract features
        features_match = re.search(r'FEATURES:\s*(.*?)(?=CTA:|$)', content, re.DOTALL)
        if features_match:
            features_text = features_match.group(1).strip()
            # Parse bullet points
            features = [line.strip().lstrip('•-*').strip() 
                       for line in features_text.split('\n') 
                       if line.strip()]
            sections["features"] = features
        else:
            sections["features"] = []
        
        # Extract CTA
        cta_match = re.search(r'CTA:\s*(.+)', content)
        sections["cta"] = cta_match.group(1).strip() if cta_match else ""
        
        return sections
    
    async def _generate_follow_up_suggestions(self, user_message: str, ai_response: str) -> List[str]:
        """Generate follow-up question suggestions"""
        
        # Simple keyword-based suggestions
        suggestions = []
        
        message_lower = user_message.lower()
        
        if "keyword" in message_lower:
            suggestions.extend([
                "How do I check keyword difficulty?",
                "What's the ideal keyword density?",
                "Show me competitor keyword analysis"
            ])
        
        if "content" in message_lower:
            suggestions.extend([
                "How long should my content be?",
                "What's the best content structure for SEO?",
                "How do I optimize for featured snippets?"
            ])
        
        if "backlink" in message_lower or "link" in message_lower:
            suggestions.extend([
                "How do I build high-quality backlinks?",
                "What's a good domain authority score?",
                "How do I find link building opportunities?"
            ])
        
        if "technical" in message_lower or "seo audit" in message_lower:
            suggestions.extend([
                "What are the most important technical SEO factors?",
                "How do I improve page speed?",
                "What's the best way to structure my URLs?"
            ])
        
        # Return up to 3 suggestions
        return suggestions[:3]