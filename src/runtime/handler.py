import json
import logging
from src.rag.memory import setup_memory
from src.rag.budget_agent import BudgetAgent
from src.rag.invoke import invoke_agent

# Configure CloudWatch logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    """
    API Gateway → Lambda handler for Budget Agent RAG system
    """
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Parse request body
        body = json.loads(event.get("body", "{}"))
        user_input = body.get("query")

        if not user_input:
            logger.warning("Request missing 'query' parameter")
            return {
                "statusCode": 400,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                },
                "body": json.dumps({"error": "Missing 'query' parameter in request body"})
            }

        logger.info(f"Processing query: {user_input}")
        
        # Initialize agent and process query
        session_manager = setup_memory()
        agent = BudgetAgent(session_manager)
        response = invoke_agent(agent, user_input)

        logger.info("Query processed successfully")
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({"response": response})
        }

    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {str(e)}")
        return {
            "statusCode": 400,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({"error": "Invalid JSON in request body"})
        }
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({"error": "Internal server error", "message": str(e)})
        }
