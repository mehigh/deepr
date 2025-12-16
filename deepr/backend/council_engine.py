import asyncio
from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from models import Conversation, Node, NodeType, User, UserSettings
from openrouter_service import OpenRouterClient
from encryption import decrypt_key
from sqlalchemy import select
import json

class CouncilEngine:
    def __init__(self, db: AsyncSession, user: User, openrouter_client: OpenRouterClient):
        self.db = db
        self.user = user
        self.client = openrouter_client

    async def create_node(self, conversation_id: int, parent_id: Optional[int], node_type: NodeType, content: str, model_name: str = None):
        node = Node(
            conversation_id=conversation_id,
            parent_id=parent_id,
            type=node_type.value,
            content=content,
            model_name=model_name
        )
        self.db.add(node)
        await self.db.commit()
        await self.db.refresh(node)
        return node

    async def run_coordinator(self, conversation_id: int, root_node: Node, chairman_model: str) -> Node:
        """
        The Coordinator (Chairman) breaks down the prompt into a research plan.
        """
        prompt = f"""
        You are the Coordinator of a research council. 
        The user has asked: "{root_node.content}"
        
        Create a detailed research plan to answer this question comprehensively. 
        Break it down into key areas of investigation.
        """
        
        response_content = ""
        # For simplicity, we are not streaming here internally, but we could.
        # Ideally, we stream this to the frontend.
        # Using non-streaming for the logic block, but the API endpoint will likely want to stream.
        # Let's assume we collect the full response for the DB.
        
        response = await self.client.chat_completion(
            model=chairman_model,
            messages=[{"role": "user", "content": prompt}]
        )
        response_content = response.choices[0].message.content
        
        return await self.create_node(conversation_id, root_node.id, NodeType.PLAN, response_content, model_name=chairman_model)

    async def run_researchers(self, conversation_id: int, plan_node: Node, council_models: List[str]) -> List[Node]:
        """
        Parallel research by council members based on the plan.
        """
        prompt = f"""
        You are a Council Member researcher.
        Here is the research plan:
        "{plan_node.content}"
        
        Please conduct your research and provide your findings and insights.
        """
        
        tasks = []
        for model in council_models:
            tasks.append(self._fetch_research(model, prompt))
        
        results = await asyncio.gather(*tasks)
        
        nodes = []
        for model, content in results:
            node = await self.create_node(conversation_id, plan_node.id, NodeType.RESEARCH, content, model_name=model)
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

    async def run_critics(self, conversation_id: int, research_nodes: List[Node], council_models: List[str]) -> List[Node]:
        """
        Critique phase: Each council member sees the anonymized research of others.
        """
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
             tasks.append(self._fetch_research(model, prompt))
             
        results = await asyncio.gather(*tasks)
        
        nodes = []
        for model, content in results:
            # Linking to the first research node as a parent is arbitrary but keeps it in the tree.
            # Ideally, we'd link to the PlanNode. 
            # I need to pass the plan_node ID here, but I didn't in the signature.
            # Let's fix this by capturing the plan_node ID from the context or just passing it.
            # Wait, I don't have plan_node available here easily without passing it.
            # I'll rely on the caller to handle flow, but wait, `plan_node` isn't in arguments.
            # I will modify the method signature in the next step or fix it here.
            # Actually, let's just assume `research_nodes[0].parent_id` is the plan node id.
            parent_id = research_nodes[0].parent_id if research_nodes else None
            node = await self.create_node(conversation_id, parent_id, NodeType.CRITIQUE, content, model_name=model)
            nodes.append(node)
            
        return nodes

    async def run_synthesis(self, conversation_id: int, plan_node: Node, research_nodes: List[Node], critique_nodes: List[Node], chairman_model: str) -> Node:
        """
        Chairman synthesizes everything.
        """
        context = f"Original Plan:\n{plan_node.content}\n\n"
        
        context += "Research Findings:\n"
        for i, node in enumerate(research_nodes):
            # We track which model did what internally, so we can ask the synthesizer to attribute.
            # The prompt said "responses are labeled generically... forcing the synthesizer to evaluate the content".
            # BUT the user also said: "maintain references and give praise... (Idea by Agent Alpha)".
            # So I should provide a mapping like "Agent Alpha (Model A)"? Or just "Agent Alpha" and map it back later?
            # User said: "labeled generically... e.g. 'Agent Alpha', 'Agent Beta'".
            # AND "maintain references... so we can learn what opinions count more".
            # So the Synthesizer sees "Agent Alpha", and outputs "(Idea by Agent Alpha)".
            # The UI can then reveal who Agent Alpha was.
            context += f"--- Agent {i+1} ---\n{node.content}\n\n"
            
        context += "Critiques:\n"
        for i, node in enumerate(critique_nodes):
            context += f"--- Critic {i+1} ---\n{node.content}\n\n"
            
        prompt = f"""
        You are the Chairman. Synthesize the final answer based on the research and critiques provided.
        
        Your goal is to provide a comprehensive, reasoned judgment.
        
        IMPORTANT: When you use an idea from a specific Agent or Critic, please reference them in parentheses, e.g., "(Idea by Agent 1)".
        """
        
        response = await self.client.chat_completion(
            model=chairman_model,
            messages=[{"role": "user", "content": context}, {"role": "user", "content": prompt}]
        )
        content = response.choices[0].message.content
        
        # Link synthesis to the Plan (or maybe the root?)
        return await self.create_node(conversation_id, plan_node.id, NodeType.SYNTHESIS, content, model_name=chairman_model)

    async def run_ensemble_research(self, conversation_id: int, root_node: Node, council_models: List[str]) -> List[Node]:
        """
        Parallel research for Ensemble method.
        Directly asks the prompt to all models without a plan.
        """
        prompt = f"""
        You are a Model in an ensemble.
        The user has asked: "{root_node.content}"

        Please answer this question comprehensively from your perspective.
        """

        tasks = []
        for model in council_models:
            tasks.append(self._fetch_research(model, prompt))

        results = await asyncio.gather(*tasks)

        nodes = []
        for model, content in results:
            node = await self.create_node(conversation_id, root_node.id, NodeType.RESEARCH, content, model_name=model)
            nodes.append(node)

        return nodes

    async def run_ensemble_synthesis(self, conversation_id: int, root_node: Node, research_nodes: List[Node], chairman_model: str) -> Node:
        """
        Synthesizes anonymized responses from the ensemble.
        """
        context = f"User Question: {root_node.content}\n\n"

        # Anonymize
        for i, node in enumerate(research_nodes):
            # Using Greek letters or just "Agent Alpha/Beta/Gamma"
            # Let's use simple numeric or Alpha labels
            label = f"Agent {i+1}"
            context += f"--- Response from {label} ---\n{node.content}\n\n"

        prompt = f"""
        You are the Synthesizer. You have received responses from multiple AI agents (anonymized as Agent 1, Agent 2, etc.).

        Your task:
        1. Analyze the responses for consensus and conflict.
        2. Synthesize a single, unified, high-quality response.
        3. Avoid bias towards any specific style.
        4. If you use a specific idea that was unique to one agent, credit them (e.g., "As suggested by Agent 3...").
        """

        response = await self.client.chat_completion(
            model=chairman_model,
            messages=[{"role": "user", "content": context}, {"role": "user", "content": prompt}]
        )
        content = response.choices[0].message.content

        # Link to root node since there is no plan node
        return await self.create_node(conversation_id, root_node.id, NodeType.SYNTHESIS, content, model_name=chairman_model)

# Global helper to reconstruct the engine context (ugly hack for streaming via global refs if needed, but better to pass dependencies)
