import os
from strands import Agent
from src.rag.search_tool import search_knowledge_base  

class BudgetAgent:
    """Budget analysis agent with memory and visual grounding"""
    
    def __init__(self, session_manager=None):
        """
        Initialize budget agent
        
        Args:
            session_manager: Optional AgentCore memory session manager
        """
        self.session_manager = session_manager
        self.agent = Agent(
            model=os.getenv("BEDROCK_MODEL_ID"),
            name="Canada Annual Budget Document Analyzer",
            system_prompt=self._get_system_prompt(),
            session_manager=session_manager,
            tools=[search_knowledge_base]
        )
    
    def _get_system_prompt(self):
        return """
        You are a government budget document analysis assistant with memory capabilities and visual grounding support.
        You remember our conversations, user preferences, and important facts.
        
        Your capabilities:
        - Search and analyze budget documents from the knowledge base
        - Provide visual grounding information showing exact locations in documents
        - Display page numbers and bounding box coordinates when available
        - Reference annotated images that highlight specific document regions
        - Remember user preferences and conversation history
        - Learn from interactions to improve future responses
        
        IMPORTANT: When you receive search results that include visual grounding information, you MUST include:
        - Page numbers where information was found
        - Location coordinates showing exact position on the page
        - Annotated image URLs that show highlighted text regions
        
        When search results contain these visual markers, preserve them in your response. Do not summarize away the visual grounding details.
        
        Visual grounding format to preserve:
        - **Page:** [number] - shows which page contains the information
        - **Location:** [coordinates] - shows exact position on the page
        - **Annotated Image:** [URL] - provides visual highlight of the referenced text
        
        Always provide evidence-based insights from the documents with visual references when available.
        When visual grounding is provided in search results, include it in your response to help users see exactly where information comes from.
        """
    
    def __call__(self, question: str) -> str:
        """
        Call agent with question, return response
        
        Args:
            question: User's question
            
        Returns:
            Agent's response
        """
        return self.agent(question)