import httpx
from typing import Dict, List
import html

class StackOverflowService:
    """Service for searching Stack Overflow"""
    
    def __init__(self):
        self.base_url = "https://api.stackexchange.com/2.3"
    
    async def search_question(self, query: str, num_results: int = 3) -> Dict:
        """
        Search Stack Overflow for a question
        
        Args:
            query: Search query
            num_results: Number of results to return (default 3)
        
        Returns:
            Dict with questions and top answers
        """
        try:
            async with httpx.AsyncClient() as client:
                # Search for questions
                params = {
                    "order": "desc",
                    "sort": "votes",
                    "intitle": query,
                    "site": "stackoverflow",
                    "filter": "withbody"
                }
                
                response = await client.get(
                    f"{self.base_url}/search/advanced",
                    params=params,
                    timeout=10
                )
                response.raise_for_status()
                
                data = response.json()
                
                if not data.get("items"):
                    return {
                        "success": False,
                        "error": f"No Stack Overflow results found for '{query}'"
                    }
                
                # Get top results
                results = []
                for item in data["items"][:num_results]:
                    question_id = item["question_id"]
                    
                    # Get answers for this question
                    answer_response = await client.get(
                        f"{self.base_url}/questions/{question_id}/answers",
                        params={
                            "order": "desc",
                            "sort": "votes",
                            "site": "stackoverflow",
                            "filter": "withbody"
                        },
                        timeout=10
                    )
                    
                    answers_data = answer_response.json()
                    
                    # Get top answer
                    top_answer = None
                    if answers_data.get("items"):
                        answer_item = answers_data["items"][0]
                        # Clean HTML from answer body
                        answer_body = self._clean_html(answer_item.get("body", ""))
                        top_answer = {
                            "body": answer_body[:500],  # Limit length
                            "score": answer_item.get("score", 0),
                            "is_accepted": answer_item.get("is_accepted", False)
                        }
                    
                    results.append({
                        "title": item.get("title", ""),
                        "link": item.get("link", ""),
                        "score": item.get("score", 0),
                        "answer_count": item.get("answer_count", 0),
                        "top_answer": top_answer
                    })
                
                return {
                    "success": True,
                    "query": query,
                    "results": results,
                    "count": len(results)
                }
                
        except httpx.TimeoutException:
            return {
                "success": False,
                "error": "Stack Overflow search timed out"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Stack Overflow search failed: {str(e)}"
            }
    
    def _clean_html(self, html_text: str) -> str:
        """Remove HTML tags and decode entities"""
        # Remove HTML tags
        import re
        text = re.sub(r'<[^>]+>', '', html_text)
        # Decode HTML entities
        text = html.unescape(text)
        # Remove extra whitespace
        text = ' '.join(text.split())
        return text

# Global instance
stackoverflow_service = StackOverflowService()