import asyncio
from codesight.server.mcp_server import call_tool
from codesight.config import settings
from pathlib import Path

async def test():
    settings.codebase_path = Path("/Volumes/Work/AI Work/AI Learning")
    print(f"Codebase path: {settings.codebase_path}")
    try:
        results = await call_tool("plan_refactor", {
            "old_name": "classify_answerability",
            "new_name": "can_answer_question",
            "file_hint": "rag_classification.py"
        })
        for r in results:
            print(r.text)
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
