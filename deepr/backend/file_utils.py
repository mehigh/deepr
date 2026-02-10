"""
File upload utilities for attachment support.
Handles file validation, temporary storage, and MIME type detection.
"""
import uuid
from typing import Dict, Optional

# File size limits (in bytes)
MAX_FILE_SIZE = {
    'image': 10 * 1024 * 1024,   # 10MB
    'pdf': 20 * 1024 * 1024,      # 20MB
    'text': 5 * 1024 * 1024,      # 5MB for text files
    'audio': 25 * 1024 * 1024,    # 25MB
    'video': 50 * 1024 * 1024     # 50MB
}

# Allowed MIME types by category
ALLOWED_MIME_TYPES = {
    'image': [
        'image/jpeg', 
        'image/png', 
        'image/gif', 
        'image/webp',
        'image/svg+xml'
    ],
    'pdf': [
        'application/pdf'
    ],
    'text': [
        # Plain text
        'text/plain',
        # Markdown
        'text/markdown',
        'text/x-markdown',
        # Code files
        'text/x-python',
        'text/x-java',
        'text/x-c',
        'text/x-c++',
        'text/javascript',
        'application/javascript',
        'application/x-javascript',
        'text/typescript',
        'application/typescript',
        # Web files
        'text/html',
        'text/css',
        'application/json',
        'application/xml',
        'text/xml',
        # Config files
        'application/yaml',
        'text/yaml',
        'application/x-yaml',
        'text/x-yaml',
        # Data files
        'text/csv',
        'application/csv',
        # Logs
        'text/x-log',
        # Generic (often text files)
        'application/octet-stream',
    ],
    'audio': [
        'audio/mpeg', 
        'audio/wav', 
        'audio/ogg'
    ],
    'video': [
        'video/mp4', 
        'video/webm'
    ]
}

# Temporary storage for uploaded files (before node creation)
# In production, use Redis or similar
temp_storage: Dict[str, dict] = {}

def get_file_type(mime_type: str) -> Optional[str]:
    """Determine file type category from MIME type"""
    for ftype, mimes in ALLOWED_MIME_TYPES.items():
        if mime_type in mimes:
            return ftype
    return None

def validate_file_size(file_size: int, file_type: str) -> bool:
    """Check if file size is within limits"""
    max_size = MAX_FILE_SIZE.get(file_type, 0)
    return file_size <= max_size
