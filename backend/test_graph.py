"""Quick smoke test for the LangGraph pipeline.

Run from the project root:
    cd backend && python test_graph.py
"""
import asyncio
from app.graph.builder import graph


async def main():
    initial_state = {
        "user_prompt": "Build a simple Todo List app using FastAPI and React with PostgreSQL.",
        "requirements": {},
        "architecture": {},
        "database_schema": {},
        "backend_code": {},
        "frontend_code": {},
        "review_report": {},
        "security_report": {},
        "testing_report": {},
        "bugfix_report": {},
        "documentation": {},
        "deployment": {},
        "status": "running",
        "current_agent": "PM",
        "log": [],
    }

    print("Starting CodeSmith AI pipeline...")
    
    # Graphs compiled with a checkpointer require a thread_id in the config
    config = {"configurable": {"thread_id": "smoke-test-thread"}}
    
    # Run the pipeline asynchronously
    result = await graph.ainvoke(initial_state, config=config)

    print("\nPipeline completed!")
    print(f"   Agents run: {[entry['agent'] for entry in result.get('log', [])]}")
    print(f"   Status: {result.get('status')}")
    print(f"   Project: {result.get('requirements', {}).get('project_name', 'N/A')}")


if __name__ == "__main__":
    asyncio.run(main())
