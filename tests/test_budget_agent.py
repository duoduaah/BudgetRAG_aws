"""
Unit tests for BudgetAgent
Tests agent initialization and configuration
"""
import pytest
import os
from unittest.mock import Mock, patch
from src.rag.budget_agent import BudgetAgent


class TestBudgetAgent:
    """Test suite for BudgetAgent class"""
    
    @pytest.fixture
    def mock_agent(self):
        """Mock the Strands Agent"""
        with patch('src.rag.budget_agent.Agent') as mock:
            yield mock
    
    @pytest.fixture
    def mock_search_tool(self):
        """Mock the search tool"""
        with patch('src.rag.budget_agent.search_knowledge_base') as mock:
            yield mock
    
    def test_agent_initialization_without_memory(self, mock_agent, mock_search_tool):
        """Test agent can be initialized without session manager"""
        budget_agent = BudgetAgent()
        
        assert budget_agent.session_manager is None
        mock_agent.assert_called_once()
    
    def test_agent_initialization_with_memory(self, mock_agent, mock_search_tool):
        """Test agent initialization with session manager"""
        mock_session = Mock()
        
        budget_agent = BudgetAgent(session_manager=mock_session)
        
        assert budget_agent.session_manager == mock_session
        # Verify Agent was called with session_manager
        call_kwargs = mock_agent.call_args[1]
        assert call_kwargs['session_manager'] == mock_session
    
    def test_agent_has_search_tool(self, mock_agent, mock_search_tool):
        """Test that search tool is configured"""
        BudgetAgent()
        
        call_kwargs = mock_agent.call_args[1]
        assert 'tools' in call_kwargs
        assert mock_search_tool in call_kwargs['tools']
    
    @patch.dict(os.environ, {'BEDROCK_MODEL_ID': 'test-model-id'})
    def test_uses_environment_model_id(self, mock_agent, mock_search_tool):
        """Test that model ID is loaded from environment"""
        BudgetAgent()
        
        call_kwargs = mock_agent.call_args[1]
        assert call_kwargs['model'] == 'test-model-id'
    
    def test_agent_has_system_prompt(self, mock_agent, mock_search_tool):
        """Test that agent is configured with system prompt"""
        BudgetAgent()
        
        call_kwargs = mock_agent.call_args[1]
        assert 'system_prompt' in call_kwargs
        system_prompt = call_kwargs['system_prompt']
        assert len(system_prompt) > 0
        assert 'budget' in system_prompt.lower()
    
    def test_system_prompt_mentions_visual_grounding(self, mock_agent, mock_search_tool):
        """Test that system prompt includes visual grounding instructions"""
        BudgetAgent()
        
        call_kwargs = mock_agent.call_args[1]
        system_prompt = call_kwargs['system_prompt']
        assert 'visual grounding' in system_prompt.lower()
        assert 'page' in system_prompt.lower()
    
    def test_system_prompt_mentions_memory(self, mock_agent, mock_search_tool):
        """Test that system prompt includes memory capabilities"""
        BudgetAgent()
        
        call_kwargs = mock_agent.call_args[1]
        system_prompt = call_kwargs['system_prompt']
        assert 'memory' in system_prompt.lower()
        assert 'remember' in system_prompt.lower()
    
    def test_agent_name_is_set(self, mock_agent, mock_search_tool):
        """Test that agent has a descriptive name"""
        BudgetAgent()
        
        call_kwargs = mock_agent.call_args[1]
        assert 'name' in call_kwargs
        assert 'Budget' in call_kwargs['name']
        assert 'Canada' in call_kwargs['name']
