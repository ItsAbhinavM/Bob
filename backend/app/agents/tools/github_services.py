from github import Github, GithubException
import os
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

class GitHubService:
    """Service for GitHub API operations"""
    
    def __init__(self):
        self.token = os.getenv("GITHUB_TOKEN")
        self.default_repo = os.getenv("GITHUB_DEFAULT_REPO")
        
        if not self.token:
            print("⚠️  WARNING: GITHUB_TOKEN not configured")
            self.github = None
        else:
            self.github = Github(self.token)
    
    async def create_issue(
        self,
        title: str,
        body: Optional[str] = None,
        labels: Optional[List[str]] = None,
        repo_name: Optional[str] = None
    ) -> Dict:
        """
        Create a GitHub issue
        
        Args:
            title: Issue title
            body: Issue description (optional)
            labels: List of label names (optional)
            repo_name: Repository name like "owner/repo" (optional, uses default)
        
        Returns:
            Dict with issue details
        """
        try:
            if not self.github:
                return {
                    "success": False,
                    "error": "GitHub token not configured. Add GITHUB_TOKEN to .env"
                }
            
            # Use provided repo or default
            target_repo = repo_name or self.default_repo
            
            if not target_repo:
                return {
                    "success": False,
                    "error": "No repository specified. Set GITHUB_DEFAULT_REPO in .env or provide repo_name"
                }
            
            print(f"📝 Creating GitHub issue in {target_repo}")
            
            # Get repository
            repo = self.github.get_repo(target_repo)
            
            # Create issue
            issue = repo.create_issue(
                title=title,
                body=body or "",
                labels=labels or []
            )
            
            print(f"✅ GitHub issue created: #{issue.number}")
            
            return {
                "success": True,
                "issue_number": issue.number,
                "title": issue.title,
                "url": issue.html_url,
                "state": issue.state,
                "repo": target_repo
            }
            
        except GithubException as e:
            print(f"❌ GitHub API error: {str(e)}")
            return {
                "success": False,
                "error": f"GitHub API error: {e.data.get('message', str(e))}"
            }
        except Exception as e:
            print(f"❌ GitHub error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def list_issues(
        self,
        state: str = "open",
        limit: int = 10,
        repo_name: Optional[str] = None
    ) -> Dict:
        """
        List GitHub issues
        
        Args:
            state: Issue state - "open", "closed", or "all"
            limit: Maximum number of issues to return
            repo_name: Repository name (optional, uses default)
        
        Returns:
            Dict with list of issues
        """
        try:
            if not self.github:
                return {
                    "success": False,
                    "error": "GitHub token not configured"
                }
            
            target_repo = repo_name or self.default_repo
            
            if not target_repo:
                return {
                    "success": False,
                    "error": "No repository specified"
                }
            
            print(f"📋 Listing {state} issues from {target_repo}")
            
            repo = self.github.get_repo(target_repo)
            issues = repo.get_issues(state=state)
            
            # Get first N issues
            issue_list = []
            for issue in issues[:limit]:
                if not issue.pull_request:  # Skip PRs
                    issue_list.append({
                        "number": issue.number,
                        "title": issue.title,
                        "state": issue.state,
                        "url": issue.html_url,
                        "labels": [label.name for label in issue.labels],
                        "created_at": issue.created_at.strftime("%Y-%m-%d")
                    })
            
            print(f"✅ Found {len(issue_list)} issues")
            
            return {
                "success": True,
                "issues": issue_list,
                "count": len(issue_list),
                "repo": target_repo
            }
            
        except Exception as e:
            print(f"❌ GitHub list error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_my_repos(self, limit: int = 10) -> Dict:
        """
        Get user's repositories
        
        Returns:
            Dict with list of repositories
        """
        try:
            if not self.github:
                return {
                    "success": False,
                    "error": "GitHub token not configured"
                }
            
            print(f"📚 Fetching user repositories")
            
            user = self.github.get_user()
            repos = user.get_repos()
            
            repo_list = []
            for repo in repos[:limit]:
                repo_list.append({
                    "name": repo.full_name,
                    "description": repo.description or "No description",
                    "private": repo.private,
                    "url": repo.html_url,
                    "stars": repo.stargazers_count
                })
            
            print(f"✅ Found {len(repo_list)} repositories")
            
            return {
                "success": True,
                "repos": repo_list,
                "count": len(repo_list)
            }
            
        except Exception as e:
            print(f"❌ GitHub repos error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

# Global instance
github_service = GitHubService()