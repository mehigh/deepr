# DeepR Agents

DeepR employs a multi-agent "Council" architecture where different AI models take on specific roles to ensure comprehensive and unbiased research.

## Core Agents (DAG Workflow)

These agents are used in the standard `DAG` and `Ensemble` workflows.

### 1. The Coordinator
- **Role:** Planning & Strategy.
- **Responsibility:** Receives the user's initial prompt and breaks it down into a structured research plan. It identifies key questions to investigate and assigns them to the Researchers.
- **Model:** Typically a high-reasoning model (e.g., GPT-4o).

### 2. The Council Members (Researchers)
- **Role:** Execution & Investigation.
- **Responsibility:** Each member executes the research tasks assigned by the Coordinator. They work in parallel to gather information, analyze data, and generate initial findings.
- **Diversity:** Users can select multiple different models (e.g., Claude 3 Opus, Llama 3) to ensure cognitive diversity and reduce single-model bias.

### 3. The Critics
- **Role:** Quality Control & Peer Review.
- **Responsibility:** They review the findings of the Researchers. The critique process is **blind** (anonymized) to prevent bias based on the identity of the researching model. They point out logical fallacies, missing context, or weak arguments.

### 4. The Chairman
- **Role:** Synthesis & Final Decision.
- **Responsibility:** The Chairman reads the original plan, the research findings, and the critiques. It then synthesizes everything into a final, comprehensive answer for the user.
- **Nature:** Acts as the final arbiter and voice of the Council.

## Diagnostic Orchestration (DxO) Agents

The DxO workflow uses a more flexible, role-based panel approach. The system dynamically executes all roles defined in the panel.

### 1. Lead Researcher (Proposer)
- **Focus:** Primary analysis and synthesis.
- **Role in Workflow:** Drafts the initial proposal and refines it based on feedback from the Council.
- **Identity:** The first role defined in the panel, or explicitly named "Lead Researcher/Architect".

### 2. The Council (Reviewers)
- **Focus:** Multi-perspective feedback.
- **Role in Workflow:** All other roles defined in the panel act as reviewers. They analyze the proposal in parallel.
- **Specializations:**
    - **Critical Reviewer:** If a role is named "Critical Reviewer", it performs a scored critique (Confidence Score).
    - **QA / Quality Assurance:** If a role is named "QA" or "Quality", it generates specific Test Cases instead of a general critique.
    - **Domain Experts:** Any other custom roles (e.g., "Legal", "Security", "UX") generate standard critiques based on their specific system instructions.

### 3. Loop Execution
- The process iterates (Draft -> Review -> Refine) up to 3 times or until the "Critical Reviewer" assigns a confidence score >= 85%.

## Collaboration Workflow

To ensure smooth collaboration between human developers and AI agents (Jules) on the same branch:

1.  **Pull Before Working**: Always pull the latest changes from the branch before starting any new task to avoid conflicts.
2.  **Commit After Completing**: Commit all changes immediately after completing a task or request.
