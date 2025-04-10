import requests
import csv
import re
from pathlib import Path
import logging
from datetime import datetime
import base64
import os
from dotenv import load_dotenv

load_dotenv()

# Constants
GITHUB_API_BASE_URL = "https://api.github.com"
GITHUB_API_VERSION = "2022-11-28"
README_URL = "https://raw.githubusercontent.com/punkpeye/awesome-mcp-servers/refs/heads/main/README.md"

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

def fetch_readme_content():
    """Fetch the README content from GitHub."""
    try:
        response = requests.get(README_URL)
        if response.status_code == 200:
            return response.text
        else:
            logging.error(f"Failed to fetch README content: {response.status_code}")
            return ""
    except Exception as e:
        logging.error(f"Error fetching README content: {e}")
        return ""

def extract_repo_info(text):
    """Extract repository information from text."""
    # Pattern to match repository entries
    # Format: - [owner/repo](url) emoji - description
    pattern = r'-\s+\[([a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+)\]\(([^)]+)\)\s+([^\s-]+(?:\s+[^\s-]+)*)\s+-\s+(.*?)(?=\n-|\n\n|$)'
    matches = re.findall(pattern, text, re.DOTALL)
    
    repos = []
    for match in matches:
        repo_path, url, emojis, description = match
        owner, repo = repo_path.split('/')
        repos.append({
            'owner': owner,
            'repo': repo,
            'description': description.strip(),
            'html_url': url,
            'emojis': emojis.strip()
        })
    
    return repos

def extract_tech_stack(text, emojis):
    """Extract tech stack information from text and emojis."""
    tech_stack = []
    
    # Programming Languages
    if re.search(r'🐍|python', text, re.IGNORECASE) or '🐍' in emojis:
        tech_stack.append("python")
    if re.search(r'📇|typescript|ts', text, re.IGNORECASE) or '📇' in emojis:
        tech_stack.append("typescript")
    if re.search(r'🏎️|go|golang', text, re.IGNORECASE) or '🏎️' in emojis:
        tech_stack.append("go")
    if re.search(r'🦀|rust', text, re.IGNORECASE) or '🦀' in emojis:
        tech_stack.append("rust")
    if re.search(r'☕|java|kotlin', text, re.IGNORECASE) or '☕' in emojis:
        tech_stack.append("java")
    if re.search(r'#️⃣|c#|dotnet', text, re.IGNORECASE) or '#️⃣' in emojis:
        tech_stack.append("csharp")
    
    # Deployment and Environment
    if re.search(r'☁️|cloud|aws|azure|gcp', text, re.IGNORECASE) or '☁️' in emojis:
        tech_stack.append("cloud")
    if re.search(r'🏠|local|desktop|cli', text, re.IGNORECASE) or '🏠' in emojis:
        tech_stack.append("local")
    if re.search(r'📟|embedded', text, re.IGNORECASE) or '📟' in emojis:
        tech_stack.append("embedded")
    
    # Operating Systems
    if '🍎' in emojis:
        tech_stack.append("macos")
    if '🪟' in emojis:
        tech_stack.append("windows")
    if '🐧' in emojis:
        tech_stack.append("linux")
    
    # Transport and Protocols
    if re.search(r'sse|server sent events', text, re.IGNORECASE):
        tech_stack.append("sse")
    if re.search(r'websocket|ws', text, re.IGNORECASE):
        tech_stack.append("websocket")
    if re.search(r'http|rest|api', text, re.IGNORECASE):
        tech_stack.append("http")
    
    return tech_stack

def assign_category(text, emojis):
    """Assign category based on text content and emojis."""
    # Check for category emojis
    if '🔗' in emojis:
        return "aggregator"
    if '🎨' in emojis:
        return "art_culture"
    if '📂' in emojis and 'browser' in text.lower():
        return "browser_automation"
    if '☁️' in emojis and 'cloud' in text.lower():
        return "cloud_platform"
    if '👨‍💻' in emojis or 'code' in text.lower():
        return "code_execution"
    if '🤖' in emojis or 'agent' in text.lower():
        return "coding_agent"
    if '🖥️' in emojis or 'cli' in text.lower():
        return "command_line"
    if '💬' in emojis or 'communication' in text.lower():
        return "communication"
    if '👤' in emojis or 'customer' in text.lower():
        return "customer_data"
    if '🗄️' in emojis or 'database' in text.lower():
        return "database"
    if '📊' in emojis and 'data' in text.lower():
        return "data_platform"
    if '🛠️' in emojis or 'developer' in text.lower():
        return "developer_tool"
    if '🧮' in emojis or 'data science' in text.lower():
        return "data_science"
    if '📟' in emojis or 'embedded' in text.lower():
        return "embedded_system"
    if '📂' in emojis and 'file' in text.lower():
        return "file_system"
    if '💰' in emojis or 'finance' in text.lower():
        return "finance"
    if '🎮' in emojis or 'gaming' in text.lower():
        return "gaming"
    if '🧠' in emojis or 'knowledge' in text.lower():
        return "knowledge"
    if '🗺️' in emojis or 'location' in text.lower():
        return "location"
    if '🎯' in emojis or 'marketing' in text.lower():
        return "marketing"
    if '📊' in emojis and 'monitoring' in text.lower():
        return "monitoring"
    if '🔎' in emojis or 'search' in text.lower():
        return "search"
    if '🔒' in emojis or 'security' in text.lower():
        return "security"
    if '🏃' in emojis or 'sports' in text.lower():
        return "sports"
    if '🎧' in emojis or 'support' in text.lower():
        return "support"
    if '🌎' in emojis or 'translation' in text.lower():
        return "translation"
    if '🚆' in emojis or 'travel' in text.lower():
        return "travel"
    if '🔄' in emojis or 'version' in text.lower():
        return "version_control"
    
    # Check for framework/utility categories
    if re.search(r'framework|sdk|kit|template', text, re.IGNORECASE):
        return "framework"
    if re.search(r'utility|tool|helper|gateway|proxy|bridge', text, re.IGNORECASE):
        return "utility"
    if re.search(r'client|chat|interface', text, re.IGNORECASE):
        return "client"
    if re.search(r'tutorial|guide|example|demo', text, re.IGNORECASE):
        return "tutorial"
    if re.search(r'community|discord|reddit', text, re.IGNORECASE):
        return "community"
    
    return "other"

def extract_keywords(text):
    """Extract keywords from text."""
    # Remove emojis and special characters
    clean_text = re.sub(r'[^\w\s]', ' ', text)
    # Split by whitespace and filter out common words
    words = clean_text.lower().split()
    common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'shall', 'should', 'may', 'might', 'must', 'can', 'could'}
    keywords = [word for word in words if word not in common_words and len(word) > 2]
    return list(set(keywords))

def main():
    # Fetch the README content from GitHub
    readme_content = fetch_readme_content()
    if not readme_content:
        logging.error("Failed to fetch README content")
        return
    
    # Extract repository information
    repos = extract_repo_info(readme_content)
    logging.info(f"Found {len(repos)} repositories")
    
    # Process each repository
    for repo in repos:
        # Extract additional information
        repo['techstack'] = extract_tech_stack(repo['description'], repo['emojis'])
        repo['category'] = assign_category(repo['description'], repo['emojis'])
        repo['keywords'] = extract_keywords(repo['description'])
        
        # Add stars and forks (placeholder values)
        repo['stars'] = 0
        repo['forks'] = 0
    
    # Save to CSV
    date_str = datetime.now().strftime("%Y%m%d")
    csv_filepath = Path("data") / f"awesome_list_{date_str}.csv"
    csv_filepath.parent.mkdir(parents=True, exist_ok=True)
    
    # Define fieldnames
    fieldnames = ['name', 'description', 'html_url', 'stars', 'forks', 'keywords', 'category', 'techstack', 'emojis']
    
    with open(csv_filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for repo in repos:
            # Prepare row data
            row = {
                'name': f"{repo['owner']}/{repo['repo']}",
                'description': repo['description'],
                'html_url': repo['html_url'],
                'stars': repo['stars'],
                'forks': repo['forks'],
                'keywords': ','.join(repo['keywords']),
                'category': repo['category'],
                'techstack': ','.join(repo['techstack']),
                'emojis': repo['emojis']
            }
            writer.writerow(row)
    
    logging.info(f"CSV file saved to: {csv_filepath}")

if __name__ == "__main__":
    main() 