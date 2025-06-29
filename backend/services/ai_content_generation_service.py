"""
AI Content Generation Service
SEO-optimized content creation with multiple language support
"""

import asyncio
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import openai
from anthropic import AsyncAnthropic
import json
import re
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Pinecone
import pinecone
import nltk
from textstat import flesch_reading_ease, flesch_kincaid_grade
import yake
from transformers import pipeline

class ContentType(Enum):
    """Types of content that can be generated"""
    BLOG_POST = "blog_post"
    PRODUCT_DESCRIPTION = "product_description"
    LANDING_PAGE = "landing_page"
    META_DESCRIPTION = "meta_description"
    TITLE_TAG = "title_tag"
    FAQ_SCHEMA = "faq_schema"
    EMAIL_CAMPAIGN = "email_campaign"
    SOCIAL_MEDIA = "social_media"
    PRESS_RELEASE = "press_release"
    CASE_STUDY = "case_study"

class ToneOfVoice(Enum):
    """Content tone options"""
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    FRIENDLY = "friendly"
    AUTHORITATIVE = "authoritative"
    CONVERSATIONAL = "conversational"
    TECHNICAL = "technical"
    PERSUASIVE = "persuasive"
    EDUCATIONAL = "educational"

@dataclass
class ContentRequest:
    """Content generation request structure"""
    content_type: ContentType
    primary_keyword: str
    secondary_keywords: List[str]
    tone: ToneOfVoice
    length: int  # word count
    language: str
    target_audience: str
    competitor_urls: Optional[List[str]] = None
    outline: Optional[List[str]] = None
    seo_guidelines: Optional[Dict] = None

@dataclass
class GeneratedContent:
    """Generated content with SEO metadata"""
    content: str
    title: str
    meta_description: str
    word_count: int
    reading_level: str
    keyword_density: Dict[str, float]
    seo_score: float
    suggestions: List[str]
    outline_used: List[str]
    internal_links: List[Dict[str, str]]
    external_links: List[Dict[str, str]]
    schema_markup: Optional[Dict] = None

class AIContentGenerationService:
    def __init__(self, openai_key: str, anthropic_key: str, pinecone_key: str):
        self.openai_client = openai.AsyncOpenAI(api_key=openai_key)
        self.anthropic_client = AsyncAnthropic(api_key=anthropic_key)
        
        # Initialize Pinecone for content similarity
        pinecone.init(api_key=pinecone_key, environment="us-east-1-aws")
        self.embeddings = OpenAIEmbeddings(openai_api_key=openai_key)
        
        # Initialize NLP tools
        nltk.download('punkt', quiet=True)
        nltk.download('stopwords', quiet=True)
        self.sentiment_analyzer = pipeline("sentiment-analysis")
        
        # Keyword extractor
        self.keyword_extractor = yake.KeywordExtractor(
            lan="en",
            n=3,
            dedupLim=0.7,
            top=20
        )
        
    async def generate_content(self, request: ContentRequest) -> GeneratedContent:
        """Generate SEO-optimized content based on request"""
        
        # Research phase - analyze competitors if provided
        competitor_insights = None
        if request.competitor_urls:
            competitor_insights = await self._analyze_competitors(request.competitor_urls)
        
        # Generate content outline
        outline = request.outline or await self._generate_outline(
            request,
            competitor_insights
        )
        
        # Generate the main content
        content = await self._generate_main_content(request, outline, competitor_insights)
        
        # Optimize content for SEO
        optimized_content = await self._optimize_content(content, request)
        
        # Generate metadata
        title = await self._generate_title(request, optimized_content)
        meta_description = await self._generate_meta_description(request, optimized_content)
        
        # Calculate SEO metrics
        seo_metrics = self._calculate_seo_metrics(optimized_content, request)
        
        # Generate internal linking suggestions
        internal_links = await self._suggest_internal_links(optimized_content, request)
        
        # Generate schema markup if applicable
        schema_markup = await self._generate_schema_markup(request, optimized_content)
        
        return GeneratedContent(
            content=optimized_content,
            title=title,
            meta_description=meta_description,
            word_count=len(optimized_content.split()),
            reading_level=self._calculate_reading_level(optimized_content),
            keyword_density=seo_metrics['keyword_density'],
            seo_score=seo_metrics['seo_score'],
            suggestions=seo_metrics['suggestions'],
            outline_used=outline,
            internal_links=internal_links,
            external_links=seo_metrics['external_links'],
            schema_markup=schema_markup
        )
    
    async def _generate_outline(self, 
                              request: ContentRequest,
                              competitor_insights: Optional[Dict]) -> List[str]:
        """Generate content outline based on SEO best practices"""
        
        competitor_context = ""
        if competitor_insights:
            competitor_context = f"""
            Competitor analysis shows these common topics:
            {json.dumps(competitor_insights['common_topics'], indent=2)}
            
            Content gaps identified:
            {json.dumps(competitor_insights['content_gaps'], indent=2)}
            """
        
        prompt = f"""
        Create a comprehensive outline for a {request.content_type.value} about "{request.primary_keyword}".
        
        Target audience: {request.target_audience}
        Tone: {request.tone.value}
        Target length: {request.length} words
        Secondary keywords to include: {', '.join(request.secondary_keywords)}
        
        {competitor_context}
        
        Create an SEO-optimized outline that:
        1. Naturally incorporates all keywords
        2. Follows a logical flow
        3. Addresses search intent
        4. Includes sections that would earn featured snippets
        5. Has clear H2 and H3 structure
        
        Format as a JSON list of sections with titles and key points.
        """
        
        response = await self.openai_client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        outline_data = json.loads(response.choices[0].message.content)
        return outline_data.get('outline', [])
    
    async def _generate_main_content(self,
                                   request: ContentRequest,
                                   outline: List[str],
                                   competitor_insights: Optional[Dict]) -> str:
        """Generate the main content using Claude for better long-form content"""
        
        # Build context from competitor insights
        context = ""
        if competitor_insights:
            context = f"""
            Based on competitor analysis:
            - Average content length: {competitor_insights.get('avg_length', 'N/A')} words
            - Common topics covered: {', '.join(competitor_insights.get('common_topics', [])[:5])}
            - Unique angle to take: Focus on {competitor_insights.get('content_gaps', ['practical examples'])[0]}
            """
        
        prompt = f"""
        Write a comprehensive {request.content_type.value} about "{request.primary_keyword}".
        
        Outline to follow:
        {json.dumps(outline, indent=2)}
        
        Requirements:
        - Target audience: {request.target_audience}
        - Tone of voice: {request.tone.value}
        - Length: {request.length} words
        - Primary keyword: {request.primary_keyword}
        - Secondary keywords: {', '.join(request.secondary_keywords)}
        - Language: {request.language}
        
        {context}
        
        SEO Guidelines:
        1. Use the primary keyword in the first 100 words
        2. Include secondary keywords naturally throughout
        3. Write scannable content with short paragraphs
        4. Include relevant statistics and examples
        5. Add a compelling introduction and conclusion
        6. Use transition words for better flow
        7. Optimize for featured snippets where possible
        
        Write engaging, informative content that provides real value while being optimized for search engines.
        """
        
        # Use Claude for better long-form content
        response = await self.anthropic_client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=4000,
            temperature=0.7,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.content[0].text
    
    async def _optimize_content(self, content: str, request: ContentRequest) -> str:
        """Optimize content for SEO"""
        
        # Check keyword density
        keyword_density = self._calculate_keyword_density(content, request)
        
        # Add keywords if density is too low
        optimized_content = content
        
        for keyword, density in keyword_density.items():
            if density < 0.5:  # Less than 0.5%
                # Find places to naturally add the keyword
                optimized_content = await self._add_keyword_naturally(
                    optimized_content,
                    keyword,
                    target_density=1.0
                )
        
        # Ensure proper heading structure
        optimized_content = self._optimize_heading_structure(optimized_content)
        
        # Add internal linking placeholders
        optimized_content = self._add_link_placeholders(optimized_content)
        
        # Optimize for featured snippets
        optimized_content = self._optimize_for_featured_snippets(optimized_content)
        
        return optimized_content
    
    async def _generate_title(self, request: ContentRequest, content: str) -> str:
        """Generate SEO-optimized title tag"""
        
        prompt = f"""
        Generate an SEO-optimized title tag for this content about "{request.primary_keyword}".
        
        Requirements:
        - Include the primary keyword
        - 50-60 characters ideal length
        - Compelling and click-worthy
        - Match search intent
        - Include power words or numbers if relevant
        
        Content summary: {content[:500]}...
        
        Generate 3 title options and pick the best one.
        """
        
        response = await self.openai_client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8
        )
        
        return response.choices[0].message.content.strip()
    
    async def _generate_meta_description(self, request: ContentRequest, content: str) -> str:
        """Generate SEO-optimized meta description"""
        
        prompt = f"""
        Generate an SEO-optimized meta description for this content about "{request.primary_keyword}".
        
        Requirements:
        - Include the primary keyword naturally
        - 150-160 characters ideal length
        - Compelling call-to-action
        - Accurately summarize the content
        - Include a benefit or value proposition
        
        Content summary: {content[:800]}...
        """
        
        response = await self.openai_client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
    
    async def _generate_schema_markup(self, request: ContentRequest, content: str) -> Optional[Dict]:
        """Generate appropriate schema markup"""
        
        schema_map = {
            ContentType.BLOG_POST: "Article",
            ContentType.FAQ_SCHEMA: "FAQPage",
            ContentType.PRODUCT_DESCRIPTION: "Product",
            ContentType.CASE_STUDY: "Article",
            ContentType.PRESS_RELEASE: "NewsArticle"
        }
        
        schema_type = schema_map.get(request.content_type)
        if not schema_type:
            return None
        
        if request.content_type == ContentType.FAQ_SCHEMA:
            return self._generate_faq_schema(content)
        
        # Generate general schema
        schema = {
            "@context": "https://schema.org",
            "@type": schema_type,
            "headline": await self._generate_title(request, content),
            "description": await self._generate_meta_description(request, content),
            "keywords": f"{request.primary_keyword}, {', '.join(request.secondary_keywords)}",
            "wordCount": len(content.split()),
            "author": {
                "@type": "Organization",
                "name": "Your Company"
            },
            "datePublished": "2024-06-29",
            "dateModified": "2024-06-29"
        }
        
        return schema
    
    def _generate_faq_schema(self, content: str) -> Dict:
        """Extract FAQ schema from content"""
        
        # Simple pattern matching for Q&A format
        qa_pattern = r'(?:Q:|Question:)\s*(.+?)(?:\n|$)(?:A:|Answer:)\s*(.+?)(?=(?:Q:|Question:|$))'
        matches = re.findall(qa_pattern, content, re.DOTALL | re.IGNORECASE)
        
        if not matches:
            return None
        
        faq_schema = {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": []
        }
        
        for question, answer in matches:
            faq_schema["mainEntity"].append({
                "@type": "Question",
                "name": question.strip(),
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": answer.strip()
                }
            })
        
        return faq_schema
    
    def _calculate_seo_metrics(self, content: str, request: ContentRequest) -> Dict:
        """Calculate comprehensive SEO metrics"""
        
        # Keyword density
        keyword_density = self._calculate_keyword_density(content, request)
        
        # Reading level
        reading_ease = flesch_reading_ease(content)
        grade_level = flesch_kincaid_grade(content)
        
        # Content structure analysis
        headings = re.findall(r'<h[1-6]>(.*?)</h[1-6]>', content, re.IGNORECASE)
        paragraphs = content.split('\n\n')
        avg_paragraph_length = sum(len(p.split()) for p in paragraphs) / len(paragraphs) if paragraphs else 0
        
        # SEO score calculation (0-100)
        seo_score = 0
        suggestions = []
        
        # Keyword optimization (30 points)
        primary_density = keyword_density.get(request.primary_keyword.lower(), 0)
        if 0.5 <= primary_density <= 2.5:
            seo_score += 30
        else:
            seo_score += 15
            suggestions.append(f"Adjust primary keyword density (current: {primary_density:.1f}%)")
        
        # Content length (20 points)
        word_count = len(content.split())
        if word_count >= request.length * 0.9:
            seo_score += 20
        else:
            seo_score += 10
            suggestions.append(f"Increase content length (current: {word_count}, target: {request.length})")
        
        # Readability (20 points)
        if 60 <= reading_ease <= 70:
            seo_score += 20
        elif 50 <= reading_ease <= 80:
            seo_score += 15
        else:
            seo_score += 10
            suggestions.append(f"Improve readability (current score: {reading_ease:.1f})")
        
        # Structure (15 points)
        if len(headings) >= 3 and avg_paragraph_length <= 150:
            seo_score += 15
        else:
            seo_score += 8
            suggestions.append("Improve content structure with more headings and shorter paragraphs")
        
        # Internal/External links (15 points)
        internal_links = len(re.findall(r'\[INTERNAL_LINK:.*?\]', content))
        external_links = len(re.findall(r'\[EXTERNAL_LINK:.*?\]', content))
        
        if internal_links >= 2 and external_links >= 1:
            seo_score += 15
        else:
            seo_score += 7
            suggestions.append("Add more internal and external links")
        
        return {
            'seo_score': seo_score,
            'keyword_density': keyword_density,
            'reading_ease': reading_ease,
            'grade_level': grade_level,
            'suggestions': suggestions,
            'external_links': []  # To be populated by link finder
        }
    
    def _calculate_keyword_density(self, content: str, request: ContentRequest) -> Dict[str, float]:
        """Calculate keyword density for all target keywords"""
        
        # Clean content
        clean_content = re.sub(r'<[^>]+>', '', content).lower()
        words = clean_content.split()
        total_words = len(words)
        
        densities = {}
        
        # Check primary keyword
        primary_count = clean_content.count(request.primary_keyword.lower())
        densities[request.primary_keyword.lower()] = (primary_count / total_words) * 100 if total_words > 0 else 0
        
        # Check secondary keywords
        for keyword in request.secondary_keywords:
            count = clean_content.count(keyword.lower())
            densities[keyword.lower()] = (count / total_words) * 100 if total_words > 0 else 0
        
        return densities
    
    def _calculate_reading_level(self, content: str) -> str:
        """Calculate and return reading level description"""
        
        grade = flesch_kincaid_grade(content)
        
        if grade < 6:
            return "Elementary"
        elif grade < 9:
            return "Middle School"
        elif grade < 13:
            return "High School"
        elif grade < 16:
            return "College"
        else:
            return "Graduate"
    
    async def _suggest_internal_links(self, content: str, request: ContentRequest) -> List[Dict[str, str]]:
        """Suggest internal linking opportunities"""
        
        # Extract key phrases that could be linked
        keywords = self.keyword_extractor.extract_keywords(content)
        
        # Simulate internal link suggestions (in production, query your content database)
        suggestions = []
        for keyword, score in keywords[:10]:
            if score < 0.3:  # High relevance
                suggestions.append({
                    "anchor_text": keyword,
                    "suggested_url": f"/blog/{keyword.replace(' ', '-').lower()}",
                    "relevance_score": 1 - score
                })
        
        return suggestions
    
    def _optimize_heading_structure(self, content: str) -> str:
        """Ensure proper H1-H6 hierarchy"""
        # Implementation would analyze and fix heading structure
        return content
    
    def _add_link_placeholders(self, content: str) -> str:
        """Add placeholders for internal/external links"""
        # Implementation would intelligently add link placeholders
        return content
    
    def _optimize_for_featured_snippets(self, content: str) -> str:
        """Optimize content sections for featured snippets"""
        # Implementation would format content for snippet eligibility
        return content
    
    async def _add_keyword_naturally(self, content: str, keyword: str, target_density: float) -> str:
        """Add keywords naturally to reach target density"""
        # Implementation would use NLP to find natural insertion points
        return content
    
    async def _analyze_competitors(self, urls: List[str]) -> Dict:
        """Analyze competitor content for insights"""
        # Implementation would scrape and analyze competitor content
        return {
            'common_topics': ['topic1', 'topic2'],
            'content_gaps': ['gap1', 'gap2'],
            'avg_length': 2000
        }

# Usage example
async def generate_blog_post():
    service = AIContentGenerationService(
        openai_key="your-key",
        anthropic_key="your-key",
        pinecone_key="your-key"
    )
    
    request = ContentRequest(
        content_type=ContentType.BLOG_POST,
        primary_keyword="best seo tools 2024",
        secondary_keywords=["seo software", "keyword research tools", "backlink checkers"],
        tone=ToneOfVoice.EDUCATIONAL,
        length=2000,
        language="en",
        target_audience="Digital marketers and SEO professionals",
        competitor_urls=[
            "https://competitor1.com/seo-tools",
            "https://competitor2.com/best-seo-software"
        ]
    )
    
    generated = await service.generate_content(request)
    
    print(f"Title: {generated.title}")
    print(f"Meta Description: {generated.meta_description}")
    print(f"SEO Score: {generated.seo_score}/100")
    print(f"Word Count: {generated.word_count}")
    print(f"Reading Level: {generated.reading_level}")
    print("\nSuggestions:")
    for suggestion in generated.suggestions:
        print(f"- {suggestion}")

if __name__ == "__main__":
    asyncio.run(generate_blog_post())