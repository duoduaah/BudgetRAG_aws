import os
from datetime import datetime
from bedrock_agentcore.memory import MemoryClient
from bedrock_agentcore.memory.integrations.strands.config import AgentCoreMemoryConfig
from bedrock_agentcore.memory.integrations.strands.session_manager import AgentCoreMemorySessionManager

def setup_memory():
    memory_client = MemoryClient(region_name=os.getenv("AWS_REGION", "ca-central-1"))

    try:
        existing_memories = memory_client.gmcp_client.list_memories()
        memory_list = existing_memories.get('memories', [])
        
        budget_memories = [m for m in memory_list if 'BudgetAgentMemory' in m.get('id', '')]
        
        if budget_memories:
            # Sort by creation date and take the most recent
            budget_memories.sort(key=lambda x: x.get('createdAt', ''), reverse=True)
            existing_budget_memory = budget_memories[0]
            MEMORY_ID = existing_budget_memory.get('id')
        else:
            # Only create if none exist
            raise Exception("No existing BudgetAgentMemory found, will create new one")
            
    except Exception as e:
        print(f" Creating new memory... (Reason: {e})")
        try:
            # Add timestamp to make name unique
            comprehensive_memory = memory_client.create_memory_and_wait(
                name=f"BudgetAgentMemory_{datetime.now().strftime('%Y%m%d_%H%M%S')}", 
                description="Memory for budget document analysis with user preferences",
                strategies=[
                    {
                        "summaryMemoryStrategy": {
                            "name": "SessionSummarizer",
                            "namespaces": ["/summaries/{actorId}/{sessionId}"]
                        }
                    },
                    {
                        "userPreferenceMemoryStrategy": {
                            "name": "PreferenceLearner",
                            "namespaces": ["/preferences/{actorId}"]
                        }
                    },
                    {
                        "semanticMemoryStrategy": {
                            "name": "FactExtractor",
                            "namespaces": ["/facts/{actorId}"]
                        }
                    }
                ]
            )
            MEMORY_ID = comprehensive_memory.get('id')
            print(f" New memory created: {MEMORY_ID}")
        except Exception as create_error:
            print(f" Could not create memory: {create_error}")
            print("Continuing without memory functionality...")
            MEMORY_ID = None


    if MEMORY_ID:
        ACTOR_ID = f"user_{datetime.now().strftime('%H%M%S')}"
        SESSION_ID = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        print(f"   Actor: {ACTOR_ID}")
        print(f"   Session: {SESSION_ID}")

        # Configure memory
        memory_config = AgentCoreMemoryConfig(
            memory_id=MEMORY_ID,
            session_id=SESSION_ID,
            actor_id=ACTOR_ID
        )

        # Create session manager
        session_manager = AgentCoreMemorySessionManager(
            agentcore_memory_config=memory_config,
            region_name=os.getenv("AWS_REGION", "ca-central-1")
        )
    else:
        session_manager = None
        print("Agent will run without memory")

    return session_manager