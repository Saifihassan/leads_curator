from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
import os
import requests
import asyncio
import nest_asyncio

# Apply nest_asyncio to allow asyncio.run() in environments where a loop is already running
nest_asyncio.apply()

class SearxngSearchToolInput(BaseModel):
    """Input schema for SearxngSearchTool."""
    query: str = Field(..., description="The search query to execute on Searxng.")

class SearxngSearchTool(BaseTool):
    name: str = "Searxng Search Tool"
    description: str = (
        "Useful for searching the web using a Searxng instance. "
        "Provide a search query to get relevant results."
    )
    args_schema: Type[BaseModel] = SearxngSearchToolInput

    def _run(self, query: str) -> str:
        searxng_url = os.getenv("SEARXNG_URL")
        try:
            response = requests.get(
                f"{searxng_url}/search",
                params={"q": query, "format": "json"}
            )
            response.raise_for_status()
            data = response.json()
            results = data.get("results", [])
            
            output = []
            for res in results[:20]:  # return top 5
                output.append(f"Title: {res.get('title')}\nURL: {res.get('url')}\nContent: {res.get('content')}\n")
            
            return "\n".join(output) if output else "No results found."
        except Exception as e:
            return f"Error performing search: {e}"

class Crawl4aiSearchToolInput(BaseModel):
    """Input schema for Crawl4aiSearchTool."""
    url: str = Field(..., description="The URL of the webpage to crawl.")

class Crawl4aiSearchTool(BaseTool):
    name: str = "Crawl4AI Search Tool"
    description: str = (
        "Useful for crawling a specific webpage URL and extracting its markdown content."
    )
    args_schema: Type[BaseModel] = Crawl4aiSearchToolInput

    def _run(self, url: str) -> str:
        try:
            from crawl4ai import AsyncWebCrawler
            
            async def _crawl():
                async with AsyncWebCrawler() as crawler:
                    result = await crawler.arun(url=url)
                    return result.markdown
            
            return asyncio.run(_crawl())
        except Exception as e:
            return f"Error crawling webpage: {e}"
