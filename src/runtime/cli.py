from src.rag.budget_agent import BudgetAgent
from src.rag.memory import setup_memory
from src.rag.invoke import invoke_agent


def run_interactive_chat():
    session_manager = setup_memory()
    agent = BudgetAgent(session_manager)

    print("Interactive chat started. Type 'exit' to quit.\n")

    try:
        while True:
            user_input = input("User: ").strip()

            if user_input.lower() in {"exit", "quit"}:
                print("Ending session.")
                break

            response = invoke_agent(agent, user_input)
            print(f"Agent: {response}\n")

    except Exception as e:
        print(e)


if __name__ == "__main__":
    run_interactive_chat()