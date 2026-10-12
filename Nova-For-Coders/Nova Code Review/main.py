import os
import sys
from google import genai
from dotenv import load_dotenv

load_dotenv()

gemini_client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

READABLE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".c", ".cpp", ".cs",
    ".go", ".rs", ".rb", ".php", ".swift", ".kt", ".html", ".css",
    ".json", ".toml", ".yaml", ".yml", ".sh", ".bat"
}

SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv", "env",
    "dist", "build", ".next", ".nuxt", "coverage", ".pytest_cache",
    ".mypy_cache", ".tox", "eggs", ".eggs"
}

MAX_FILE_SIZE_KB = 100
MAX_FILES = 40
MAX_CONTENT_CHARS = 150000


def scan_project(root_path):
    structure = []
    collected_files = {}
    file_count = 0

    for dirpath, dirnames, filenames in os.walk(root_path):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]

        rel_dir = os.path.relpath(dirpath, root_path)
        indent = "  " * (rel_dir.count(os.sep) if rel_dir != "." else 0)
        folder_name = os.path.basename(dirpath) if rel_dir != "." else os.path.basename(root_path)
        structure.append(f"{indent}📁 {folder_name}/")

        for filename in sorted(filenames):
            if filename.startswith("."):
                continue

            file_indent = indent + "  "
            structure.append(f"{file_indent}📄 {filename}")

            if file_count >= MAX_FILES:
                continue

            filepath = os.path.join(dirpath, filename)
            ext = os.path.splitext(filename)[1].lower()

            if ext not in READABLE_EXTENSIONS:
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
        snippet = content[:2000]
        entry = f"\n--- {path} ---\n{snippet}\n"
        files_block += entry
        total_chars += len(entry)

    prompt = f"""You are a senior software engineer conducting a thorough code review. Analyze the provided project files and generate a detailed CODE_REVIEW.md report.

Project Name: {project_name}

Project File Structure:
{structure}

File Contents:
{files_block}

Instructions:
- Write a complete code review report in English using proper Markdown
- Be specific — reference actual file names, function names, and line patterns you observe
- Do NOT hallucinate issues that aren't evident from the code
- Use phrases like "appears to", "likely", "consider" where uncertain
- Score the project out of 100

Include these sections:

# 🔍 Code Review — {project_name}

## ⭐ Overall Score
X/100 — with a one-line verdict

## 📋 Summary
Brief overview of what the project does and general code quality impression

## ✅ Strengths
What is done well (be specific)

## ❌ Issues
List issues by severity:
- 🔴 Critical — bugs, security holes, data loss risks
- 🟡 Medium — bad practices, performance issues, code smells
- 🟢 Minor — style, naming, small improvements

For each issue: what it is, which file/area, why it matters, how to fix it

## 💡 Recommendations
Concrete, actionable suggestions to improve the codebase

## 📊 Category Scores
| Category | Score | Notes |
|---|---|---|
| Code Quality | X/10 | ... |
| Security | X/10 | ... |
| Performance | X/10 | ... |
| Readability | X/10 | ... |
| Error Handling | X/10 | ... |
| Structure | X/10 | ... |

Return ONLY the raw Markdown content, no explanation, no preamble.
"""
    return prompt


def generate_code_review(project_path):
    project_path = os.path.abspath(project_path)

    if not os.path.isdir(project_path):
        print(f"❌ Directory not found: {project_path}")
        sys.exit(1)

    project_name = os.path.basename(project_path)

    print(f"🔍 Scanning project: {project_name}")
    structure, files = scan_project(project_path)

    print(f"📂 Found {len(files)} readable file(s)")
    print("🤖 Sending to Gemini AI for code review...")

    prompt = build_prompt(project_name, structure, files)

    try:
        ai_response = gemini_client.models.generate_content(
            model="gemini-3.1-flash-lite",
            contents=prompt
        )

        review_content = ai_response.text.strip()

        if review_content.startswith("```"):
            lines = review_content.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            review_content = "\n".join(lines).strip()

    except Exception as e:
        print(f"❌ Gemini API Error: {e}")
        sys.exit(1)

    output_path = os.path.join(project_path, "CODE_REVIEW.md")

    if os.path.exists(output_path):
        overwrite = input("⚠️  CODE_REVIEW.md already exists. Overwrite? (y/n): ").strip().lower()
        if overwrite != "y":
            print("⛔ Aborted.")
            sys.exit(0)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(review_content)

    print(f"\n✅ CODE_REVIEW.md successfully generated!")
    print(f"📄 Saved to: {output_path}")
    print(f"\n--- Preview (first 500 chars) ---\n")
    print(review_content[:500] + "...")


if __name__ == "__main__":
    print("🤖 Nova Code Review 🤖 | AI-Powered Code Review Generator")
    print("=" * 55)

    if len(sys.argv) > 1:
        path = sys.argv[1]
    else:
        path = input("📁 Enter project folder path (or press Enter for current directory): ").strip()
        if not path:
            path = "."

    generate_code_review(path)
    input("\nPress Enter to Close Terminal")