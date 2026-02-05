"""
Unit tests for Lambda handler
Tests API Gateway integration, error handling, and responses
"""
import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.runtime.handler import lambda_handler


class TestLambdaHandler:
    """Test suite for Lambda handler function"""
    
    @pytest.fixture
    def mock_agent(self):
        """Mock BudgetAgent for testing"""
        with patch('src.runtime.handler.BudgetAgent') as mock:
            agent_instance = Mock()
            mock.return_value = agent_instance
            yield agent_instance
    
    @pytest.fixture
    def mock_memory(self):
        """Mock memory setup"""
        with patch('src.runtime.handler.setup_memory') as mock:
            mock.return_value = Mock()
            yield mock
    
    @pytest.fixture
    def mock_invoke(self):
        """Mock invoke_agent function"""
        with patch('src.runtime.handler.invoke_agent') as mock:
            mock.return_value = "Test response from agent"
            yield mock
    
    def test_successful_query(self, mock_agent, mock_memory, mock_invoke):
        """Test successful query processing"""
        event = {
            "body": json.dumps({"query": "What is the carbon tax?"})
        }
        context = Mock()
        
        response = lambda_handler(event, context)
        
        assert response["statusCode"] == 200
        assert "response" in json.loads(response["body"])
        assert json.loads(response["body"])["response"] == "Test response from agent"
        assert "Access-Control-Allow-Origin" in response["headers"]
        mock_invoke.assert_called_once()
    
    def test_missing_query_parameter(self, mock_agent, mock_memory):
        """Test error handling when query parameter is missing"""
        event = {
            "body": json.dumps({})
        }
        context = Mock()
        
        response = lambda_handler(event, context)
        
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert "error" in body
        assert "query" in body["error"].lower()
    
    def test_empty_body(self, mock_agent, mock_memory):
        """Test handling of empty request body"""
        event = {}
        context = Mock()
        
        response = lambda_handler(event, context)
        
        assert response["statusCode"] == 400
        assert "error" in json.loads(response["body"])
    
    def test_invalid_json(self, mock_agent, mock_memory):
        """Test handling of invalid JSON in request body"""
        event = {
            "body": "invalid json{{"
        }
        context = Mock()
        
        response = lambda_handler(event, context)
        
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert "error" in body
        assert "json" in body["error"].lower()
    
    def test_agent_exception(self, mock_agent, mock_memory, mock_invoke):
        """Test error handling when agent raises exception"""
        mock_invoke.side_effect = Exception("Agent processing failed")
        
        event = {
            "body": json.dumps({"query": "test query"})
        }
        context = Mock()
        
        response = lambda_handler(event, context)
        
        assert response["statusCode"] == 500
        body = json.loads(response["body"])
        assert "error" in body
    
    def test_cors_headers_present(self, mock_agent, mock_memory, mock_invoke):
        """Test that CORS headers are present in all responses"""
        event = {
            "body": json.dumps({"query": "test"})
        }
        context = Mock()
        
        response = lambda_handler(event, context)
        
        assert "Access-Control-Allow-Origin" in response["headers"]
        assert response["headers"]["Access-Control-Allow-Origin"] == "*"
        assert response["headers"]["Content-Type"] == "application/json"
    
    def test_logging_on_success(self, mock_agent, mock_memory, mock_invoke, caplog):
        """Test that successful requests are logged"""
        event = {
            "body": json.dumps({"query": "test query"})
        }
        context = Mock()
        
        with caplog.at_level("INFO"):
            lambda_handler(event, context)
        
        # Check that info logs were created
        assert any("Processing query" in record.message for record in caplog.records)
    
    def test_query_with_special_characters(self, mock_agent, mock_memory, mock_invoke):
        """Test handling of queries with special characters"""
        special_query = "What's the budget for 2024/2025?"
        event = {
            "body": json.dumps({"query": special_query})
        }
        context = Mock()
        
        response = lambda_handler(event, context)
        
        assert response["statusCode"] == 200
        mock_invoke.assert_called_once()


class TestLambdaHandlerIntegration:
    """Integration-style tests (still mocked, but testing flow)"""
    
    @patch('src.runtime.handler.invoke_agent')
    @patch('src.runtime.handler.BudgetAgent')
    @patch('src.runtime.handler.setup_memory')
    def test_full_request_flow(self, mock_memory, mock_agent_class, mock_invoke):
        """Test complete request flow from event to response"""
        # Setup mocks
        mock_memory.return_value = Mock()
        mock_agent_instance = Mock()
        mock_agent_class.return_value = mock_agent_instance
        mock_invoke.return_value = "Carbon tax is $65/tonne"
        
        # Create event
        event = {
            "body": json.dumps({
                "query": "What is the carbon tax rate?"
            })
        }
        context = Mock()
        
        # Execute
        response = lambda_handler(event, context)
        
        # Verify
        assert response["statusCode"] == 200
        assert "Carbon tax" in json.loads(response["body"])["response"]
        
        # Verify call chain
        mock_memory.assert_called_once()
        mock_agent_class.assert_called_once_with(mock_memory.return_value)
        mock_invoke.assert_called_once_with(mock_agent_instance, "What is the carbon tax rate?")
