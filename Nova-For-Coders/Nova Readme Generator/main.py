import os
import sys
import json
from google import genai
from dotenv import load_dotenv

load_dotenv()

gemini_client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# File extensions to read content from
READABLE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".c", ".cpp", ".cs",
    ".go", ".rs", ".rb", ".php", ".swift", ".kt", ".html", ".css",
    ".json", ".toml", ".yaml", ".yml", ".env.example", ".sh", ".bat"
}

# Important config/meta files to always read if present
PRIORITY_FILES = {
    "requirements.txt", "package.json", "Pipfile", "pyproject.toml",
    "Cargo.toml", "go.mod", "pom.xml", "build.gradle", "Makefile",
    "Dockerfile", "docker-compose.yml", ".env.example", "setup.py",
    "setup.cfg", "tsconfig.json", "webpack.config.js"
}

# Directories to skip
SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv", "env",
    "dist", "build", ".next", ".nuxt", "coverage", ".pytest_cache",
    ".mypy_cache", ".tox", "eggs", ".eggs"
}

MAX_FILE_SIZE_KB = 30
MAX_FILES = 40
MAX_CONTENT_CHARS = 12000


def scan_project(root_path):
    structure = []
    collected_files = {}
    file_count = 0

    for dirpath, dirnames, filenames in os.walk(root_path):
        # Skip unwanted directories
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]

        rel_dir = os.path.relpath(dirpath, root_path)
        indent = "  " * (rel_dir.count(os.sep) if rel_dir != "." else 0)
        folder_name = os.path.basename(dirpath) if rel_dir != "." else os.path.basename(root_path)
        structure.append(f"{indent}📁 {folder_name}/")

        for filename in sorted(filenames):
            if filename.startswith(".") and filename not in {".env.example"}:
                continue

            file_indent = indent + "  "
            structure.append(f"{file_indent}📄 {filename}")

            if file_count >= MAX_FILES:
                continue

            filepath = os.path.join(dirpath, filename)
            ext = os.path.splitext(filename)[1].lower()
            is_priority = filename in PRIORITY_FILES

            if not (is_priority or ext in READABLE_EXTENSIONS):
                continue

            try:
                size_kb = os.path.getsize(filepath) / 1024
                if size_kb > MAX_FILE_SIZE_KB:
                    continue

                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                rel_path = os.path.relpath(filepath, root_path)
                collected_files[rel_path] = content
                file_count += 1

            except Exception:
                continue

    return "\n".join(structure), collected_files


def build_prompt(project_name, structure, files):
    files_block = ""
    total_chars = 0

    for path, content in files.items():
        if total_chars >= MAX_CONTENT_CHARS:
            break
        snippet = content[:1500]
        entry = f"\n--- {path} ---\n{snippet}\n"
        files_block += entry
        total_chars += len(entry)

    prompt = f"""You are a technical documentation expert. Your job is to generate a professional, clear, and well-structured README.md for a software project based on the provided project files and structure.

Project Name: {project_name}

Project File Structure:
{structure}

File Contents (partial):
{files_block}

Instructions:
- Write a complete README.md in English
- Use proper Markdown formatting
- Infer the project's purpose, tech stack, and features from the files
- Include these sections if applicable:
  - Project title and short description
  - Features
  - Tech stack / built with
  - Installation
  - Usage
  - Configuration (.env variables if detected)
  - Project structure (simplified)
  - License
- If you find a package.json or requirements.txt, list the main dependencies
- If you find a Dockerfile or docker-compose.yml, add a Docker usage section
- Be concise but informative
- Use emojis for section headers to make it visually appealing
- Do NOT hallucinate features that aren't evident from the code
- Return ONLY the raw Markdown content, no explanation, no preamble
"""
    return prompt


def generate_readme(project_path):
    project_path = os.path.abspath(project_path)

    if not os.path.isdir(project_path):
        print(f"❌ Directory not found: {project_path}")
        sys.exit(1)

    project_name = os.path.basename(project_path)

    print(f"🔍 Scanning project: {project_name}")
    structure, files = scan_project(project_path)

    print(f"📂 Found {len(files)} readable file(s)")
    print("🤖 Sending to Gemini AI for analysis...")

    prompt = build_prompt(project_name, structure, files)

    try:
        ai_response = gemini_client.models.generate_content(
            model="gemini-3.1-flash-lite",
            contents=prompt
        )

        readme_content = ai_response.text.strip()

        # Strip markdown code fences if model wraps output
        if readme_content.startswith("```"):
            lines = readme_content.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            readme_content = "\n".join(lines).strip()

    except Exception as e:
        print(f"❌ Gemini API Error: {e}")
        sys.exit(1)

    output_path = os.path.join(project_path, "README.md")

    # Warn if README already exists
    if os.path.exists(output_path):
        overwrite = input("⚠️  README.md already exists. Overwrite? (y/n): ").strip().lower()
        if overwrite != "y":
            print("⛔ Aborted.")
            sys.exit(0)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(readme_content)

    print(f"\n✅ README.md successfully generated!")
    print(f"📄 Saved to: {output_path}")
    print(f"\n--- Preview (first 500 chars) ---\n")
    print(readme_content[:500] + "...")


if __name__ == "__main__":
    print("🤖 Nova Readme Gen 🤖 | AI-Powered README Generator")
    print("=" * 50)

    if len(sys.argv) > 1:
        path = sys.argv[1]
    else:
        path = input("📁 Enter project folder path (or press Enter for current directory): ").strip()
        if not path:
            path = "."

    generate_readme(path)
    input("\nPress Enter to Close Terminal")