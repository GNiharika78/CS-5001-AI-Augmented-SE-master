from ddgs import DDGS


class WebSearchTool:
    def search(self, query: str, top_k: int = 5):
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=top_k):
                results.append({
                    "title": r.get("title", "untitled"),
                    "snippet": r.get("body", ""),
                    "url": r.get("href", "")
                })
        return {"results": results}