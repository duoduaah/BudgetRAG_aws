"""
Unit tests for memory management
Tests session creation, retrieval, and error handling
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from src.rag.memory import setup_memory


class TestMemorySetup:
    """Test suite for memory setup and management"""
    
    @pytest.fixture
    def mock_memory_client(self):
        """Mock MemoryClient"""
        with patch('src.rag.memory.MemoryClient') as mock:
            client_instance = Mock()
            mock.return_value = client_instance
            yield client_instance
    
    @pytest.fixture
    def mock_session_manager(self):
        """Mock AgentCoreMemorySessionManager"""
        with patch('src.rag.memory.AgentCoreMemorySessionManager') as mock:
            yield mock
    
    def test_uses_existing_memory_when_available(self, mock_memory_client, mock_session_manager):
        """Test that existing memory is reused instead of creating new"""
        # Setup mock to return existing memory
        mock_memory_client.gmcp_client.list_memories.return_value = {
            'memories': [
                {
                    'id': 'BudgetAgentMemory_20260204_120000',
                    'name': 'BudgetAgentMemory_20260204_120000',
                    'createdAt': '2026-02-04T12:00:00Z'
                }
            ]
        }
        
        result = setup_memory()
        
        # Should not create new memory
        mock_memory_client.create_memory_and_wait.assert_not_called()
        # Should create session manager with existing memory ID
        mock_session_manager.assert_called_once()
    
    def test_creates_new_memory_when_none_exists(self, mock_memory_client, mock_session_manager):
        """Test memory creation when no existing memory found"""
        # Setup mock to return empty list
        mock_memory_client.gmcp_client.list_memories.return_value = {
            'memories': []
        }
        
        # Mock the create_memory_and_wait response
        mock_memory_client.create_memory_and_wait.return_value = Mock(id='new_memory_id')
        
        result = setup_memory()
        
        # Should create new memory
        mock_memory_client.create_memory_and_wait.assert_called_once()
        call_kwargs = mock_memory_client.create_memory_and_wait.call_args[1]
        assert 'BudgetAgentMemory' in call_kwargs['name']
        assert 'strategies' in call_kwargs
    
    def test_uses_most_recent_memory(self, mock_memory_client, mock_session_manager):
        """Test that most recent memory is selected when multiple exist"""
        mock_memory_client.gmcp_client.list_memories.return_value = {
            'memories': [
                {
                    'id': 'BudgetAgentMemory_20260204_100000',
                    'createdAt': '2026-02-04T10:00:00Z'
                },
                {
                    'id': 'BudgetAgentMemory_20260204_120000',
                    'createdAt': '2026-02-04T12:00:00Z'  # Most recent
                },
                {
                    'id': 'BudgetAgentMemory_20260204_110000',
                    'createdAt': '2026-02-04T11:00:00Z'
                }
            ]
        }
        
        result = setup_memory()
        
        # Should use the most recent memory (12:00:00)
        mock_session_manager.assert_called_once()
        call_args = mock_session_manager.call_args
        # The memory ID should be from the most recent entry
        assert 'BudgetAgentMemory_20260204_120000' in str(call_args)
    
    def test_memory_strategies_configuration(self, mock_memory_client, mock_session_manager):
        """Test that memory is created with correct strategies"""
        mock_memory_client.gmcp_client.list_memories.return_value = {'memories': []}
        mock_memory_client.create_memory_and_wait.return_value = Mock(id='new_memory')
        
        setup_memory()
        
        call_kwargs = mock_memory_client.create_memory_and_wait.call_args[1]
        strategies = call_kwargs['strategies']
        
        # Check all three strategies are configured
        assert len(strategies) == 3
        strategy_names = [list(s.keys())[0] for s in strategies]
        assert 'summaryMemoryStrategy' in strategy_names
        assert 'userPreferenceMemoryStrategy' in strategy_names
        assert 'semanticMemoryStrategy' in strategy_names
    
    def test_handles_list_memories_exception(self, mock_memory_client, mock_session_manager):
        """Test graceful handling when listing memories fails"""
        mock_memory_client.gmcp_client.list_memories.side_effect = Exception("API Error")
        mock_memory_client.create_memory_and_wait.return_value = Mock(id='fallback_memory')
        
        result = setup_memory()
        
        # Should fall back to creating new memory
        mock_memory_client.create_memory_and_wait.assert_called_once()
    
    @patch('src.rag.memory.os.getenv')
    def test_uses_correct_aws_region(self, mock_getenv, mock_memory_client, mock_session_manager):
        """Test that correct AWS region is used"""
        mock_getenv.return_value = "us-west-2"
        mock_memory_client.gmcp_client.list_memories.return_value = {'memories': []}
        mock_memory_client.create_memory_and_wait.return_value = Mock(id='test_memory')
        
        with patch('src.rag.memory.MemoryClient') as mock_client_class:
            mock_client_class.return_value = mock_memory_client
            setup_memory()
            
            mock_client_class.assert_called_once_with(region_name="us-west-2")
    
    def test_returns_session_manager(self, mock_memory_client, mock_session_manager):
        """Test that function returns a session manager instance"""
        mock_memory_client.gmcp_client.list_memories.return_value = {
            'memories': [{'id': 'test_memory', 'createdAt': '2026-02-04T12:00:00Z'}]
        }
        
        mock_session_manager_instance = Mock()
        mock_session_manager.return_value = mock_session_manager_instance
        
        result = setup_memory()
        
        assert result == mock_session_manager_instance
