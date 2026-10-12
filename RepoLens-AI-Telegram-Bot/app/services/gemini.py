import json
from google import genai
from google.genai import types
from app.config import settings
from app.logger import logger
from app.models.schemas import RepoData, AnalysisReport

class GeminiService:
    def __init__(self):
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model_name = settings.gemini_model

    async def analyze_repository(self, repo_data: RepoData, owner: str, repo: str) -> AnalysisReport | str:
        """
        Sends the repository structure and optional README to Gemini to generate an analysis.
        """
        tree_paths = [f"- {node.path} ({node.type})" for node in repo_data.tree]
        # To avoid massive prompts for huge repos, we could truncate the tree paths in a real scenario
        tree_str = "\n".join(tree_paths[:1000]) # Limit to 1000 items for MVP safety
        
        prompt = f"""
You are an expert Software Architect and Senior Full-Stack Engineer.
Please analyze the following GitHub repository: {owner}/{repo}.

REPOSITORY STRUCTURE:
{tree_str}
"""

        if repo_data.readme_content:
            readme_excerpt = repo_data.readme_content[:15000] # Limit README length to avoid context overflow
            prompt += f"\n\nREADME.md CONTENT:\n{readme_excerpt}"

        prompt += """

Based on the provided information, generate a detailed technical report.
Respond STRICTLY with a JSON object matching this schema, no markdown blocks, just raw JSON:
{
  "summary": "Project summary...",
  "technologies": ["tech1", "tech2"],
  "code_quality": "Code structure quality analysis...",
  "issues": ["issue1", "issue2"],
  "developer_level": "Junior | Mid | Senior",
  "suggestions": ["suggestion1", "suggestion2"]
}
"""

        try:
            # We can use the structured output format supported by Gemini SDK if we want,
            # or rely on JSON instruction. Given MVP, we rely on JSON instruction with text response
            # but using structured outputs via types.GenerateContentConfig is better.
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                ),
            )
            
            if response.text:
                data = json.loads(response.text)
                return AnalysisReport(**data)
            return "Failed to generate report (empty response)."
        except Exception as e:
            logger.error(f"Gemini API Error: {e}")
            return f"Error during AI analysis: {str(e)}"
