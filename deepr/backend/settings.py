from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from pydantic import BaseModel
from database import get_db
from models import User, UserSettings
from auth import get_current_user
from encryption import encrypt_key, decrypt_key

router = APIRouter()

class SettingsUpdate(BaseModel):
    openrouter_api_key: str

class SettingsResponse(BaseModel):
    has_api_key: bool

@router.get("/settings", response_model=SettingsResponse)
async def get_settings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(UserSettings).where(UserSettings.user_id == current_user.id))
    settings = result.scalars().first()
    if not settings:
        # Create if missing
        settings = UserSettings(user_id=current_user.id)
        db.add(settings)
        await db.commit()
    
    return {"has_api_key": settings.encrypted_api_key is not None}

@router.put("/settings")
async def update_settings(
    settings_update: SettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    encrypted = encrypt_key(settings_update.openrouter_api_key, current_user.id)
    
    stmt = update(UserSettings).where(UserSettings.user_id == current_user.id).values(encrypted_api_key=encrypted)
    await db.execute(stmt)
    await db.commit()
    
    # Force reload of models on next request
    clear_model_cache(current_user.id)
    
    return {"status": "ok"}
