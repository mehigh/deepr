import httpx
import os
import json
from typing import List, Dict, AsyncGenerator
from openai import AsyncOpenAI

# Hardcoded curated list of models
AVAILABLE_MODELS = [
    # Curren Flagship
    {"id": "openai/gpt-5.2", "name": "GPT-5.2", "description": "OpenAI Flagship"},
    {"id": "anthropic/claude-opus-4.5", "name": "Claude 4.5 Opus", "description": "Anthropic Flagship"},
    {"id": "google/gemini-3-pro-preview", "name": "Gemini 3 Pro", "description": "Google Flagship"},
    {"id": "x-ai/grok-4", "name": "Grok 4", "description": "xAI Flagship"},
    {"id": "deepseek/deepseek-v3.2", "name": "DeepSeek v3.2", "description": "Deepseek Flagship"},
    
    # Prior Flagships
    {"id": "openai/gpt-4o", "name": "GPT-4o", "description": "Prior Flagship"},
    {"id": "anthropic/claude-3-opus", "name": "Claude 3 Opus", "description": "Prior Flagship"},
    {"id": "google/gemini-2.5-pro", "name": "Gemini 2.5 Pro", "description": "Prior Flagship"},
    
    # Fast & Efficient
    {"id": "openai/gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "description": "Fast & Efficient"},
    {"id": "anthropic/claude-3-haiku", "name": "Claude 3 Haiku", "description": "Speed Optimized"},
    {"id": "google/gemini-1.5-flash", "name": "Gemini 1.5 Flash", "description": "Google Fast"},
    {"id": "meta-llama/llama-3-70b-instruct", "name": "Llama 3 70B", "description": "Meta Flagship"},
]

class OpenRouterClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )

    async def get_available_models(self):
        # In a real scenario, we might fetch from API, but for now return curated list
        return AVAILABLE_MODELS

    async def chat_completion(self, model: str, messages: List[Dict], stream: bool = False):
        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                stream=stream
            )
            return response
        except Exception as e:
            print(f"Error calling {model}: {e}")
            raise

    async def stream_chat_completion(self, model: str, messages: List[Dict]) -> AsyncGenerator[str, None]:
        try:
            stream = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                stream=True
            )
            async for chunk in stream:
                content = chunk.choices[0].delta.content
                if content:
                    yield content
        except Exception as e:
            print(f"Error streaming {model}: {e}")
            yield f"[Error: {str(e)}]"
