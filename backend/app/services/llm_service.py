"""
LLM Service - Manages interactions with different LLM providers
"""

from typing import Dict, Any, Optional, List
import openai
import google.generativeai as genai
import anthropic
from app.core.config import settings


class LLMService:
    """Service for managing LLM interactions"""
    
    def __init__(self):
        self._configure_providers()
    
    def _configure_providers(self):
        """Configure LLM providers"""
        # Azure OpenAI
        if settings.AZURE_OPENAI_API_KEY:
            openai.api_key = settings.AZURE_OPENAI_API_KEY
            openai.api_base = settings.AZURE_OPENAI_ENDPOINT
            openai.api_type = "azure"
            openai.api_version = settings.AZURE_OPENAI_API_VERSION
        
        # OpenAI
        elif settings.OPENAI_API_KEY:
            openai.api_key = settings.OPENAI_API_KEY
            openai.api_type = "openai"
        
        # Google Gemini
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
        
        # Anthropic Claude
        if settings.CLAUDE_API_KEY:
            self.claude_client = anthropic.Anthropic(
                api_key=settings.CLAUDE_API_KEY
            )
    
    async def get_llm(self, model_name: str):
        """Get LLM instance based on model name"""
        try:
            if model_name.startswith("gpt-"):
                from langchain_openai import AzureChatOpenAI, ChatOpenAI
                
                if settings.AZURE_OPENAI_API_KEY:
                    return AzureChatOpenAI(
                        deployment_name=model_name,
                        openai_api_version=settings.AZURE_OPENAI_API_VERSION,
                        azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
                        openai_api_key=settings.AZURE_OPENAI_API_KEY
                    )
                else:
                    return ChatOpenAI(
                        model_name=model_name,
                        openai_api_key=settings.OPENAI_API_KEY
                    )
            
            elif model_name.startswith("gemini-"):
                from langchain_google_genai import ChatGoogleGenerativeAI
                return ChatGoogleGenerativeAI(
                    model=model_name,
                    google_api_key=settings.GEMINI_API_KEY
                )
            
            elif model_name.startswith("claude-"):
                from langchain_anthropic import ChatAnthropic
                return ChatAnthropic(
                    model=model_name,
                    anthropic_api_key=settings.CLAUDE_API_KEY
                )
            
            else:
                raise ValueError(f"Unsupported model: {model_name}")
                
        except ImportError as e:
            raise ValueError(f"Required library not installed for model {model_name}: {e}")
    
    async def generate_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate completion using the specified model"""
        try:
            if model.startswith("gpt-"):
                return await self._generate_openai_completion(
                    messages, model, temperature, max_tokens, **kwargs
                )
            elif model.startswith("gemini-"):
                return await self._generate_gemini_completion(
                    messages, model, temperature, max_tokens, **kwargs
                )
            elif model.startswith("claude-"):
                return await self._generate_claude_completion(
                    messages, model, temperature, max_tokens, **kwargs
                )
            else:
                raise ValueError(f"Unsupported model: {model}")
                
        except Exception as e:
            raise Exception(f"LLM completion failed: {str(e)}")
    
    async def _generate_openai_completion(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: Optional[int],
        **kwargs
    ) -> Dict[str, Any]:
        """Generate OpenAI completion"""
        try:
            response = await openai.ChatCompletion.acreate(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            return {
                "content": response.choices[0].message.content,
                "model": model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
                "finish_reason": response.choices[0].finish_reason
            }
            
        except Exception as e:
            raise Exception(f"OpenAI completion failed: {str(e)}")
    
    async def _generate_gemini_completion(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: Optional[int],
        **kwargs
    ) -> Dict[str, Any]:
        """Generate Gemini completion"""
        try:
            # Convert messages to Gemini format
            prompt = self._convert_messages_to_text(messages)
            
            model_instance = genai.GenerativeModel(model)
            response = await model_instance.generate_content_async(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                    **kwargs
                )
            )
            
            return {
                "content": response.text,
                "model": model,
                "usage": {
                    "prompt_tokens": response.usage_metadata.prompt_token_count,
                    "completion_tokens": response.usage_metadata.candidates_token_count,
                    "total_tokens": response.usage_metadata.total_token_count,
                },
                "finish_reason": response.candidates[0].finish_reason.name if response.candidates else "stop"
            }
            
        except Exception as e:
            raise Exception(f"Gemini completion failed: {str(e)}")
    
    async def _generate_claude_completion(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: Optional[int],
        **kwargs
    ) -> Dict[str, Any]:
        """Generate Claude completion"""
        try:
            response = await self.claude_client.messages.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens or 1024,
                **kwargs
            )
            
            return {
                "content": response.content[0].text,
                "model": model,
                "usage": {
                    "prompt_tokens": response.usage.input_tokens,
                    "completion_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
                },
                "finish_reason": response.stop_reason
            }
            
        except Exception as e:
            raise Exception(f"Claude completion failed: {str(e)}")
    
    def _convert_messages_to_text(self, messages: List[Dict[str, str]]) -> str:
        """Convert messages to plain text for models that don't support message format"""
        text = ""
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            if role == "system":
                text += f"System: {content}\n"
            elif role == "user":
                text += f"User: {content}\n"
            elif role == "assistant":
                text += f"Assistant: {content}\n"
        return text.strip()
    
    async def generate_embedding(
        self,
        text: str,
        model: str = "text-embedding-ada-002"
    ) -> List[float]:
        """Generate text embedding"""
        try:
            if model.startswith("text-embedding"):
                # OpenAI embedding
                response = await openai.Embedding.acreate(
                    input=text,
                    model=model
                )
                return response['data'][0]['embedding']
            else:
                # Fallback to mock embedding for other models
                # In production, implement proper embedding generation
                import hashlib
                import numpy as np
                
                # Generate deterministic embedding from text hash
                hash_object = hashlib.md5(text.encode())
                hex_dig = hash_object.hexdigest()
                
                # Convert to numpy array and normalize
                embedding = np.array([ord(c) for c in hex_dig[:1536]])
                embedding = embedding / np.linalg.norm(embedding)
                
                return embedding.tolist()
                
        except Exception as e:
            raise Exception(f"Embedding generation failed: {str(e)}")
    
    async def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available models"""
        models = []
        
        # OpenAI models
        if settings.AZURE_OPENAI_API_KEY or settings.OPENAI_API_KEY:
            models.extend([
                {"name": "gpt-4", "provider": "openai", "type": "chat"},
                {"name": "gpt-4-turbo", "provider": "openai", "type": "chat"},
                {"name": "gpt-3.5-turbo", "provider": "openai", "type": "chat"},
                {"name": "text-embedding-ada-002", "provider": "openai", "type": "embedding"},
            ])
        
        # Gemini models
        if settings.GEMINI_API_KEY:
            models.extend([
                {"name": "gemini-pro", "provider": "google", "type": "chat"},
                {"name": "gemini-pro-vision", "provider": "google", "type": "chat"},
            ])
        
        # Claude models
        if settings.CLAUDE_API_KEY:
            models.extend([
                {"name": "claude-3-haiku", "provider": "anthropic", "type": "chat"},
                {"name": "claude-3-sonnet", "provider": "anthropic", "type": "chat"},
                {"name": "claude-3-opus", "provider": "anthropic", "type": "chat"},
            ])
        
        return models
