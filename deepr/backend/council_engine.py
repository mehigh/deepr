import asyncio
from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from models import Conversation, Node, NodeType, User, UserSettings
from openrouter_service import OpenRouterClient, get_unsupported_attachments
from encryption import decrypt_key
from sqlalchemy import select
import json
import logging

logger = logging.getLogger(__name__)

class CouncilEngine:
    def __init__(self, db: AsyncSession, user: User, openrouter_client: OpenRouterClient):
        self.db = db
        self.user = user
        self.client = openrouter_client

    async def create_node(
        self, 
        conversation_id: int, 
        parent_id: Optional[int], 
        node_type: NodeType, 
        content: str, 
        model_name: str = None, 
        attachment_filenames: str = None, 
        prompt_sent: str = None,
        actual_cost: float = None,
        warnings: str = None
    ):
        node = Node(
            conversation_id=conversation_id,
            parent_id=parent_id,
            type=node_type.value,
            content=content,
            model_name=model_name,
            attachment_filenames=attachment_filenames,
            prompt_sent=prompt_sent,
            actual_cost=actual_cost,
            warnings=warnings
        )
        self.db.add(node)
        await self.db.commit()
        await self.db.refresh(node)
        return node

    async def get_attachments_for_node(self, node_id: int):
        """Get attachments associated with a node"""
        from models import Attachment
        result = await self.db.execute(
            select(Attachment).where(Attachment.node_id == node_id)
        )
        return result.scalars().all()

    async def get_attachments_chain(self, node: Node, max_depth: int = 3):
        """
        Get attachments from node and its ancestors (for SuperChat).
        Limited to max_depth to prevent exponential growth.
        """
        from models import Attachment
        attachments = []
        current = node
        depth = 0
        
        while current and depth < max_depth:
            node_atts = await self.get_attachments_for_node(current.id)
            attachments.extend(node_atts)
            
            if current.parent_id:
                result = await self.db.execute(
                    select(Node).where(Node.id == current.parent_id)
                )
                current = result.scalars().first()
                depth += 1
            else:
                break
        
        return attachments


    async def run_coordinator(self, conversation_id: int, root_node: Node, chairman_model: str) -> Node:
        """
        The Coordinator (Chairman) breaks down the prompt into a research plan.
        """
        # Get attachments using chain (from root node)
        attachments = await self.get_attachments_chain(root_node, max_depth=3)
        attachment_filenames = ",".join([att.filename for att in attachments]) if attachments else None
        
        # Check for warnings (non-vision model with images, etc.)
        warning_list = get_unsupported_attachments(chairman_model, attachments, self.user.id)
        
        prompt = f"""
        You are the Coordinator of a research council. 
        The user has asked: "{root_node.content}"
        
        Break this down into a clear research plan with specific questions or areas to investigate.
        """
        
        # Make API call with cost tracking
        response, cost_info = await self.client.chat_completion_details(
            model=chairman_model,
            messages=[{"role": "user", "content": prompt}],
            attachments=attachments
        )
        
        response_content = response.choices[0].message.content
        
        # Create node with cost and warnings
        return await self.create_node(
            conversation_id, 
            root_node.id, 
            NodeType.PLAN, 
            response_content, 
            model_name=chairman_model,
            attachment_filenames=attachment_filenames,
            prompt_sent=prompt.strip(),
            actual_cost=cost_info['actual_cost'],
            warnings=json.dumps(warning_list) if warning_list else None
        )

    async def run_researchers(self, conversation_id: int, plan_node: Node, council_models: List[str]) -> List[Node]:
        """
        Parallel research by council members based on the plan.
        """
        # Get attachments using chain from plan_node
        attachments = await self.get_attachments_chain(plan_node, max_depth=3)
        attachment_filenames = ",".join([att.filename for att in attachments]) if attachments else None
        
        prompt = f"""
        You are a Council Member researcher.
        Here is the research plan:
        "{plan_node.content}"
        
        Please conduct your research and provide your findings and insights.
        """
        
        tasks = []
        for model in council_models:
            tasks.append(self._fetch_research_with_attachments(model, prompt, attachments))
        
        results = await asyncio.gather(*tasks)
        
        nodes = []
        for model, content, cost_info in results:
            # Get warnings for this specific model
            warning_list = get_unsupported_attachments(model, attachments, self.user.id)
            
            node = await self.create_node(
                conversation_id, 
                plan_node.id, 
                NodeType.RESEARCH, 
                content, 
                model_name=model,
                attachment_filenames=attachment_filenames,
                prompt_sent=prompt.strip(),
                actual_cost=cost_info['actual_cost'],
                warnings=json.dumps(warning_list) if warning_list else None
            )
            nodes.append(node)
            
        return nodes

    async def _fetch_research(self, model: str, prompt: str):
        try:
            response = await self.client.chat_completion(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
            return model, response.choices[0].message.content
        except Exception as e:
            return model, f"Error conducting research: {str(e)}"

    async def _fetch_research_with_attachments(self, model: str, prompt: str, attachments):
        try:
            response, cost_info = await self.client.chat_completion_details(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                attachments=attachments
            )
            return model, response.choices[0].message.content, cost_info
        except Exception as e:
            return model, f"Error conducting research: {str(e)}", {'actual_cost': 0}

    async def run_critics(self, conversation_id: int, research_nodes: List[Node], council_models: List[str]) -> List[Node]:
        """
        Critique phase: Each council member sees the anonymized research of others.
        """
        # Get attachments using chain from first research node
        attachments = await self.get_attachments_chain(research_nodes[0], max_depth=3) if research_nodes else []
        attachment_filenames = ",".join([att.filename for att in attachments]) if attachments else None
        
        # Prepare anonymized context
        context = "Here are the findings from other researchers:\n\n"
        for i, node in enumerate(research_nodes):
            context += f"--- Findings from Agent {i+1} ---\n{node.content}\n\n"
            
        prompt = f"""
        You are a Critic. Review the following research findings from other agents.
        Identify gaps, conflicts, biases, or areas that need more depth.
        
        {context}
        """
        
        tasks = []
        for model in council_models:
            tasks.append(self._fetch_research_with_attachments(model, prompt, attachments))
             
        results = await asyncio.gather(*tasks)
        
        nodes = []
        for model, content, cost_info in results:
            # Get warnings for this specific model
            warning_list = get_unsupported_attachments(model, attachments, self.user.id)
            
            parent_id = research_nodes[0].parent_id if research_nodes else None
            node = await self.create_node(
                conversation_id, 
                parent_id, 
                NodeType.CRITIQUE, 
                content, 
                model_name=model,
                attachment_filenames=attachment_filenames,
                prompt_sent=prompt.strip(),
                actual_cost=cost_info['actual_cost'],
                warnings=json.dumps(warning_list) if warning_list else None
            )
            nodes.append(node)
            
        return nodes

    async def run_synthesis(self, conversation_id: int, plan_node: Node, research_nodes: List[Node], critique_nodes: List[Node], chairman_model: str) -> Node:
        """
        Chairman synthesizes everything.
        """
        # Get attachments using chain from plan_node
        attachments = await self.get_attachments_chain(plan_node, max_depth=3)
        attachment_filenames = ",".join([att.filename for att in attachments]) if attachments else None
        
        # Check for warnings
        warning_list = get_unsupported_attachments(chairman_model, attachments, self.user.id)
        
        context = f"Original Plan:\n{plan_node.content}\n\n"
        
        context += "Research Findings:\n"
        for i, node in enumerate(research_nodes):
            context += f"--- Agent {i+1} ---\n{node.content}\n\n"
            
        context += "Critiques:\n"
        for i, node in enumerate(critique_nodes):
            context += f"--- Critic {i+1} ---\n{node.content}\n\n"
            
        prompt = f"""
        You are the Chairman. Synthesize the final answer based on the research and critiques provided.
        
        Your goal is to provide a comprehensive, reasoned judgment.
        
        IMPORTANT: When you use an idea from a specific Agent or Critic, please reference them in parentheses, e.g., "(Idea by Agent 1)".
        """
        
        response, cost_info = await self.client.chat_completion_details(
            model=chairman_model,
            messages=[{"role": "user", "content": context}, {"role": "user", "content": prompt}],
            attachments=attachments
        )
        content = response.choices[0].message.content
        
        # Link synthesis to the Plan (or maybe the root?)
        return await self.create_node(
            conversation_id, 
            plan_node.id, 
            NodeType.SYNTHESIS, 
            content, 
            model_name=chairman_model,
            attachment_filenames=attachment_filenames,
            prompt_sent=f"{context}\n\n{prompt}".strip(),
            actual_cost=cost_info['actual_cost'],
            warnings=json.dumps(warning_list) if warning_list else None
        )

    async def run_ensemble_research(self, conversation_id: int, root_node: Node, council_models: List[str]) -> List[Node]:
        """
        Parallel research for Ensemble method.
        Directly asks the prompt to all models without a plan.
        """
        # Get attachments using chain from root node
        attachments = await self.get_attachments_chain(root_node, max_depth=3)
        attachment_filenames = ",".join([att.filename for att in attachments]) if attachments else None
        
        prompt = f"""
        You are a Model in an ensemble.
        The user has asked: "{root_node.content}"

        Please answer this question comprehensively from your perspective.
        """

        tasks = []
        for model in council_models:
            tasks.append(self._fetch_research_with_attachments(model, prompt, attachments))

        results = await asyncio.gather(*tasks)

        nodes = []
        for model, content, cost_info in results:
            # Get warnings for this specific model
            warning_list = get_unsupported_attachments(model, attachments, self.user.id)
            
            node = await self.create_node(
                conversation_id, 
                root_node.id, 
                NodeType.RESEARCH, 
                content, 
                model_name=model,
                attachment_filenames=attachment_filenames,
                prompt_sent=prompt.strip(),
                actual_cost=cost_info['actual_cost'],
                warnings=json.dumps(warning_list) if warning_list else None
            )
            nodes.append(node)

        return nodes

    async def run_ensemble_synthesis(self, conversation_id: int, root_node: Node, research_nodes: List[Node], chairman_model: str) -> Node:
        """
        Synthesize all ensemble research into final answer.
        """
        # Get attachments using chain from root node
        attachments = await self.get_attachments_chain(root_node, max_depth=3)
        attachment_filenames = ",".join([att.filename for att in attachments]) if attachments else None
        
        # Check for warnings
        warning_list = get_unsupported_attachments(chairman_model, attachments, self.user.id)
        
        context = f"Original Question:\n{root_node.content}\n\n"
        
        context += "Responses from different models:\n"
        for i, node in enumerate(research_nodes):
            context += f"--- Model {i+1} ({node.model_name}) ---\n{node.content}\n\n"
            
        prompt = f"""
        You are the Synthesizer. Combine the insights from all models into a comprehensive final answer.
        
        Your goal is to provide the best possible answer by synthesizing all perspectives.
        
        IMPORTANT: When you use an idea from a specific model, please reference them, e.g., "(Model 1: GPT-4)".
        """
        
        response, cost_info = await self.client.chat_completion_details(
            model=chairman_model,
            messages=[{"role": "user", "content": context}, {"role": "user", "content": prompt}],
            attachments=attachments
        )
        content = response.choices[0].message.content
        
        return await self.create_node(
            conversation_id, 
            root_node.id, 
            NodeType.SYNTHESIS, 
            content, 
            model_name=chairman_model,
            attachment_filenames=attachment_filenames,
            prompt_sent=f"{context}\n\n{prompt}".strip(),
            actual_cost=cost_info['actual_cost'],
            warnings=json.dumps(warning_list) if warning_list else None
        )

# Global helper to reconstruct the engine context (ugly hack for streaming via global refs if needed, but better to pass dependencies)
