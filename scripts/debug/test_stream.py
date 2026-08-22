import asyncio
import sys
sys.path.append('C:\\Users\\daarv\\.gemini\\antigravity\\scratch\\aarkaai3b')
from pipeline import stream_query

async def test():
    async for chunk in stream_query('what is the price of gold'):
        print(chunk)

asyncio.run(test())
