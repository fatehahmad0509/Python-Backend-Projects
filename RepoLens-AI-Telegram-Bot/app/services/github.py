import httpx
import base64
from typing import Optional
from app.config import settings
from app.logger import logger
from app.models.schemas import RepoData, GitHubTreeNode

class GitHubService:
    BASE_URL = "https://api.github.com"

    def __init__(self):
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "RepoLens-Bot"
        }
        if settings.github_token:
            self.headers["Authorization"] = f"token {settings.github_token}"

    async def fetch_repository_data(self, owner: str, repo: str, include_readme: bool) -> Optional[RepoData]:
        """
        Fetches the repository tree (recursive) and optionally the README.md content.
        """
        try:
            async with httpx.AsyncClient(headers=self.headers, timeout=10.0, follow_redirects=True) as client:
                # Get the default branch first
                repo_url = f"{self.BASE_URL}/repos/{owner}/{repo}"
                repo_response = await client.get(repo_url)
                
                if repo_response.status_code != 200:
                    logger.error(f"Failed to fetch repository info: {repo_response.status_code}")
                    return None
                    
                default_branch = repo_response.json().get("default_branch", "main")
                
                # Fetch tree
                tree_url = f"{self.BASE_URL}/repos/{owner}/{repo}/git/trees/{default_branch}?recursive=1"
                tree_response = await client.get(tree_url)
                
                if tree_response.status_code != 200:
                    logger.error(f"Failed to fetch repository tree: {tree_response.status_code}")
                    return None
                
                tree_data = tree_response.json().get("tree", [])
                
                # Filter out irrelevant files (e.g. limit to code files, exclude large binary files if needed)
                # For MVP, we will include path and type
                nodes = []
                for item in tree_data:
                    # Ignore `.git` contents, maybe some binary extensions
                    nodes.append(GitHubTreeNode(path=item["path"], type=item["type"]))

                # Fetch README if requested
                readme_content = None
                if include_readme:
                    readme_url = f"{self.BASE_URL}/repos/{owner}/{repo}/readme"
                    readme_response = await client.get(readme_url)
                    
                    if readme_response.status_code == 200:
                        content_b64 = readme_response.json().get("content", "")
                        try:
                            readme_content = base64.b64decode(content_b64).decode('utf-8')
                        except Exception as e:
                            logger.error(f"Failed to decode README: {e}")
                            readme_content = None
                            
                return RepoData(tree=nodes, readme_content=readme_content)

        except Exception as e:
            logger.error(f"Exception in fetching github data: {e}")
            return None
