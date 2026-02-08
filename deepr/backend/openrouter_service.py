import httpx
import os
import json
import base64
from typing import List, Dict, AsyncGenerator, Optional, Tuple
from openai import AsyncOpenAI
from encryption import decrypt_key
from models import User
from fastapi import HTTPException

# Global cache for models
_CACHED_MODELS_LIST = []

async def fetch_models_from_api(current_user: User):
    """Fetch models from OpenRouter and populate cache"""
    global _CACHED_MODELS_LIST

    # Retrieve API Key
    if not current_user.settings or not current_user.settings.encrypted_api_key:
        raise HTTPException(status_code=400, detail="OpenRouter API Key not configured in Settings")
    
    api_key = decrypt_key(current_user.settings.encrypted_api_key, current_user.id)
        

    try:
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}            
            response = await client.get("https://openrouter.ai/api/v1/models/user", headers=headers)            
            response.raise_for_status()
            data = response.json()
            api_models = data.get('data', [])            
                        
            # Populate cache
            models_list = []

            # Sort API models by name
            api_models.sort(key=lambda x: x.get('name', ''))

            for m in api_models:
                # Parse capability
                architecture = m.get('architecture', {})
                modality = architecture.get('modality', '') 
                                
                model_entry = {
                    "id": m['id'],
                    "name": m.get('name', m['id']),
                    "description": m.get('description', ''),
                    "context_length": m.get('context_length', 0),
                    "pricing": m.get('pricing', {}),
                    "capabilities": {
                        "image": 'image' in modality or 'vision' in m['id'].lower(),
                        "file": 'file' in modality, 
                        "audio": 'audio' in modality, 
                        "video": 'video' in modality,
                        "text": 'text' in modality
                    }
                }
                models_list.append(model_entry)
            
            # Filter generic models if count < 200 (user request)
            if len(models_list) < 200:
                exclude_ids = {'openrouter/bodybuilder', 'openrouter/free', 'openrouter/auto'}
                models_list = [m for m in models_list if m['id'] not in exclude_ids]

            # Update globals
            global _CACHED_MODELS_LIST
            _CACHED_MODELS_LIST = models_list            
            
            return models_list
            
    except Exception as e:
        # Fallback if API fails
        return []

async def get_available_models(current_user: User):
    """Get list of available models, fetching if necessary"""
    if not _CACHED_MODELS_LIST:
        await fetch_models_from_api(current_user)
    return _CACHED_MODELS_LIST

def get_unsupported_attachments(model_id: str, attachments: List) -> List[str]:
    """
    Get list of warnings for unsupported attachments.    
    """
    warnings = []
    
    if not attachments:
        return warnings
    
    # Check capabilities
    model = next((m for m in _CACHED_MODELS_LIST if m['id'] == model_id), {})
    caps = model.get('capabilities', {})
    vision_supported = caps.get('image', False)
    file_supported = caps.get('file', False)
    audio_supported = caps.get('audio', False)
    video_supported = caps.get('video', False)
    text_supported = caps.get('text', False)
    
    # Count attachment types
    image_count = sum(1 for att in attachments if att.file_type == 'image')
    file_count = sum(1 for att in attachments if att.file_type == 'file')
    audio_count = sum(1 for att in attachments if att.file_type == 'audio')
    video_count = sum(1 for att in attachments if att.file_type == 'video')
    
    # Check for unsupported types
    if image_count > 0 and not vision_supported:
        warnings.append(
            f"⚠️ Model '{model_id}' doesn't support vision. "
            f"{image_count} image(s) sent anyway - may be ignored by model."
        )
    if file_count > 0 and not file_supported:
        warnings.append(
            f"⚠️ Model '{model_id}' doesn't support files. "
            f"{file_count} file(s) sent anyway - may be ignored by model."
        )
    if audio_count > 0 and not audio_supported:
        warnings.append(
            f"⚠️ Model '{model_id}' doesn't support audio. "
            f"{audio_count} audio(s) sent anyway - may be ignored by model."
        )
    if video_count > 0 and not video_supported:
        warnings.append(
            f"⚠️ Model '{model_id}' doesn't support video. "
            f"{video_count} video(s) sent anyway - may be ignored by model."
        )           
    return warnings

class OpenRouterClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = AsyncOpenAI(
            base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
            api_key=api_key,
        )

    async def get_models(self):
         # Just a wrapper if needed, but not used.
         pass

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

    async def chat_completion_details(
        self,
        model: str,
        messages: List[Dict],
        attachments: Optional[List] = None,
        stream: bool = False
    ) -> Tuple[any, Dict]:

        if attachments:
            # Process messages to include attachments
            for msg in messages:
                if msg.get('role') == 'user':
                    # Convert string content to array format
                    if isinstance(msg.get('content'), str):
                        text_content = msg['content']
                        content_array = [{"type": "text", "text": text_content}]
                        
                        # Add attachments
                        for att in attachments:
                            base64_data = base64.b64encode(att.file_data).decode('utf-8')
                            
                            if att.file_type == 'image':
                                content_array.append({
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:{att.mime_type};base64,{base64_data}"
                                    }
                                })
                            elif att.file_type == 'file' or att.file_type == 'pdf':
                                content_array.append({
                                    "type": "file",
                                    "file": {
                                        "url": f"data:{att.mime_type};base64,{base64_data}"
                                    }
                                })
                            elif att.file_type == 'audio':
                                content_array.append({
                                    "type": "audio_url",
                                    "audio_url": {
                                        "url": f"data:{att.mime_type};base64,{base64_data}"
                                    }
                                })
                            elif att.file_type == 'video':
                                content_array.append({
                                    "type": "video_url",
                                    "video_url": {
                                        "url": f"data:{att.mime_type};base64,{base64_data}"
                                    }
                                })
                            else:
                                content_array.append({
                                    "type": "text",
                                    "text": att.file_data.decode('utf-8')
                                })
                        
                        msg['content'] = content_array
        
        # Determine referer
        host = os.getenv("HOST_IP", "localhost")
        port = os.getenv("FRONTEND_PORT", "9080")
        referer = f"http://{host}:{port}"

        # Make the API call        
        response = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            stream=stream,
            extra_headers={
                "HTTP-Referer": referer,
                "X-Title": "DeepR Council"
            }
        )
        
        # Extract token counts from response
        input_tokens = 0
        output_tokens = 0
        actual_cost = 0.0 # Initialize variable
        
        if hasattr(response, 'usage') and response.usage:
            input_tokens = getattr(response.usage, 'prompt_tokens', 0)
            output_tokens = getattr(response.usage, 'completion_tokens', 0)            
            
            # Extract actual cost provided by OpenRouter
            try:
                # Convert usage to dict to access extra fields
                usage_data = response.usage.model_dump() if hasattr(response.usage, 'model_dump') else response.usage.__dict__                
                if 'cost' in usage_data:
                    actual_cost = float(usage_data['cost'])
                elif 'total_cost' in usage_data:
                    actual_cost = float(usage_data['total_cost'])
                elif 'cost_details' in usage_data:
                    cost_details = usage_data['cost_details']
                    if isinstance(cost_details, dict):
                        actual_cost = float(cost_details.get('upstream_inference_cost', 0.0)) + float(cost_details.get('upstream_image_inference_cost', 0.0))                
                if actual_cost == 0.0 and hasattr(response, 'cost'):
                     actual_cost = float(response.cost)
            except Exception as e:
                pass

        # Return response and cost info
        cost_info = {
            'actual_cost': actual_cost,
            'input_tokens': input_tokens,
            'output_tokens': output_tokens
        }
        
        return response, cost_info

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
