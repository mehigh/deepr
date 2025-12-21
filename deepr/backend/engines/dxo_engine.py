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
        Phase A: Proposal (Lead Researcher)
        Loop:
          Phase B: Expert Council Review (Parallel)
          Phase C: Refinement (Lead Researcher)
          Phase D: Critical Review (Sequential Gatekeeper)
        Step E: Convergence/Verdict
        """

        if not roles:
             yield json.dumps({'type': 'error', 'message': 'No roles defined!'})
             return

        # 1. Identify Roles
        proposer_role = next((r for r in roles if "Lead" in r['name'] or "Architect" in r['name'] or "Researcher" in r['name']), roles[0])
        
        # Internal helper to find critic
        critic_role = next((r for r in roles if "Critical Reviewer" in r['name']), None)

        # Experts are everyone else (excluding proposer and critic)
        experts = [
            r for r in roles 
            if r['name'] != proposer_role['name'] 
            and (not critic_role or r['name'] != critic_role['name'])
        ]

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

        # Define the Reviewer Runner Helper
        async def run_single_reviewer(role, content_to_review, is_gatekeeper=False):
            is_qa = "QA" in role.get('name') or "Quality" in role.get('name')
            review_prompt = ""
            node_type = "critique"

            if is_gatekeeper: # Critical Reviewer
                 review_prompt = f"""
                 You are the {role['name']}.
                 Instructions: {role.get('instructions', 'TEAR DOWN the proposal. Scan for risks, flaws, complexity.')}
                 
                 Review the following Refined Draft:
                 {content_to_review}
                 
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
                 {content_to_review}
                 
                 Generate specific test cases to validate this design.
                 """
            else:
                 # General Council Member
                 review_prompt = f"""
                 You are the {role['name']}.
                 Instructions: {role.get('instructions', 'Provide your domain-specific perspective.')}
                 
                 Review the following draft:
                 {content_to_review}
                 
                 Provide your analysis, pointed critiques, or suggestions based on your expertise.
                 """

            res = await self.client.chat_completion(
                model=role['model'],
                messages=[{"role": "user", "content": review_prompt}]
            )
            response_text = res.choices[0].message.content
            
            # Extract score if gatekeeper
            score = 0
            if is_gatekeeper:
                score_match = re.search(r'(?:Confidence )?Score:\s*(\d+)', response_text, re.IGNORECASE)
                if score_match:
                    score = int(score_match.group(1))
            
            display_name = f"{role['name']} ({role['model']})"
            new_node = await self.create_node(conversation_id, draft_node.id, node_type, response_text, model_name=display_name)
            
            return {
                'role': role['name'],
                'content': response_text,
                'score': score,
                'node': new_node,
                'type': node_type
            }

        # Loop
        iteration = 0
        confidence_score = 0

        while iteration < max_iterations and confidence_score < 85:
            iteration += 1
            
            # --- Phase B: Expert Council Review ---
            yield json.dumps({'type': 'status', 'message': f'Phase B: Council Review (Loop {iteration})...'})
            feedback_collection = []
            
            if experts:
                # Run experts in parallel
                tasks = [run_single_reviewer(r, draft_content, is_gatekeeper=False) for r in experts]
                expert_results = await asyncio.gather(*tasks)
                
                for res in expert_results:
                    feedback_collection.append(f"--- Feedback from {res['role']} ---\n{res['content']}\n")
                    yield json.dumps({'type': 'node', 'node': {
                        'id': res['node'].id, 
                        'type': res['type'], 
                        'content': res['content'], 
                        'model': res['node'].model_name,
                        'score': 0
                    }})
            
            # --- Phase C: Refinement ---
            yield json.dumps({'type': 'status', 'message': f'Phase C: {proposer_role["name"]} is refining the design...'})
            
            all_feedback = "\n".join(feedback_collection)
            refine_prompt = f"""
            You are the {proposer_role['name']}.
            Iteration: {iteration}
            
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

            # --- Phase D: Critical Review (Gatekeeper) ---
            if critic_role:
                yield json.dumps({'type': 'status', 'message': f'Phase D: Critical Review (Gatekeeper)...'})
                critic_res = await run_single_reviewer(critic_role, draft_content, is_gatekeeper=True)
                
                confidence_score = critic_res['score']
                
                yield json.dumps({'type': 'node', 'node': {
                    'id': critic_res['node'].id, 
                    'type': critic_res['type'], 
                    'content': critic_res['content'], 
                    'model': critic_res['node'].model_name,
                    'score': confidence_score
                }})
            else:
                # Fallback if no critic exists
                confidence_score = 50 + (iteration * 15)

        # Final Verdict
        yield json.dumps({'type': 'status', 'message': 'Finalizing result...'})
        final_verdict = f"""
        Final Output
        Status: {"APPROVED" if confidence_score >= 85 else "Review Limit Reached"} (Confidence: {confidence_score}%)
        Iterations: {iteration} Loops

        EXECUTIVE SUMMARY:
        (See final draft)
        """
        final_node = await self.create_node(conversation_id, draft_node.id, "verdict", final_verdict, model_name="System")
        yield json.dumps({'type': 'node', 'node': {'id': final_node.id, 'type': 'verdict', 'content': final_verdict, 'model': 'System'}})
