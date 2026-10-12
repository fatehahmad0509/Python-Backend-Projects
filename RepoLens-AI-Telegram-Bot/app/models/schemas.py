from pydantic import BaseModel
from typing import List, Optional

class RepoAnalysisRequest(BaseModel):
    owner: str
    repo: str
    include_readme: bool

class GitHubTreeNode(BaseModel):
    path: str
    type: str

class RepoData(BaseModel):
    tree: List[GitHubTreeNode]
    readme_content: Optional[str] = None

class AnalysisReport(BaseModel):
    summary: str
    technologies: List[str]
    code_quality: str
    issues: List[str]
    developer_level: str
    suggestions: List[str]
