from typing import Optional, Dict, Any
import asyncio
from abc import ABC, abstractmethod
import openai
import anthropic
from loguru import logger

from app.core.config import settings
from app.services.prompt_service import ResponseParser


class AIProvider(ABC):
    """Abstract base class for AI providers."""
    
    @abstractmethod
    async def analyze_problem(self, prompt: str, model: Optional[str] = None) -> Dict[str, Any]:
        """Analyze a problem using the AI provider."""
        pass


class OpenAIProvider(AIProvider):
    """OpenAI provider for problem analysis."""
    
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not configured")
        
        self.client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    
    async def analyze_problem(self, prompt: str, model: Optional[str] = None) -> Dict[str, Any]:
        """Analyze problem using OpenAI API."""
        
        if not model:
            model = "gpt-4"
        
        try:
            start_time = asyncio.get_event_loop().time()
            
            response = await self.client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a senior software engineer and computer science expert. "
                                 "Provide comprehensive, technical, and practical analysis of problems. "
                                 "Focus on real-world implementable solutions with clear trade-offs."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                max_tokens=4000,
                temperature=0.7,
            )
            
            end_time = asyncio.get_event_loop().time()
            processing_time = int(end_time - start_time)
            
            response_text = response.choices[0].message.content
            
            # Parse the response into structured format
            structured_result = ResponseParser.parse_analysis_response(response_text)
            
            return {
                "success": True,
                "provider": "openai",
                "model": model,
                "response": response_text,
                "structured_analysis": structured_result,
                "tokens_used": response.usage.total_tokens if response.usage else None,
                "processing_time_seconds": processing_time,
                "error": None
            }
            
        except Exception as e:
            logger.error(f"OpenAI analysis failed: {str(e)}")
            return {
                "success": False,
                "provider": "openai",
                "model": model,
                "response": None,
                "structured_analysis": None,
                "tokens_used": None,
                "processing_time_seconds": None,
                "error": str(e)
            }


class AnthropicProvider(AIProvider):
    """Anthropic (Claude) provider for problem analysis."""
    
    def __init__(self):
        if not settings.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY not configured")
        
        self.client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    
    async def analyze_problem(self, prompt: str, model: Optional[str] = None) -> Dict[str, Any]:
        """Analyze problem using Anthropic API."""
        
        if not model:
            model = "claude-3-sonnet-20240229"
        
        try:
            start_time = asyncio.get_event_loop().time()
            
            message = await self.client.messages.create(
                model=model,
                max_tokens=4000,
                temperature=0.7,
                system="You are a senior software engineer and computer science expert. "
                       "Provide comprehensive, technical, and practical analysis of problems. "
                       "Focus on real-world implementable solutions with clear trade-offs.",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            end_time = asyncio.get_event_loop().time()
            processing_time = int(end_time - start_time)
            
            response_text = message.content[0].text
            
            # Parse the response into structured format
            structured_result = ResponseParser.parse_analysis_response(response_text)
            
            return {
                "success": True,
                "provider": "anthropic",
                "model": model,
                "response": response_text,
                "structured_analysis": structured_result,
                "tokens_used": message.usage.input_tokens + message.usage.output_tokens if message.usage else None,
                "processing_time_seconds": processing_time,
                "error": None
            }
            
        except Exception as e:
            logger.error(f"Anthropic analysis failed: {str(e)}")
            return {
                "success": False,
                "provider": "anthropic",
                "model": model,
                "response": None,
                "structured_analysis": None,
                "tokens_used": None,
                "processing_time_seconds": None,
                "error": str(e)
            }


class AIService:
    """Main service for AI-powered problem analysis."""
    
    def __init__(self):
        self.providers = {}
        
        # Initialize available providers
        try:
            self.providers["openai"] = OpenAIProvider()
        except ValueError:
            logger.warning("OpenAI provider not available - API key not configured")
        
        try:
            self.providers["anthropic"] = AnthropicProvider()
        except ValueError:
            logger.warning("Anthropic provider not available - API key not configured")
        
        if not self.providers:
            logger.error("No AI providers available! Please configure API keys.")
    
    async def analyze_problem(
        self,
        prompt: str,
        provider: str = "openai",
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze a problem using the specified AI provider.
        
        Args:
            prompt: The analysis prompt
            provider: AI provider to use ("openai" or "anthropic")
            model: Specific model to use (optional)
            
        Returns:
            Dictionary containing analysis result and metadata
        """
        
        if provider not in self.providers:
            return {
                "success": False,
                "provider": provider,
                "model": model,
                "response": None,
                "structured_analysis": None,
                "tokens_used": None,
                "processing_time_seconds": None,
                "error": f"Provider '{provider}' not available or not configured"
            }
        
        ai_provider = self.providers[provider]
        result = await ai_provider.analyze_problem(prompt, model)
        
        logger.info(f"Analysis completed using {provider} - Success: {result['success']}")
        return result
    
    def get_available_providers(self) -> list:
        """Get list of available AI providers."""
        return list(self.providers.keys())


# Global AI service instance
ai_service = AIService()