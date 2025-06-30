"""
LLM Chat Service
Handles AI chat interactions for SEO insights and recommendations
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import openai
from anthropic import AsyncAnthropic
from core.config import settings
from core.redis_client import redis_client

logger = logging.getLogger(__name__)

class LLMChatService:
    """AI-powered chat service for SEO assistance"""
    
    def __init__(self):
        self.openai_client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.anthropic_client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.default_model = "gpt-4"
        self.cache_ttl = 3600  # 1 hour cache
    
    async def chat(
        self, 
        message: str, 
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        model: str = None
    ) -> Dict[str, Any]:
        """Process chat message and generate AI response"""
        
        try:
            # Get conversation history from cache
            conversation_history = []
            if session_id:
                cached_history = await redis_client.get(f"chat_session:{session_id}")
                if cached_history:
                    conversation_history = json.loads(cached_history)
            
            # Build context for the assistant
            system_prompt = self._build_system_prompt(context)
            messages = self._build_conversation_messages(
                system_prompt, 
                conversation_history, 
                message
            )
            
            # Generate response
            response = await self._generate_response(messages, model or self.default_model)
            
            # Extract actionable insights
            insights = await self._extract_insights(message, response)
            
            # Generate follow-up suggestions
            suggestions = await self._generate_suggestions(message, response, context)
            
            # Get relevant data based on the conversation
            relevant_data = await self._fetch_relevant_data(message, response, context)
            
            # Update conversation history
            if session_id:
                conversation_history.append({"role": "user", "content": message})
                conversation_history.append({"role": "assistant", "content": response})
                await redis_client.setex(
                    f"chat_session:{session_id}",
                    self.cache_ttl,
                    json.dumps(conversation_history[-20:])  # Keep last 20 messages
                )
            
            return {
                "response": response,
                "insights": insights,
                "suggestions": suggestions,
                "relevant_data": relevant_data,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Chat processing failed: {str(e)}")
            return {
                "response": "I apologize, but I'm having trouble processing your request. Please try again.",
                "error": str(e),
                "suggestions": ["Can you rephrase your question?", "Try asking about a specific SEO topic"],
                "relevant_data": {}
            }
    
    def _build_system_prompt(self, context: Optional[Dict[str, Any]] = None) -> str:
        """Build system prompt based on context"""
        
        base_prompt = """You are an expert SEO consultant and digital marketing strategist with 15+ years of experience. 
        You provide data-driven insights and actionable recommendations for:
        
        - Keyword research and analysis
        - Content optimization strategies
        - Technical SEO improvements
        - Competitor analysis
        - Link building strategies
        - Local SEO optimization
        - E-commerce SEO
        - SERP feature optimization
        - Core Web Vitals and page speed
        - International SEO
        
        Always provide specific, actionable advice with clear next steps.
        Reference current best practices and recent algorithm updates.
        When possible, include metrics and KPIs to track success.
        Be professional but conversational."""
        
        if context:
            # Add project-specific context
            if "project_name" in context:
                base_prompt += f"\n\nYou're helping with the project: {context['project_name']}"
            
            if "domain" in context:
                base_prompt += f"\nWebsite: {context['domain']}"
            
            if "industry" in context:
                base_prompt += f"\nIndustry: {context['industry']}"
            
            if "goals" in context:
                base_prompt += f"\nMain goals: {', '.join(context['goals'])}"
        
        return base_prompt
    
    def _build_conversation_messages(
        self, 
        system_prompt: str, 
        history: List[Dict[str, str]], 
        current_message: str
    ) -> List[Dict[str, str]]:
        """Build conversation messages for the AI model"""
        
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add relevant conversation history
        for msg in history[-10:]:  # Last 10 messages for context
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        # Add current message
        messages.append({"role": "user", "content": current_message})
        
        return messages
    
    async def _generate_response(self, messages: List[Dict[str, str]], model: str) -> str:
        """Generate AI response using specified model"""
        
        try:
            if model.startswith("claude"):
                # Use Anthropic Claude
                response = await self.anthropic_client.messages.create(
                    model=model,
                    messages=messages[1:],  # Skip system message
                    system=messages[0]["content"],  # System message separately
                    max_tokens=1500
                )
                return response.content[0].text
            else:
                # Use OpenAI
                response = await self.openai_client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=1500,
                    temperature=0.7
                )
                return response.choices[0].message.content
                
        except Exception as e:
            logger.error(f"Model generation failed: {str(e)}")
            raise
    
    async def _extract_insights(self, message: str, response: str) -> List[Dict[str, str]]:
        """Extract actionable insights from the response"""
        
        insights = []
        
        # Simple pattern matching for now
        # In production, this could use NLP or another AI call
        
        patterns = {
            "recommendation": ["recommend", "suggest", "should", "consider"],
            "warning": ["avoid", "don't", "careful", "warning", "caution"],
            "opportunity": ["opportunity", "potential", "could", "leverage"],
            "metric": ["increase", "decrease", "improve", "%", "score"]
        }
        
        response_lower = response.lower()
        
        for insight_type, keywords in patterns.items():
            for keyword in keywords:
                if keyword in response_lower:
                    # Extract sentence containing the keyword
                    sentences = response.split('.')
                    for sentence in sentences:
                        if keyword in sentence.lower():
                            insights.append({
                                "type": insight_type,
                                "text": sentence.strip(),
                                "keyword": keyword
                            })
                            break
                    break
        
        return insights[:5]  # Return top 5 insights
    
    async def _generate_suggestions(
        self, 
        message: str, 
        response: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """Generate follow-up suggestions based on the conversation"""
        
        suggestions = []
        message_lower = message.lower()
        
        # Topic-based suggestions
        topic_suggestions = {
            "keyword": [
                "How do I find long-tail keywords?",
                "What's the ideal keyword difficulty to target?",
                "Show me keyword gap analysis"
            ],
            "content": [
                "How can I optimize content for featured snippets?",
                "What's the ideal content length for my topic?",
                "How do I create topic clusters?"
            ],
            "technical": [
                "How can I improve Core Web Vitals?",
                "What schema markup should I implement?",
                "How do I fix crawl errors?"
            ],
            "backlink": [
                "What's a good link building strategy?",
                "How do I analyze competitor backlinks?",
                "What makes a high-quality backlink?"
            ],
            "local": [
                "How do I optimize Google My Business?",
                "What are the local ranking factors?",
                "How can I get more local reviews?"
            ],
            "competitor": [
                "How do I conduct competitor analysis?",
                "What tools can track competitor rankings?",
                "How do I find competitor keywords?"
            ]
        }
        
        # Find relevant topics in the message
        for topic, topic_suggestions_list in topic_suggestions.items():
            if topic in message_lower:
                suggestions.extend(topic_suggestions_list)
                break
        
        # Context-based suggestions
        if context:
            if "current_rankings" in context and context["current_rankings"]:
                suggestions.append("How can I improve my current rankings?")
            
            if "competitors" in context and context["competitors"]:
                suggestions.append("What are my competitors doing differently?")
        
        # Default suggestions if none found
        if not suggestions:
            suggestions = [
                "What are the most important SEO factors?",
                "How do I create an SEO strategy?",
                "What SEO metrics should I track?"
            ]
        
        return suggestions[:3]
    
    async def _fetch_relevant_data(
        self, 
        message: str, 
        response: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Fetch relevant data based on the conversation"""
        
        relevant_data = {}
        message_lower = message.lower()
        
        # Mock data for demonstration
        # In production, this would fetch real data from the database
        
        if "ranking" in message_lower or "position" in message_lower:
            relevant_data["current_rankings"] = {
                "average_position": 15.2,
                "top_10_keywords": 25,
                "total_keywords": 150,
                "trend": "improving"
            }
        
        if "traffic" in message_lower:
            relevant_data["traffic_stats"] = {
                "organic_traffic": 45000,
                "growth_rate": 12.5,
                "top_pages": [
                    {"url": "/blog/seo-guide", "traffic": 5000},
                    {"url": "/products", "traffic": 3500}
                ]
            }
        
        if "competitor" in message_lower:
            relevant_data["competitor_insights"] = {
                "main_competitors": ["competitor1.com", "competitor2.com"],
                "keyword_overlap": 35,
                "content_gap": 120
            }
        
        if "backlink" in message_lower or "link" in message_lower:
            relevant_data["backlink_profile"] = {
                "total_backlinks": 1250,
                "referring_domains": 85,
                "domain_authority": 42,
                "toxic_score": 5
            }
        
        return relevant_data
    
    async def get_templates(self) -> List[Dict[str, Any]]:
        """Get available chat templates/prompts"""
        
        return [
            {
                "name": "SEO Audit Request",
                "prompt": "Please perform a comprehensive SEO audit for my website",
                "category": "audit"
            },
            {
                "name": "Keyword Research",
                "prompt": "I need help finding keywords for [topic]",
                "category": "keywords"
            },
            {
                "name": "Content Strategy",
                "prompt": "Help me create a content strategy for [industry]",
                "category": "content"
            },
            {
                "name": "Technical SEO Issues",
                "prompt": "I'm experiencing technical SEO issues with [problem]",
                "category": "technical"
            },
            {
                "name": "Competitor Analysis",
                "prompt": "Analyze my competitors and suggest improvements",
                "category": "competitor"
            },
            {
                "name": "Local SEO Setup",
                "prompt": "Help me optimize for local search in [location]",
                "category": "local"
            }
        ]
    
    async def export_conversation(self, session_id: str) -> Dict[str, Any]:
        """Export conversation history"""
        
        try:
            cached_history = await redis_client.get(f"chat_session:{session_id}")
            if cached_history:
                history = json.loads(cached_history)
                return {
                    "session_id": session_id,
                    "messages": history,
                    "exported_at": datetime.utcnow().isoformat()
                }
            else:
                return {
                    "session_id": session_id,
                    "messages": [],
                    "error": "Session not found"
                }
        except Exception as e:
            logger.error(f"Export conversation failed: {str(e)}")
            return {"error": str(e)}