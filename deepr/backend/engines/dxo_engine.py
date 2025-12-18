import asyncio
import json
import re
from typing import List, Dict, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from models import Conversation, Node, NodeType, User
from openrouter_service import OpenRouterClient

class DxOEngine:
    def __init__(self, db: AsyncSession, user: User, openrouter_client: OpenRouterClient):
        self.db = db
        self.user = user
        self.client = openrouter_client

    async def create_node(self, conversation_id: int, parent_id: Optional[int], node_type: str, content: str, model_name: str = None, metadata: Dict = None):
        node = Node(
            conversation_id=conversation_id,
            parent_id=parent_id,
            type=node_type,
            content=content,
            model_name=model_name
        )
        self.db.add(node)
        await self.db.commit()
        await self.db.refresh(node)
        return node

    async def run_dxo_pipeline(self, conversation_id: int, root_node: Node, roles: List[Dict], max_iterations: int = 3):
        """
        Orchestrates the DxO workflow:
        Phase A: Proposal (Lead System Architect)
        Phase B: Multi-Perspective Review (Council Members)
        Phase C: Defense & Refinement Loop (Lead Architect)
        Phase D: Convergence
        """

        if not roles:
             # Just in case
             yield json.dumps({'type': 'error', 'message': 'No roles defined!'})
             return

        # 1. Identify Roles
        # Proposer is the first role or one named "Lead..."
        proposer_role = next((r for r in roles if "Lead" in r['name'] or "Architect" in r['name'] or "Researcher" in r['name']), roles[0])
        
        # Identify Reviewers (Everyone else)
        # We filter out the proposer from the reviewer list to avoid self-critique (unless explicit?)
        # For simplicity, everyone else is a reviewer.
        reviewers = [r for r in roles if r['name'] != proposer_role['name']]

        # Critic and QA are special roles that trigger specific actions, but they are also reviewers.
        critic_role = next((r for r in roles if "Critical Reviewer" in r['name']), None)
        qa_role = next((r for r in roles if "QA" in r['name'] or "Quality" in r['name']), None)

        if not reviewers and len(roles) > 1:
             # If filter by name failed but we have other roles, treat them as reviewers
             reviewers = roles[1:]

        # Phase A: Proposal
        yield json.dumps({'type': 'status', 'message': f'Phase A: {proposer_role["name"]} is drafting the proposal...'})

        proposal_prompt = f"""
        You are the {proposer_role['name']}.
        Instructions: {proposer_role.get('instructions', '')}

        User Request: "{root_node.content}"

        Please provide a solid initial design/response. Focus on structure, patterns, and scalability.
        """

        response = await self.client.chat_completion(
            model=proposer_role['model'],
            messages=[{"role": "user", "content": proposal_prompt}]
        )
        draft_content = response.choices[0].message.content
        draft_node = await self.create_node(conversation_id, root_node.id, "proposal", draft_content, model_name=proposer_role['model'])
        yield json.dumps({'type': 'node', 'node': {'id': draft_node.id, 'type': 'proposal', 'content': draft_node.content, 'model': draft_node.model_name}})

        # Loop
        iteration = 0
        # max_iterations used from arg
        confidence_score = 0

        while iteration < max_iterations and confidence_score < 85:
            iteration += 1
            yield json.dumps({'type': 'status', 'message': f'Phase B: Council Review (Loop {iteration})...'})

            # Collect all feedback content for the proposer to see
            feedback_collection = []
            
            # Run all reviewers in parallel (Phase B)
            # We create a coroutine for each reviewer
            async def run_reviewer(role):
                is_critic = role.get('name') == "Critical Reviewer"
                is_qa = "QA" in role.get('name') or "Quality" in role.get('name')

                review_prompt = ""
                node_type = "critique" # Default type for everyone

                if is_critic:
                     review_prompt = f"""
                     You are the {role['name']}.
                     Instructions: {role.get('instructions', 'TEAR DOWN the proposal. Scan for risks, flaws, complexity.')}
                     
                     Review the following draft:
                     {draft_content}
                     
                     Output a Critique Report.
                     IMPORTANT: You must include a "Confidence Score" (0-100) indicating your confidence in the design's safety and completeness.
                     Format your response as JSON or clearly structured text where "Score: X" can be parsed.
                     """
                elif is_qa:
                     node_type = "test_cases"
                     review_prompt = f"""
                     You are the {role['name']}.
                     Instructions: {role.get('instructions', 'Generate test cases.')}
                     
                     Draft:
                     {draft_content}
                     
                     Generate specific test cases to validate this design.
                     """
                else:
                     # General Council Member
                     review_prompt = f"""
                     You are the {role['name']}.
                     Instructions: {role.get('instructions', 'Provide your domain-specific perspective.')}
                     
                     Review the following draft:
                     {draft_content}
                     
                     Provide your analysis, pointed critiques, or suggestions based on your expertise.
                     """

                response = await self.client.chat_completion(
                    model=role['model'],
                    messages=[{"role": "user", "content": review_prompt}]
                )
                content = response.choices[0].message.content
                
                # Extract score if critic
                score = 0
                if is_critic:
                    score_match = re.search(r'(?:Confidence )?Score:\s*(\d+)', content, re.IGNORECASE)
                    if score_match:
                        score = int(score_match.group(1))
                
                # Create Node
                # We use 'critique' type for general reviewers so frontend renders them in the critique list
                # We use 'test_cases' for QA
                # Pass the Role Name as the "model_name" so the frontend displays "Critical Reviewer" 
                # instead of just the raw model string.
                display_name = f"{role['name']} ({role['model']})"
                new_node = await self.create_node(conversation_id, draft_node.id, node_type, content, model_name=display_name)
                
                return {
                    'role': role['name'],
                    'content': content,
                    'score': score,
                    'node': new_node,
                    'type': node_type
                }

            # Execute parallel
            tasks = [run_reviewer(r) for r in reviewers]
            if tasks:
                results = await asyncio.gather(*tasks)
            else:
                results = []

            # Process Results
            current_loop_score = 0
            has_critic = False

            for res in results:
                feedback_collection.append(f"--- Feedback from {res['role']} ---\n{res['content']}\n")
                
                # Emit to frontend
                yield json.dumps({'type': 'node', 'node': {
                    'id': res['node'].id, 
                    'type': res['type'], 
                    'content': res['content'], 
                    'model': res['node'].model_name,
                    'score': res['score'] if res['role'] == "Critical Reviewer" else 0
                }})

                if res['role'] == "Critical Reviewer":
                    current_loop_score = res['score']
                    has_critic = True

            # If no explicit critic, maybe average scores? or just assume low confidence to force iteration?
            # Or if no critics exist, we might break automatically?
            if has_critic:
                confidence_score = current_loop_score
            else:
                # If no critic, we can't judge "85%". 
                # If we have iterations left, we iterate. If it's 3rd loop, we stop.
                # Let's set a default 'progress' score to allow loops but not infinite.
                confidence_score = 50 + (iteration * 15) # Artificial progress if no critic

            if confidence_score >= 85:
                break

            # Phase C: Refinement
            yield json.dumps({'type': 'status', 'message': f'Phase C: {proposer_role["name"]} is refining the design...'})

            all_feedback = "\n".join(feedback_collection)

            refine_prompt = f"""
            You are the {proposer_role['name']}.
            Your previous design received a score of {confidence_score}%.

            Feedback from the Council:
            {all_feedback}

            Fix the issues identified. Provide a new version (Draft_v{iteration+1}).
            """

            response = await self.client.chat_completion(
                model=proposer_role['model'],
                messages=[{"role": "user", "content": refine_prompt}]
            )
            draft_content = response.choices[0].message.content
            draft_node = await self.create_node(conversation_id, draft_node.id, "refinement", draft_content, model_name=proposer_role['model'])
            yield json.dumps({'type': 'node', 'node': {'id': draft_node.id, 'type': 'refinement', 'content': draft_content, 'model': draft_node.model_name}})

        # Final Verdict
        yield json.dumps({'type': 'status', 'message': 'Finalizing result...'})
        final_verdict = f"""
        Final Output
        Status: {"APPROVED" if confidence_score >= 85 else "Review Limit Reached"} (Confidence: {confidence_score}%)
        Iterations: {iteration} Loops

        EXECUTIVE SUMMARY:
        (See final draft)
        """
        # Create a final node that points to the last draft
        final_node = await self.create_node(conversation_id, draft_node.id, "verdict", final_verdict, model_name="System")
        yield json.dumps({'type': 'node', 'node': {'id': final_node.id, 'type': 'verdict', 'content': final_verdict, 'model': 'System'}})
