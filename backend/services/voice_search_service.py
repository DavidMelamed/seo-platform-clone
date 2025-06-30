"""
Voice Search Optimization Service
Optimizes content for voice search and conversational queries
"""

import asyncio
import re
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import openai
from core.config import settings
from core.redis_client import redis_client

logger = logging.getLogger(__name__)

class VoiceSearchService:
    """Service for optimizing content for voice search"""
    
    def __init__(self):
        self.openai_client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "gpt-4"
    
    async def optimize_for_voice(
        self,
        content: str,
        target_queries: List[str],
        location: Optional[str] = None,
        language: str = "en"
    ) -> Dict[str, Any]:
        """Optimize content for voice search queries"""
        
        try:
            # Analyze current content
            content_analysis = await self._analyze_content_for_voice(content)
            
            # Generate voice-optimized snippets
            voice_snippets = await self._generate_voice_snippets(
                content, 
                target_queries, 
                location
            )
            
            # Create FAQ schema
            faq_schema = await self._generate_faq_schema(content, target_queries)
            
            # Generate natural language variations
            nlp_variations = await self._generate_nlp_variations(target_queries)
            
            # Optimize content structure
            optimized_content = await self._optimize_content_structure(
                content,
                voice_snippets,
                target_queries
            )
            
            # Calculate optimization score
            score = self._calculate_voice_optimization_score(
                optimized_content,
                voice_snippets,
                faq_schema
            )
            
            return {
                "optimized_content": optimized_content,
                "voice_snippets": voice_snippets,
                "faq_schema": faq_schema,
                "natural_language_variations": nlp_variations,
                "score": score,
                "analysis": content_analysis,
                "recommendations": await self._generate_recommendations(
                    content_analysis,
                    score
                )
            }
            
        except Exception as e:
            logger.error(f"Voice optimization failed: {str(e)}")
            raise
    
    async def _analyze_content_for_voice(self, content: str) -> Dict[str, Any]:
        """Analyze content for voice search compatibility"""
        
        analysis = {
            "conversational_tone": 0,
            "question_answers": 0,
            "natural_language": 0,
            "local_relevance": 0,
            "featured_snippet_potential": 0
        }
        
        # Check for conversational tone
        conversational_patterns = [
            r'\b(you|your|we|our|us)\b',
            r'\b(how|what|when|where|why|who)\b',
            r'\b(can|could|would|should)\b'
        ]
        
        for pattern in conversational_patterns:
            matches = len(re.findall(pattern, content, re.IGNORECASE))
            analysis["conversational_tone"] += matches
        
        # Check for Q&A format
        question_patterns = [
            r'[^.!?]*\?',  # Questions
            r'\b(answer|solution|tip|guide)\b'
        ]
        
        for pattern in question_patterns:
            matches = len(re.findall(pattern, content, re.IGNORECASE))
            analysis["question_answers"] += matches
        
        # Natural language score
        word_count = len(content.split())
        avg_sentence_length = word_count / max(content.count('.'), 1)
        
        if 15 <= avg_sentence_length <= 25:
            analysis["natural_language"] = 80
        elif 10 <= avg_sentence_length <= 30:
            analysis["natural_language"] = 60
        else:
            analysis["natural_language"] = 40
        
        # Featured snippet potential
        if analysis["question_answers"] > 0 and word_count > 50:
            analysis["featured_snippet_potential"] = 70
        
        return analysis
    
    async def _generate_voice_snippets(
        self,
        content: str,
        target_queries: List[str],
        location: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """Generate voice-optimized snippets for target queries"""
        
        snippets = []
        
        for query in target_queries:
            prompt = f"""
            Create a voice search optimized answer for: "{query}"
            
            Context from content: {content[:500]}...
            
            Requirements:
            - Answer in 40-50 words (perfect for voice assistants)
            - Use natural, conversational language
            - Start with a direct answer
            - Include the question keywords naturally
            - Be informative and helpful
            {f"- Include local context for: {location}" if location else ""}
            
            Format: Just the answer text, no labels or formatting.
            """
            
            try:
                response = await self.openai_client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are an expert at creating voice search optimized content."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=150,
                    temperature=0.7
                )
                
                snippet_text = response.choices[0].message.content.strip()
                
                snippets.append({
                    "query": query,
                    "snippet": snippet_text,
                    "word_count": len(snippet_text.split()),
                    "location": location
                })
                
            except Exception as e:
                logger.error(f"Failed to generate snippet for '{query}': {str(e)}")
                continue
        
        return snippets
    
    async def _generate_faq_schema(
        self,
        content: str,
        target_queries: List[str]
    ) -> Dict[str, Any]:
        """Generate FAQ schema markup for voice search"""
        
        prompt = f"""
        Create FAQ schema markup based on these queries: {', '.join(target_queries)}
        
        Content context: {content[:1000]}...
        
        Generate 3-5 frequently asked questions with answers.
        Each answer should be 50-100 words, conversational, and direct.
        
        Format as JSON:
        {{
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [
                {{
                    "@type": "Question",
                    "name": "question text",
                    "acceptedAnswer": {{
                        "@type": "Answer",
                        "text": "answer text"
                    }}
                }}
            ]
        }}
        """
        
        try:
            response = await self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert at creating structured data for SEO."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            # Parse JSON from response
            response_text = response.choices[0].message.content
            
            # Extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                try:
                    faq_schema = json.loads(json_match.group())
                    return faq_schema
                except json.JSONDecodeError:
                    logger.error("Failed to parse FAQ schema JSON")
                    return self._create_default_faq_schema(target_queries)
            else:
                return self._create_default_faq_schema(target_queries)
                
        except Exception as e:
            logger.error(f"FAQ schema generation failed: {str(e)}")
            return self._create_default_faq_schema(target_queries)
    
    def _create_default_faq_schema(self, queries: List[str]) -> Dict[str, Any]:
        """Create default FAQ schema structure"""
        
        return {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": query,
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": f"Answer for: {query}"
                    }
                }
                for query in queries[:3]
            ]
        }
    
    async def _generate_nlp_variations(self, queries: List[str]) -> List[str]:
        """Generate natural language variations of queries"""
        
        variations = []
        
        for query in queries:
            prompt = f"""
            Generate 5 natural language variations of this voice search query: "{query}"
            
            Include:
            - Conversational phrasing
            - Different word orders
            - Colloquial expressions
            - Question formats
            - Command formats (e.g., "Show me...", "Find...")
            
            Format: One variation per line, no numbering.
            """
            
            try:
                response = await self.openai_client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are an expert in natural language processing and voice search."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=200,
                    temperature=0.8
                )
                
                response_text = response.choices[0].message.content
                query_variations = [
                    line.strip() 
                    for line in response_text.split('\n') 
                    if line.strip()
                ]
                
                variations.extend(query_variations)
                
            except Exception as e:
                logger.error(f"Failed to generate variations for '{query}': {str(e)}")
                # Add basic variations
                variations.extend([
                    f"What is {query}",
                    f"How do I {query}",
                    f"Tell me about {query}"
                ])
        
        return variations
    
    async def _optimize_content_structure(
        self,
        content: str,
        voice_snippets: List[Dict[str, str]],
        target_queries: List[str]
    ) -> str:
        """Optimize content structure for voice search"""
        
        prompt = f"""
        Optimize this content for voice search:
        
        Original content: {content}
        
        Target voice queries: {', '.join(target_queries)}
        
        Requirements:
        1. Add conversational headings as questions
        2. Include direct answers after question headings (40-50 words)
        3. Use natural, conversational language throughout
        4. Add transition phrases between sections
        5. Include a summary section at the end
        6. Maintain all important information from original
        
        Voice snippets to incorporate:
        {json.dumps(voice_snippets, indent=2)}
        
        Format: Return the optimized content with markdown formatting.
        """
        
        try:
            response = await self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert content optimizer specializing in voice search optimization."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Content structure optimization failed: {str(e)}")
            # Return original content with basic optimizations
            optimized = f"# {target_queries[0] if target_queries else 'Content'}\n\n"
            optimized += content
            return optimized
    
    def _calculate_voice_optimization_score(
        self,
        content: str,
        voice_snippets: List[Dict[str, str]],
        faq_schema: Dict[str, Any]
    ) -> float:
        """Calculate voice search optimization score"""
        
        score = 0.0
        
        # Content factors (40%)
        content_lower = content.lower()
        
        # Conversational tone
        conversational_words = ['you', 'your', 'we', 'our', 'how', 'what', 'when', 'where', 'why']
        conversational_count = sum(
            content_lower.count(word) 
            for word in conversational_words
        )
        if conversational_count > 20:
            score += 20
        elif conversational_count > 10:
            score += 15
        elif conversational_count > 5:
            score += 10
        
        # Question-answer format
        question_count = content.count('?')
        if question_count > 5:
            score += 20
        elif question_count > 2:
            score += 15
        elif question_count > 0:
            score += 10
        
        # Voice snippets (30%)
        if len(voice_snippets) >= 3:
            score += 30
        elif len(voice_snippets) >= 2:
            score += 20
        elif len(voice_snippets) >= 1:
            score += 10
        
        # FAQ Schema (20%)
        if faq_schema and "mainEntity" in faq_schema:
            faq_count = len(faq_schema["mainEntity"])
            if faq_count >= 5:
                score += 20
            elif faq_count >= 3:
                score += 15
            elif faq_count >= 1:
                score += 10
        
        # Natural language (10%)
        avg_sentence_length = len(content.split()) / max(content.count('.'), 1)
        if 15 <= avg_sentence_length <= 25:
            score += 10
        elif 10 <= avg_sentence_length <= 30:
            score += 5
        
        return min(score, 100)
    
    async def _generate_recommendations(
        self,
        analysis: Dict[str, Any],
        score: float
    ) -> List[str]:
        """Generate voice search optimization recommendations"""
        
        recommendations = []
        
        if score < 50:
            recommendations.append("Major improvements needed for voice search optimization")
        
        if analysis["conversational_tone"] < 10:
            recommendations.append("Increase conversational tone by using 'you', 'your', and natural language")
        
        if analysis["question_answers"] < 3:
            recommendations.append("Add more question-and-answer sections to match voice search queries")
        
        if analysis["natural_language"] < 60:
            recommendations.append("Simplify sentence structure for better voice assistant comprehension")
        
        if analysis["featured_snippet_potential"] < 50:
            recommendations.append("Structure content with clear, concise answers for featured snippets")
        
        if not recommendations:
            recommendations.append("Content is well-optimized for voice search!")
        
        return recommendations
    
    async def analyze_voice_search_trends(
        self,
        industry: str,
        location: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze voice search trends for an industry"""
        
        # This would integrate with real trend data
        # For now, return mock trends
        
        return {
            "industry": industry,
            "location": location,
            "top_voice_queries": [
                f"What is the best {industry} near me",
                f"How much does {industry} cost",
                f"Open {industry} now",
                f"{industry} reviews",
                f"How to choose {industry}"
            ],
            "query_types": {
                "navigational": 25,
                "informational": 45,
                "transactional": 20,
                "local": 10
            },
            "device_breakdown": {
                "smart_speakers": 40,
                "mobile": 45,
                "car": 15
            },
            "optimization_tips": [
                "Focus on conversational long-tail keywords",
                "Optimize for 'near me' searches",
                "Create FAQ content",
                "Use natural language in content",
                "Implement structured data"
            ]
        }