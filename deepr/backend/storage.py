"""
Storage abstraction layer for file attachments.
Allows switching between database storage and external document management systems.
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict
from models import Attachment
from sqlalchemy.ext.asyncio import AsyncSession


class StorageBackend(ABC):
    """Abstract base class for storage backends"""
    
    @abstractmethod
    async def save_file(
        self,
        db: AsyncSession,
        node_id: int,
        filename: str,
        file_type: str,
        mime_type: str,
        file_data: bytes,
        file_size: int
    ) -> Attachment:
        """Save file and return Attachment object"""
        pass
    
    @abstractmethod
    async def get_file(self, db: AsyncSession, attachment_id: int) -> Optional[Attachment]:
        """Retrieve file by attachment ID"""
        pass
    
    @abstractmethod
    async def delete_file(self, db: AsyncSession, attachment_id: int) -> bool:
        """Delete file by attachment ID"""
        pass


class DatabaseStorage(StorageBackend):
    """Store files directly in PostgreSQL database as BYTEA"""
    
    async def save_file(
        self,
        db: AsyncSession,
        node_id: int,
        filename: str,
        file_type: str,
        mime_type: str,
        file_data: bytes,
        file_size: int
    ) -> Attachment:
        """Save file to database"""
        attachment = Attachment(
            node_id=node_id,
            filename=filename,
            file_type=file_type,
            mime_type=mime_type,
            file_data=file_data,
            file_size=file_size
        )
        db.add(attachment)
        await db.commit()
        await db.refresh(attachment)
        return attachment
    
    async def get_file(self, db: AsyncSession, attachment_id: int) -> Optional[Attachment]:
        """Retrieve file from database"""
        from sqlalchemy import select
        result = await db.execute(
            select(Attachment).where(Attachment.id == attachment_id)
        )
        return result.scalars().first()
    
    async def delete_file(self, db: AsyncSession, attachment_id: int) -> bool:
        """Delete file from database"""
        attachment = await self.get_file(db, attachment_id)
        if attachment:
            await db.delete(attachment)
            await db.commit()
            return True
        return False


class ExternalDocumentStorage(StorageBackend):
    """
    Future implementation for external document management system.
    Could use S3, MinIO, local filesystem, or dedicated DMS.
    """
    
    def __init__(self, base_path: str = None, s3_bucket: str = None):
        self.base_path = base_path
        self.s3_bucket = s3_bucket
    
    async def save_file(
        self,
        db: AsyncSession,
        node_id: int,
        filename: str,
        file_type: str,
        mime_type: str,
        file_data: bytes,
        file_size: int
    ) -> Attachment:
        """
        Save file to external storage and metadata to database.
        
        Future implementation:
        1. Upload file to S3/filesystem
        2. Get file URL/path
        3. Store metadata + URL in database (file_data = None)
        """
        raise NotImplementedError("External storage not yet implemented")
    
    async def get_file(self, db: AsyncSession, attachment_id: int) -> Optional[Attachment]:
        """
        Retrieve file from external storage.
        
        Future implementation:
        1. Get metadata from database
        2. Download file from S3/filesystem
        3. Return Attachment with file_data populated
        """
        raise NotImplementedError("External storage not yet implemented")
    
    async def delete_file(self, db: AsyncSession, attachment_id: int) -> bool:
        """
        Delete file from external storage.
        
        Future implementation:
        1. Get metadata from database
        2. Delete file from S3/filesystem
        3. Delete metadata from database
        """
        raise NotImplementedError("External storage not yet implemented")


# Global storage instance - can be configured via environment variable
# For now, use database storage
STORAGE_BACKEND = DatabaseStorage()


def get_storage() -> StorageBackend:
    """Get configured storage backend"""
    # Future: Read from environment variable
    # storage_type = os.getenv("STORAGE_BACKEND", "database")
    # if storage_type == "s3":
    #     return ExternalDocumentStorage(s3_bucket=os.getenv("S3_BUCKET"))
    # elif storage_type == "filesystem":
    #     return ExternalDocumentStorage(base_path=os.getenv("STORAGE_PATH"))
    # else:
    #     return DatabaseStorage()
    
    return STORAGE_BACKEND
