import asyncio
import hashlib
import json
import time
from typing import AsyncGenerator, Optional, Dict, Any
import redis.asyncio as aioredis
from openai import AsyncOpenAI, RateLimitError, APITimeoutError
import logging

from .config import settings
from .models import BackendType, StreamResponse, StreamResponseType
from .prompts import ANALYSIS_PROMPT_TEMPLATE

logger = logging.getLogger(__name__)


class CodeForgeAnalyzer:
    def __init__(self):
        self.redis_client: Optional[aioredis.Redis] = None
        self.openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
        
    async def initialize_redis(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = aioredis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                password=settings.redis_password,
                db=settings.redis_db,
                decode_responses=True
            )
            # Test connection
            await self.redis_client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None
    
    def _generate_cache_key(self, problem_description: str) -> str:
        """Generate cache key from problem description"""
        content_hash = hashlib.sha256(problem_description.encode()).hexdigest()
        return f"analysis:{content_hash[:16]}"
    
    async def check_cache(self, problem_description: str) -> Optional[Dict[str, Any]]:
        """Check Redis cache for existing analysis"""
        if not self.redis_client:
            return None
            
        try:
            cache_key = self._generate_cache_key(problem_description)
            cached_data = await self.redis_client.get(cache_key)
            if cached_data:
                logger.info(f"Cache hit for key: {cache_key}")
                return json.loads(cached_data)
        except Exception as e:
            logger.error(f"Cache check error: {e}")
        
        return None
    
    async def cache_result(self, problem_description: str, analysis: str, 
                          tokens_used: Optional[int] = None) -> None:
        """Store analysis result in Redis cache"""
        if not self.redis_client:
            return
            
        try:
            cache_key = self._generate_cache_key(problem_description)
            cache_data = {
                "analysis": analysis,
                "tokens_used": tokens_used,
                "timestamp": time.time()
            }
            
            await self.redis_client.setex(
                cache_key,
                settings.cache_ttl,
                json.dumps(cache_data)
            )
            logger.info(f"Analysis cached with key: {cache_key}")
        except Exception as e:
            logger.error(f"Cache store error: {e}")
    
    async def _stream_openai_analysis(self, prompt: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream analysis from OpenAI with retry logic"""
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                yield {
                    "type": StreamResponseType.status,
                    "message": f"Connecting to OpenAI (attempt {attempt + 1})...",
                    "progress": 10 + (attempt * 5)
                }
                
                stream = await self.openai_client.chat.completions.create(
                    model=settings.openai_model,
                    messages=[
                        {"role": "system", "content": "You are an expert technical analyst providing comprehensive problem analysis and innovative solutions."},
                        {"role": "user", "content": prompt}
                    ],
                    stream=True,
                    temperature=0.7,
                    max_tokens=4000
                )
                
                yield {
                    "type": StreamResponseType.status,
                    "message": "Generating analysis...",
                    "progress": 20
                }
                
                content_buffer = ""
                chunk_count = 0
                
                async for chunk in stream:
                    if chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        content_buffer += content
                        chunk_count += 1
                        
                        yield {
                            "type": StreamResponseType.delta,
                            "content": content
                        }
                        
                        # Update progress periodically
                        if chunk_count % 10 == 0:
                            progress = min(20 + (chunk_count // 10) * 5, 90)
                            yield {
                                "type": StreamResponseType.status,
                                "progress": progress
                            }
                
                yield {
                    "type": StreamResponseType.complete,
                    "progress": 100
                }
                
                return content_buffer
                
            except RateLimitError as e:
                logger.warning(f"Rate limit hit on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    yield {
                        "type": StreamResponseType.error,
                        "message": f"Rate limit reached. Retrying in {retry_delay} seconds...",
                        "error_code": "RATE_LIMIT"
                    }
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    yield {
                        "type": StreamResponseType.error,
                        "message": "Rate limit exceeded. Please try again later.",
                        "error_code": "RATE_LIMIT_EXCEEDED"
                    }
                    raise
                    
            except APITimeoutError as e:
                logger.warning(f"API timeout on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    yield {
                        "type": StreamResponseType.error,
                        "message": f"Request timeout. Retrying in {retry_delay} seconds...",
                        "error_code": "TIMEOUT"
                    }
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    yield {
                        "type": StreamResponseType.error,
                        "message": "Request timed out after multiple attempts.",
                        "error_code": "TIMEOUT_EXCEEDED"
                    }
                    raise
                    
            except Exception as e:
                logger.error(f"OpenAI API error on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    yield {
                        "type": StreamResponseType.error,
                        "message": f"API error. Retrying in {retry_delay} seconds...",
                        "error_code": "API_ERROR"
                    }
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    yield {
                        "type": StreamResponseType.error,
                        "message": f"API error: {str(e)}",
                        "error_code": "API_ERROR_FINAL"
                    }
                    raise
    
    async def _stream_ollama_analysis(self, prompt: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream analysis from Ollama (placeholder implementation)"""
        # TODO: Implement Ollama integration
        yield {
            "type": StreamResponseType.error,
            "message": "Ollama backend not yet implemented",
            "error_code": "NOT_IMPLEMENTED"
        }
    
    async def stream_analysis(self, problem_title: str, problem_description: str, 
                            backend: BackendType = BackendType.openai) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream analysis with progress updates"""
        try:
            # Format the prompt
            prompt = ANALYSIS_PROMPT_TEMPLATE.format(
                problem_title=problem_title,
                problem_description=problem_description
            )
            
            yield {
                "type": StreamResponseType.status,
                "message": "Initializing analysis...",
                "progress": 0
            }
            
            # Check cache first
            cached_result = await self.check_cache(problem_description)
            if cached_result:
                yield {
                    "type": StreamResponseType.status,
                    "message": "Found cached analysis",
                    "progress": 50
                }
                
                yield {
                    "type": StreamResponseType.delta,
                    "content": cached_result["analysis"]
                }
                
                yield {
                    "type": StreamResponseType.complete,
                    "progress": 100
                }
                return
            
            # Stream from selected backend
            if backend == BackendType.openai:
                content_buffer = ""
                async for chunk in self._stream_openai_analysis(prompt):
                    if chunk.get("type") == StreamResponseType.delta:
                        content_buffer += chunk.get("content", "")
                    yield chunk
                
                # Cache the complete result
                if content_buffer:
                    await self.cache_result(problem_description, content_buffer)
                    
            elif backend == BackendType.ollama:
                async for chunk in self._stream_ollama_analysis(prompt):
                    yield chunk
            else:
                yield {
                    "type": StreamResponseType.error,
                    "message": f"Unsupported backend: {backend}",
                    "error_code": "UNSUPPORTED_BACKEND"
                }
                
        except Exception as e:
            logger.error(f"Analysis streaming error: {e}")
            yield {
                "type": StreamResponseType.error,
                "message": f"Analysis failed: {str(e)}",
                "error_code": "ANALYSIS_FAILED"
            }
    
    async def analyze_blocking(self, problem_title: str, problem_description: str, 
                             backend: BackendType = BackendType.openai) -> Dict[str, Any]:
        """Perform analysis in blocking mode (for REST API)"""
        start_time = time.time()
        content_buffer = ""
        tokens_used = None
        cached = False
        
        # Check cache first
        cached_result = await self.check_cache(problem_description)
        if cached_result:
            return {
                "analysis": cached_result["analysis"],
                "tokens_used": cached_result.get("tokens_used"),
                "processing_time": time.time() - start_time,
                "cached": True
            }
        
        # Stream and collect all content
        async for chunk in self.stream_analysis(problem_title, problem_description, backend):
            if chunk.get("type") == StreamResponseType.delta:
                content_buffer += chunk.get("content", "")
            elif chunk.get("type") == StreamResponseType.error:
                raise Exception(chunk.get("message", "Analysis failed"))
        
        processing_time = time.time() - start_time
        
        return {
            "analysis": content_buffer,
            "tokens_used": tokens_used,
            "processing_time": processing_time,
            "cached": cached
        }