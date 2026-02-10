from fastapi import APIRouter, Depends, HTTPException, Body, File, UploadFile
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
import json
import asyncio
from pydantic import BaseModel

from database import get_db
from models import User, UserSettings, Conversation, NodeType, Node, Attachment
from auth import get_current_user
from encryption import decrypt_key
from openrouter_service import OpenRouterClient, get_available_models
from council_engine import CouncilEngine
from engines.dxo_engine import DxOEngine
from sqlalchemy import desc
from fastapi import File, UploadFile
from file_utils import get_file_type, validate_file_size, temp_storage
import uuid

router = APIRouter()

async def serialize_node_with_attachments(db: AsyncSession, node):
    """Helper to serialize node with attachments for streaming"""
    # Refresh node to get attachments relationship
    if db:
        try:
            await db.refresh(node, ['attachments'])
        except Exception:
            pass # In case it's a MockNode or already detached
    
    return {
        'id': node.id,
        'conversation_id': getattr(node, 'conversation_id', None),
        'parent_id': getattr(node, 'parent_id', None),
        'type': node.type,
        'content': node.content,
        'model': getattr(node, 'model_name', None),
        'attachment_filenames': getattr(node, 'attachment_filenames', None),
        'prompt_sent': getattr(node, 'prompt_sent', None),
        'actual_cost': getattr(node, 'actual_cost', 0.0),
        'warnings': json.loads(node.warnings) if hasattr(node, 'warnings') and node.warnings else [],
        'attachments': [
            {
                'id': att.id,
                'filename': att.filename,
                'file_type': att.file_type,
                'file_size': att.file_size,
                'mime_type': att.mime_type
            }
            for att in (node.attachments if hasattr(node, 'attachments') and node.attachments else [])
        ]
    }


@router.get("/models")
async def get_models(current_user: User = Depends(get_current_user)):
   return await get_available_models(current_user)   

class UpdateNodeCostRequest(BaseModel):
    actual_cost: float

@router.put("/nodes/{node_id}/cost")
async def update_node_cost(
    node_id: int,
    request: UpdateNodeCostRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update the actual_cost of a node after calculating real cost"""
    # Verify node exists and belongs to user
    result = await db.execute(
        select(Node)
        .join(Conversation, Node.conversation_id == Conversation.id)
        .where(Node.id == node_id)
        .where(Conversation.user_id == current_user.id)
    )
    node = result.scalar_one_or_none()
    
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    
    node.actual_cost = request.actual_cost
    await db.commit()
    
    return {"success": True, "node_id": node_id, "actual_cost": request.actual_cost}

@router.post("/api/upload")
async def upload_files(
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Upload files temporarily before node creation.
    Returns list of file IDs for attachment to prompt.
    """
    uploaded = []
    
    for file in files:
        # Validate MIME type
        file_type = get_file_type(file.content_type)
        if not file_type:
            raise HTTPException(400, f"Unsupported file type: {file.content_type}")
        
        # Read file data
        file_data = await file.read()
        file_size = len(file_data)
        
        # Validate size
        if not validate_file_size(file_size, file_type):
            raise HTTPException(400, f"File too large: {file.filename}")
        
        # Store temporarily (in-memory)
        file_id = str(uuid.uuid4())
        temp_storage[file_id] = {
            'filename': file.filename,
            'file_type': file_type,
            'mime_type': file.content_type,
            'file_data': file_data,
            'file_size': file_size,
            'user_id': current_user.id
        }
        
        uploaded.append({
            'id': file_id,
            'filename': file.filename,
            'size': file_size,
            'type': file_type
        })
    
    return uploaded

@router.get("/api/attachments/{attachment_id}")
async def download_attachment(
    attachment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Download attachment file.
    Verifies user owns the conversation containing this attachment.
    """
    # Get attachment with node and conversation to verify ownership
    result = await db.execute(
        select(Attachment)
        .join(Node, Attachment.node_id == Node.id)
        .join(Conversation, Node.conversation_id == Conversation.id)
        .where(Attachment.id == attachment_id)
        .where(Conversation.user_id == current_user.id)
    )
    attachment = result.scalar_one_or_none()
    
    if not attachment:
        raise HTTPException(404, "Attachment not found or access denied")
    
    # Return file as download
    return Response(
        content=attachment.file_data,
        media_type=attachment.mime_type,
        headers={
            "Content-Disposition": f'attachment; filename="{attachment.filename}"'
        }
    )

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
    council_members: List[str] = []
    chairman_model: str = "openai/gpt-4o"
    method: str = "dag" # dag, ensemble, or dxo
    roles: List[dict] = [] # List of {name, model, instructions}
    max_iterations: int = 5 # Default max loops for DxO
    attachment_ids: List[str] = [] # List of uploaded file IDs from /upload endpoint

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

    # Save attachments to database
    from storage import get_storage
    storage = get_storage()
    
    saved_filenames = []
    for attachment_id in request.attachment_ids:
        if attachment_id in temp_storage:
            file_info = temp_storage[attachment_id]
            
            # Verify user owns this upload
            if file_info['user_id'] != current_user.id:
                continue
            
            # Save to database via storage layer
            await storage.save_file(
                db=db,
                node_id=root_node.id,
                filename=file_info['filename'],
                file_type=file_info['file_type'],
                mime_type=file_info['mime_type'],
                file_data=file_info['file_data'],
                file_size=file_info['file_size']
            )
            saved_filenames.append(file_info['filename'])
            
            # Remove from temp storage
            del temp_storage[attachment_id]

    if saved_filenames:
        root_node.attachment_filenames = ",".join(saved_filenames)
        await db.commit()



    async def event_stream():
        # Setup context
        # We need a new session for the async generator because the dependency one might close?
        # Actually, FastAPI handles dependency lifetime. But running long process...
        # Let's use the passed `db` but we must ensure we commit often.
        
        try:
            client = OpenRouterClient(api_key)
            engine = CouncilEngine(db, current_user, client)
            
            yield f"data: {json.dumps({'type': 'start', 'conversation_id': conversation.id})}\n\n"
            
            # Send root node with attachments
            root_node_data = await serialize_node_with_attachments(db, root_node)
            yield f"data: {json.dumps({'type': 'node', 'node': root_node_data})}\n\n"
            
            if request.method == "ensemble":
                 # 1. Parallel Research (from all models in parallel)
                yield f"data: {json.dumps({'type': 'status', 'message': 'All models are researching in parallel...'})}\n\n"
                # For ensemble, we treat root as the plan/prompt directly
                research_nodes = await engine.run_ensemble_research(conversation.id, root_node, request.council_members)
                for node in research_nodes:
                     node_data = await serialize_node_with_attachments(db, node)
                     yield f"data: {json.dumps({'type': 'node', 'node': node_data})}\n\n"

                # 2. Synthesis (Anonymized)
                yield f"data: {json.dumps({'type': 'status', 'message': 'Synthesizing anonymized responses...'})}\n\n"
                synthesis_node = await engine.run_ensemble_synthesis(conversation.id, root_node, research_nodes, request.chairman_model)
                node_data = await serialize_node_with_attachments(db, synthesis_node)
                yield f"data: {json.dumps({'type': 'node', 'node': node_data})}\n\n"

            elif request.method == "dxo":
                dxo_engine = DxOEngine(db, current_user, client)
                yield f"data: {json.dumps({'type': 'status', 'message': 'Initializing DxO Virtual Panel...'})}\n\n"
                async for event in dxo_engine.run_dxo_pipeline(conversation.id, root_node, request.roles, max_iterations=request.max_iterations):
                    yield f"data: {event}\n\n"

            else:
                # Default DAG flow
                # 1. Coordinator
                yield f"data: {json.dumps({'type': 'status', 'message': 'Coordinator is creating a plan...'})}\n\n"
                plan_node = await engine.run_coordinator(conversation.id, root_node, request.chairman_model)
                node_data = await serialize_node_with_attachments(db, plan_node)
                yield f"data: {json.dumps({'type': 'node', 'node': node_data})}\n\n"

                # 2. Researchers
                yield f"data: {json.dumps({'type': 'status', 'message': 'Council members are researching...'})}\n\n"
                research_nodes = await engine.run_researchers(conversation.id, plan_node, request.council_members)
                for node in research_nodes:
                    node_data = await serialize_node_with_attachments(db, node)
                    yield f"data: {json.dumps({'type': 'node', 'node': node_data})}\n\n"

                # 3. Critics
                yield f"data: {json.dumps({'type': 'status', 'message': 'Critics are reviewing findings...'})}\n\n"
                critique_nodes = await engine.run_critics(conversation.id, research_nodes, request.council_members)
                for node in critique_nodes:
                    node_data = await serialize_node_with_attachments(db, node)
                    yield f"data: {json.dumps({'type': 'node', 'node': node_data})}\n\n"

                # 4. Synthesis
                yield f"data: {json.dumps({'type': 'status', 'message': 'Chairman is synthesizing the final answer...'})}\n\n"
                synthesis_node = await engine.run_synthesis(conversation.id, plan_node, research_nodes, critique_nodes, request.chairman_model)
                node_data = await serialize_node_with_attachments(db, synthesis_node)
                yield f"data: {json.dumps({'type': 'node', 'node': node_data})}\n\n"
            
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
    
    # Serialize nodes with attachments
    nodes_data = []
    for node in nodes:
        node_data = await serialize_node_with_attachments(db, node)
        nodes_data.append(node_data)
    
    return {"conversation": conversation, "nodes": nodes_data}

@router.get("/conversations/{conversation_id}/cost")
async def get_conversation_cost(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get total cost for a conversation"""
    # Verify conversation belongs to user
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id
        )
    )
    conversation = result.scalars().first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Calculate total cost
    result = await db.execute(
        select(func.sum(Node.actual_cost))
        .where(Node.conversation_id == conversation_id)
    )
    total_cost = result.scalar() or 0.0
    
    return {
        'conversation_id': conversation_id,
        'total_cost': total_cost,
        'currency': 'USD'
    }

class SuperChatRequest(BaseModel):
    prompt: str
    conversation_id: Optional[int] = None
    council_members: List[str]
    chairman_model: str
    attachment_ids: List[str] = []

@router.post("/superchat/chat")
async def superchat_chat(
    request: SuperChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Verify API Key
    result = await db.execute(select(UserSettings).where(UserSettings.user_id == current_user.id))
    settings = result.scalars().first()
    if not settings or not settings.encrypted_api_key:
        raise HTTPException(status_code=400, detail="No API Key")

    api_key = decrypt_key(settings.encrypted_api_key, current_user.id)

    # Attachments will be processed after node creation in SuperChat to match Council pattern
    attachment_ids = request.attachment_ids or []

    conversation_id = request.conversation_id
    parent_node_id = None
    last_synthesis_content = ""

    if conversation_id:
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

        # Find last synthesis node
        result = await db.execute(
            select(Node)
            .where(Node.conversation_id == conversation_id, Node.type == NodeType.SYNTHESIS.value)
            .order_by(desc(Node.id))
            .limit(1)
        )
        last_synthesis_node = result.scalars().first()
        if last_synthesis_node:
            parent_node_id = last_synthesis_node.id
            last_synthesis_content = last_synthesis_node.content
    else:
        # Create new conversation
        conversation = Conversation(
            user_id=current_user.id,
            title=request.prompt[:50],
            method="superchat"
        )
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)
        conversation_id = conversation.id

    # Create User Node (Root for this turn)
    user_node = Node(
        conversation_id=conversation_id,
        parent_id=parent_node_id,
        type=NodeType.ROOT.value, # Using ROOT as the type for user input in each turn
        content=request.prompt,
        model_name="user"
    )
    db.add(user_node)
    await db.commit()
    await db.refresh(user_node)

    # Process attachments (move from temp to permanent)
    from storage import get_storage
    storage = get_storage()
    
    saved_filenames = []
    
    for attachment_id in attachment_ids:
        if attachment_id in temp_storage:
            file_info = temp_storage[attachment_id]
            if file_info['user_id'] != current_user.id:
                continue
                
            await storage.save_file(
                db=db,
                node_id=user_node.id,
                filename=file_info['filename'],
                file_type=file_info['file_type'],
                mime_type=file_info['mime_type'],
                file_data=file_info['file_data'],
                file_size=file_info['file_size']
            )
            saved_filenames.append(file_info['filename'])
            del temp_storage[attachment_id]
            
    if saved_filenames:
        user_node.attachment_filenames = ",".join(saved_filenames)
        
    await db.commit() # Final commit for attachments and filenames
    await db.refresh(user_node) # Get latest state with attachments

    async def event_stream():
        try:
            client = OpenRouterClient(api_key)
            engine = CouncilEngine(db, current_user, client)

            yield f"data: {json.dumps({'type': 'start', 'conversation_id': conversation_id})}\n\n"

            # Send User Node to client immediately
            node_data = await serialize_node_with_attachments(db, user_node)
            yield f"data: {json.dumps({'type': 'node', 'node': node_data})}\n\n"

            # Construct Ensemble Prompt
            ensemble_prompt = request.prompt
            if last_synthesis_content:
                ensemble_prompt = f"Context from previous turn:\n{last_synthesis_content}\n\nNew Request: {request.prompt}"

            # We treat the user_node as the root for this turn.
            # However, `run_ensemble_research` uses `root_node.content`.
            # We want to use `ensemble_prompt` but `run_ensemble_research` reads from node.
            # We can create a temporary object or modify `run_ensemble_research` to accept prompt override.
            # Or simpler: Just create a dummy node object in memory with the combined content?
            # Or better: Pass the combined prompt to `run_ensemble_research`.
            # Checking `council_engine.py`: `prompt = f'... user has asked: "{root_node.content}" ...'`
            # So I should probably just modify `run_ensemble_research` to take an optional `prompt_override`.
            # OR I can just create a fake node object with the combined content.

            class MockNode:
                def __init__(self, id, content, parent_id=None, conversation_id=None):
                    self.id = id
                    self.content = content
                    self.parent_id = parent_id
                    self.conversation_id = conversation_id
                    self.model_name = "user" # Default for mock

            mock_root = MockNode(user_node.id, ensemble_prompt, user_node.parent_id, conversation_id)

            # 1. Research
            yield f"data: {json.dumps({'type': 'status', 'message': 'Council members are researching...'})}\n\n"
            research_nodes = await engine.run_ensemble_research(conversation_id, mock_root, request.council_members)
            for node in research_nodes:
                 node_data = await serialize_node_with_attachments(db, node)
                 yield f"data: {json.dumps({'type': 'node', 'node': node_data})}\n\n"

            # 2. Synthesis
            yield f"data: {json.dumps({'type': 'status', 'message': 'Chairman is synthesizing...'})}\n\n"
            # Note: run_ensemble_synthesis uses root_node.content for context.
            synthesis_node = await engine.run_ensemble_synthesis(conversation_id, mock_root, research_nodes, request.chairman_model)
            node_data = await serialize_node_with_attachments(db, synthesis_node)
            yield f"data: {json.dumps({'type': 'node', 'node': node_data})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            import traceback
            import logging
            error_msg = str(e)
            error_trace = traceback.format_exc()
            logging.error(f"Error in superchat stream: {error_trace}")
            yield f"data: {json.dumps({'type': 'error', 'message': error_msg})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")

# ============================================================================
# FILE ATTACHMENT ENDPOINTS
# ============================================================================

from fastapi import UploadFile, File
from fastapi.responses import Response
from models import Attachment
from file_utils import get_file_type, validate_file_size, temp_storage
import uuid

@router.post("/upload")
async def upload_files(
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Upload files temporarily before node creation.
    Returns list of file IDs for attachment to prompt.
    """
    uploaded = []
    
    for file in files:
        # Validate MIME type
        file_type = get_file_type(file.content_type)
        if not file_type:
            raise HTTPException(400, f"Unsupported file type: {file.content_type}")
        
        # Read file data
        file_data = await file.read()
        file_size = len(file_data)
        
        # Validate size
        if not validate_file_size(file_size, file_type):
            raise HTTPException(400, f"File too large: {file.filename}")
        
        # Store temporarily (in-memory)
        file_id = str(uuid.uuid4())
        temp_storage[file_id] = {
            'filename': file.filename,
            'file_type': file_type,
            'mime_type': file.content_type,
            'file_data': file_data,
            'file_size': file_size,
            'user_id': current_user.id
        }
        
        uploaded.append({
            'id': file_id,
            'filename': file.filename,
            'size': file_size,
            'type': file_type
        })
    
    return uploaded

@router.get("/attachments/{attachment_id}")
async def get_attachment(
    attachment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve attachment file"""
    result = await db.execute(
        select(Attachment).where(Attachment.id == attachment_id)
    )
    attachment = result.scalars().first()
    
    if not attachment:
        raise HTTPException(404, "Attachment not found")
    
    # Verify user owns this attachment's conversation
    result = await db.execute(
        select(Node).where(Node.id == attachment.node_id)
    )
    node = result.scalars().first()
    
    if not node:
        raise HTTPException(404, "Node not found")
    
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == node.conversation_id,
            Conversation.user_id == current_user.id
        )
    )
    if not result.scalars().first():
        raise HTTPException(403, "Access denied")
    
    return Response(
        content=attachment.file_data,
        media_type=attachment.mime_type,
        headers={
            'Content-Disposition': f'attachment; filename="{attachment.filename}"'
        }
    )
