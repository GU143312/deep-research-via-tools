"""DeepSeek's documented Search API, exposed as a function tool to Search Agent."""

import json
import os

import httpx
from agents import function_tool

SEARCH_URL = "https://api.deepseek.com/v1/tools/search"


async def search_deepseek(query: str) -> str:
    query = query.strip()
    if not 1 <= len(query) <= 128:
        raise ValueError("Search terms must contain 1-128 characters.")
    async with httpx.AsyncClient(timeout=45, follow_redirects=False) as client:
        response = await client.post(
            SEARCH_URL,
            headers={"Authorization": f"Bearer {os.environ['DEEPSEEK_API_KEY']}"},
            json={"query": query, "count": 5, "need_content": True},
        )
        response.raise_for_status()
        payload = response.json()
    if not isinstance(payload, dict) or not isinstance(payload.get("results"), list):
        raise ValueError("DeepSeek Search returned an invalid response.")
    results = []
    for row in payload["results"][:5]:
        if not isinstance(row, dict) or not isinstance(row.get("url"), str):
            raise ValueError("DeepSeek Search returned a result without a URL.")
        # Bound evidence passed to the LLM; retain URLs exactly for citations.
        results.append(
            {
                "title": str(row.get("title") or "")[:500],
                "url": row["url"],
                "summary": str(row.get("summary") or row.get("snippet") or "")[:3000],
                "content": str(row.get("content") or "")[:6000],
                "date": row.get("date"),
            }
        )
    return json.dumps({"query": query, "results": results}, ensure_ascii=False)


@function_tool(failure_error_function=None)
async def deepseek_web_search(query: str) -> str:
    """Search the live web using DeepSeek; returns evidence and source URLs.

    Args:
        query: A focused search term of 1-128 characters.
    """
    return await search_deepseek(query)
