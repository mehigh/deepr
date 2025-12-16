from fastapi import APIRouter, Depends, HTTPException, Body
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import json
import asyncio
from pydantic import BaseModel

from database import get_db
from models import User, UserSettings, Conversation, NodeType, Node
from auth import get_current_user
from encryption import decrypt_key
from openrouter_service import OpenRouterClient
from council_engine import CouncilEngine
from sqlalchemy import desc

router = APIRouter()

class CouncilRequest(BaseModel):
    prompt: str
    council_members: List[str]
    chairman_model: str

@router.post("/council/start")
async def start_council_session(
    request: CouncilRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Retrieve API Key
    if not current_user.settings or not current_user.settings.encrypted_api_key:
        raise HTTPException(status_code=400, detail="OpenRouter API Key not configured in Settings")
    
    api_key = decrypt_key(current_user.settings.encrypted_api_key, current_user.id)
    
    # Create Conversation
    conversation = Conversation(
        user_id=current_user.id,
        title=request.prompt[:50]
    )
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)
    
    # Create Root Node
    root_node = Node(
        conversation_id=conversation.id,
        type=NodeType.ROOT.value,
        content=request.prompt,
        model_name="user"
    )
    db.add(root_node)
    await db.commit()
    
    return {"conversation_id": conversation.id}

class CouncilRunRequest(BaseModel):
    prompt: str
    council_members: List[str]
    chairman_model: str
    method: str = "dag" # dag or ensemble

@router.post("/council/run")
async def run_council(
    request: CouncilRunRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Verify API Key
    result = await db.execute(select(UserSettings).where(UserSettings.user_id == current_user.id))
    settings = result.scalars().first()
    if not settings or not settings.encrypted_api_key:
        raise HTTPException(status_code=400, detail="No API Key")
    
    api_key = decrypt_key(settings.encrypted_api_key, current_user.id)
    
    # Create Conversation & Root Node immediately
    conversation = Conversation(
        user_id=current_user.id,
        title=request.prompt[:50],
        method=request.method
    )
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)
    
    root_node = Node(conversation_id=conversation.id, type=NodeType.ROOT.value, content=request.prompt, model_name="user")
    db.add(root_node)
    await db.commit()
    await db.refresh(root_node) # Refresh to get ID

    async def event_stream():
        # Setup context
        # We need a new session for the async generator because the dependency one might close?
        # Actually, FastAPI handles dependency lifetime. But running long process...
        # Let's use the passed `db` but we must ensure we commit often.
        
        try:
            client = OpenRouterClient(api_key)
            engine = CouncilEngine(db, current_user, client)
            
            yield f"data: {json.dumps({'type': 'start', 'conversation_id': conversation.id})}\n\n"
            
            if request.method == "ensemble":
                 # 1. Parallel Research (from all models in parallel)
                yield f"data: {json.dumps({'type': 'status', 'message': 'All models are researching in parallel...'})}\n\n"
                # For ensemble, we treat root as the plan/prompt directly
                research_nodes = await engine.run_ensemble_research(conversation.id, root_node, request.council_members)
                for node in research_nodes:
                     yield f"data: {json.dumps({'type': 'node', 'node': {'id': node.id, 'type': 'research', 'content': node.content, 'model': node.model_name}})}\n\n"

                # 2. Synthesis (Anonymized)
                yield f"data: {json.dumps({'type': 'status', 'message': 'Synthesizing anonymized responses...'})}\n\n"
                synthesis_node = await engine.run_ensemble_synthesis(conversation.id, root_node, research_nodes, request.chairman_model)
                yield f"data: {json.dumps({'type': 'node', 'node': {'id': synthesis_node.id, 'type': 'synthesis', 'content': synthesis_node.content, 'model': synthesis_node.model_name}})}\n\n"

            else:
                # Default DAG flow
                # 1. Coordinator
                yield f"data: {json.dumps({'type': 'status', 'message': 'Coordinator is creating a plan...'})}\n\n"
                plan_node = await engine.run_coordinator(conversation.id, root_node, request.chairman_model)
                yield f"data: {json.dumps({'type': 'node', 'node': {'id': plan_node.id, 'type': 'plan', 'content': plan_node.content}})}\n\n"

                # 2. Researchers
                yield f"data: {json.dumps({'type': 'status', 'message': 'Council members are researching...'})}\n\n"
                research_nodes = await engine.run_researchers(conversation.id, plan_node, request.council_members)
                for node in research_nodes:
                    yield f"data: {json.dumps({'type': 'node', 'node': {'id': node.id, 'type': 'research', 'content': node.content, 'model': node.model_name}})}\n\n"

                # 3. Critics
                yield f"data: {json.dumps({'type': 'status', 'message': 'Critics are reviewing findings...'})}\n\n"
                critique_nodes = await engine.run_critics(conversation.id, research_nodes, request.council_members)
                for node in critique_nodes:
                    yield f"data: {json.dumps({'type': 'node', 'node': {'id': node.id, 'type': 'critique', 'content': node.content, 'model': node.model_name}})}\n\n"

                # 4. Synthesis
                yield f"data: {json.dumps({'type': 'status', 'message': 'Chairman is synthesizing the final answer...'})}\n\n"
                synthesis_node = await engine.run_synthesis(conversation.id, plan_node, research_nodes, critique_nodes, request.chairman_model)
                yield f"data: {json.dumps({'type': 'node', 'node': {'id': synthesis_node.id, 'type': 'synthesis', 'content': synthesis_node.content, 'model': synthesis_node.model_name}})}\n\n"
            
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        except Exception as e:
            # Send error to frontend before closing stream
            import traceback
            import logging
            error_msg = str(e)
            error_trace = traceback.format_exc()
            logging.error(f"Error in council stream: {error_trace}")
            yield f"data: {json.dumps({'type': 'error', 'message': error_msg})}\n\n"
            # Don't re-raise - let the stream close gracefully

    return StreamingResponse(event_stream(), media_type="text/event-stream")

@router.get("/history")
async def get_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == current_user.id)
        .order_by(desc(Conversation.created_at))
    )
    conversations = result.scalars().all()
    return conversations

@router.get("/history/{conversation_id}")
async def get_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Verify ownership
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id
        )
    )
    conversation = result.scalars().first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
        
    # Fetch nodes
    result = await db.execute(
        select(Node).where(Node.conversation_id == conversation_id)
    )
    nodes = result.scalars().all()
    return {"conversation": conversation, "nodes": nodes}
