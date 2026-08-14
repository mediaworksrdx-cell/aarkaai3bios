import sys
import os
import asyncio
sys.path.append(os.getcwd())

# Ensure weasyprint can find libraries if needed, though it's already installed
import pipeline

async def test():
    query = "Create a premium PDF report about Chennai tech startups"
    print("Running stream_query for PDF...")
    async for chunk in pipeline.stream_query(query):
        if chunk.get("type") == "status":
            print(f"[STATUS] {chunk.get('status')}")
        elif chunk.get("type") == "content":
            print(chunk.get("token"), end="", flush=True)
    print("\nDone.")

if __name__ == "__main__":
    # Initialize engine if needed, pipeline handles it
    asyncio.run(test())
