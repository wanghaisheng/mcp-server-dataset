import requests
import os
from dotenv import load_dotenv
import json
from pathlib import Path
import logging
import time
import argparse
import re
import csv
from datetime import datetime, timedelta
from typing import List, Dict, Any, TypedDict, Optional
import base64

load_dotenv()

# Constants
GITHUB_API_BASE_URL = "https://api.github.com/search/repositories"
GITHUB_API_VERSION = "2022-11-28"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
KEYWORDS_ENV = os.environ.get("KEYWORDS_ENV", "")
MIN_STARS = int(os.environ.get("MIN_STARS", "10"))
MIN_FORKS = int(os.environ.get("MIN_FORKS", "5"))


class RepoData(TypedDict):
    """Define the structure of a single repository's data"""

    name: str
    description: str
    html_url: str
    stars: int
    forks: int
    readme: str
    emojis: str
    keywords: List[str]
    category: str
    techstack: List[str]


def fetch_readme_content(owner: str, repo: str, token: str = None) -> str:
    """Fetches the README content from a GitHub repository.

    Args:
        owner (str): Repository owner
        repo (str): Repository name
        token (str, optional): GitHub token for authentication

    Returns:
        str: README content or empty string if not found
    """
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": GITHUB_API_VERSION,
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        # First try to get README.md
        url = f"https://api.github.com/repos/{owner}/{repo}/readme"
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            content = response.json().get("content", "")
            # Decode base64 content
            return base64.b64decode(content).decode("utf-8")
        
        # If README.md not found, try README.mdx
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/README.mdx"
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            content = response.json().get("content", "")
            return base64.b64decode(content).decode("utf-8")
            
        return ""
    except Exception as e:
        logging.error(f"Error fetching README for {owner}/{repo}: {e}")
        return ""


def search_github_repos(
    keywords: List[str], token: str = None, min_stars: int = 0, min_forks: int = 0
) -> Dict[str, List[RepoData]]:
    """
    Searches GitHub repositories for given keywords, filtering by stars and forks.

    Args:
        keywords (list): A list of keywords to search for.
        token (str, optional): A GitHub personal access token for higher rate limits. Defaults to None.
        min_stars (int, optional): Minimum number of stars a repo should have. Defaults to 0.
        min_forks (int, optional): Minimum number of forks a repo should have. Defaults to 0.

    Returns:
        dict: A dictionary where keys are keywords and values are lists of RepoData objects.
            Returns empty dict if there are no results for a keyword.

    Raises:
        requests.exceptions.RequestException: If there's an error during the API request.
    """
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": GITHUB_API_VERSION,
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    repo_data = {}
    for keyword in keywords:
        params = {"q": keyword}
        try:
            all_repo_data_for_keyword = []
            next_page_url = GITHUB_API_BASE_URL
            while next_page_url:
                logging.info(f"Searching for '{keyword}' at '{next_page_url}'")
                response = requests.get(next_page_url, headers=headers, params=params)
                response.raise_for_status()

                data = response.json()
                logging.debug(f"API response data: {data}")
                repo_data_for_keyword = []
                for item in data.get("items", []):
                    if (
                        item["stargazers_count"] >= min_stars
                        and item["forks_count"] >= min_forks
                    ):
                        # Extract owner and repo name from html_url
                        html_url = item["html_url"]
                        owner_repo = html_url.replace("https://github.com/", "").split("/")
                        owner = owner_repo[0]
                        repo = owner_repo[1]
                        
                        # Fetch README content
                        readme_content = fetch_readme_content(owner, repo, token)
                        
                        # Generate emojis based on repository characteristics
                        emojis = generate_emojis(item, readme_content)
                        
                        repo_data_for_keyword.append(
                            RepoData(
                                name=item["name"],
                                description=item["description"],
                                html_url=item["html_url"],
                                stars=item["stargazers_count"],
                                forks=item["forks_count"],
                                readme=readme_content,
                                emojis=emojis
                            )
                        )
                all_repo_data_for_keyword.extend(repo_data_for_keyword)
                
                # Handle Pagination
                if "Link" in response.headers:
                    link_header = response.headers["Link"]
                    next_links = [
                        link.split(";")[0].strip("<>")
                        for link in link_header.split(",")
                        if 'rel="next"' in link
                    ]
                    next_page_url = next_links[0] if next_links else None
                else:
                    next_page_url = None
                if next_page_url:
                    next_page_url=next_page_url.replace('<','')

            repo_data[keyword] = all_repo_data_for_keyword
        except requests.exceptions.RequestException as e:
            logging.error(f"Error searching for '{keyword}': {e}")
            repo_data[keyword] = []
            time.sleep(60)

    return repo_data


def generate_emojis(repo_data, readme_content):
    """Generate emojis based on repository characteristics."""
    emojis = []
    
    # Programming Languages
    if re.search(r'python|django|flask|fastapi', str(readme_content), re.IGNORECASE):
        emojis.append("🐍")
    if re.search(r'typescript|ts|javascript|js|node', str(readme_content), re.IGNORECASE):
        emojis.append("📇")
    if re.search(r'go|golang', str(readme_content), re.IGNORECASE):
        emojis.append("🏎️")
    if re.search(r'rust', str(readme_content), re.IGNORECASE):
        emojis.append("🦀")
    if re.search(r'java|kotlin|spring', str(readme_content), re.IGNORECASE):
        emojis.append("☕")
    if re.search(r'c#|dotnet|net', str(readme_content), re.IGNORECASE):
        emojis.append("#️⃣")
    
    # Deployment and Environment
    if re.search(r'cloud|aws|azure|gcp', str(readme_content), re.IGNORECASE):
        emojis.append("☁️")
    if re.search(r'local|desktop|cli', str(readme_content), re.IGNORECASE):
        emojis.append("🏠")
    if re.search(r'embedded', str(readme_content), re.IGNORECASE):
        emojis.append("📟")
    
    # Operating Systems
    if re.search(r'macos|mac os|apple', str(readme_content), re.IGNORECASE):
        emojis.append("🍎")
    if re.search(r'windows|win', str(readme_content), re.IGNORECASE):
        emojis.append("🪟")
    if re.search(r'linux|ubuntu|debian', str(readme_content), re.IGNORECASE):
        emojis.append("🐧")
    
    # Categories
    if re.search(r'framework|sdk|kit|template', str(readme_content), re.IGNORECASE):
        emojis.append("🛠️")
    if re.search(r'utility|tool|helper|gateway|proxy|bridge', str(readme_content), re.IGNORECASE):
        emojis.append("🔧")
    if re.search(r'client|chat|interface', str(readme_content), re.IGNORECASE):
        emojis.append("💬")
    if re.search(r'tutorial|guide|example|demo', str(readme_content), re.IGNORECASE):
        emojis.append("📚")
    if re.search(r'community|discord|reddit', str(readme_content), re.IGNORECASE):
        emojis.append("👥")
    if re.search(r'database|sql|nosql|postgres|mysql|mongodb', str(readme_content), re.IGNORECASE):
        emojis.append("🗄️")
    if re.search(r'api|rest|graphql|http', str(readme_content), re.IGNORECASE):
        emojis.append("🔌")
    if re.search(r'file|storage|s3|cloud', str(readme_content), re.IGNORECASE):
        emojis.append("📂")
    if re.search(r'ai|llm|gpt|claude|model', str(readme_content), re.IGNORECASE):
        emojis.append("🤖")
    if re.search(r'search|elastic|lucene', str(readme_content), re.IGNORECASE):
        emojis.append("🔎")
    
    return " ".join(emojis)


def load_existing_data(filepath: Path) -> Dict[str, Any]:
    """Loads existing data from a JSON file or returns an empty dict if the file does not exist.

    Args:
        filepath (str): The path to the JSON file.

    Returns:
        dict: The loaded data, or an empty dictionary if the file doesn't exist
        or there is a json exception.
    """
    if not filepath.exists():
        logging.info("Data file not found. Starting with empty results")
        return {}
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        logging.warning("Error decoding JSON file. Starting with empty results")
        return {}


def save_data(filepath: Path, data: Dict[str, Any]) -> None:
    """Saves data to a JSON file.

    Args:
        filepath (str): The path to the JSON file.
        data (dict): The data to save.
    """
    # ensure parent directory exists
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2, default=lambda o: o.__dict__)


def extract_keywords(description: str) -> List[str]:
    """Extract keywords from description string."""
    if not description:
        return []
    print("===DES", description)
    return (
        list(set(re.findall(r"\b[a-zA-Z0-9\-]+\b", description.lower())))
        if description
        else []
    )


def assign_category(keywords: List[str], emojis: str = "") -> str:
    """Categorizes item based on extracted keywords and emojis."""
    if not keywords and not emojis:
        return "general"
    
    # Check for category emojis
    if '🔗' in emojis:
        return "aggregator"
    if '🎨' in emojis:
        return "art_culture"
    if '📂' in emojis and any(word in keywords for word in ["browser", "automation"]):
        return "browser_automation"
    if '☁️' in emojis and any(word in keywords for word in ["cloud", "aws", "azure", "gcp"]):
        return "cloud_platform"
    if '👨‍💻' in emojis or any(word in keywords for word in ["code", "execution"]):
        return "code_execution"
    if '🤖' in emojis or any(word in keywords for word in ["agent", "coding"]):
        return "coding_agent"
    if '🖥️' in emojis or any(word in keywords for word in ["cli", "command", "line"]):
        return "command_line"
    if '💬' in emojis or any(word in keywords for word in ["communication", "chat"]):
        return "communication"
    if '👤' in emojis or any(word in keywords for word in ["customer", "data"]):
        return "customer_data"
    if '🗄️' in emojis or any(word in keywords for word in ["database", "sql", "nosql"]):
        return "database"
    if '📊' in emojis and any(word in keywords for word in ["data", "platform"]):
        return "data_platform"
    if '🛠️' in emojis or any(word in keywords for word in ["developer", "tool"]):
        return "developer_tool"
    if '🧮' in emojis or any(word in keywords for word in ["data", "science"]):
        return "data_science"
    if '📟' in emojis or any(word in keywords for word in ["embedded", "system"]):
        return "embedded_system"
    if '📂' in emojis and any(word in keywords for word in ["file", "system"]):
        return "file_system"
    if '💰' in emojis or any(word in keywords for word in ["finance", "money"]):
        return "finance"
    if '🎮' in emojis or any(word in keywords for word in ["gaming", "game"]):
        return "gaming"
    if '🧠' in emojis or any(word in keywords for word in ["knowledge", "brain"]):
        return "knowledge"
    if '🗺️' in emojis or any(word in keywords for word in ["location", "map"]):
        return "location"
    if '🎯' in emojis or any(word in keywords for word in ["marketing", "ad"]):
        return "marketing"
    if '📊' in emojis and any(word in keywords for word in ["monitoring", "metrics"]):
        return "monitoring"
    if '🔎' in emojis or any(word in keywords for word in ["search", "find"]):
        return "search"
    if '🔒' in emojis or any(word in keywords for word in ["security", "secure"]):
        return "security"
    if '🏃' in emojis or any(word in keywords for word in ["sports", "athlete"]):
        return "sports"
    if '🎧' in emojis or any(word in keywords for word in ["support", "help"]):
        return "support"
    if '🌎' in emojis or any(word in keywords for word in ["translation", "language"]):
        return "translation"
    if '🚆' in emojis or any(word in keywords for word in ["travel", "trip"]):
        return "travel"
    if '🔄' in emojis or any(word in keywords for word in ["version", "control"]):
        return "version_control"
    
    # MCP Server Categories
    if any(tech in keywords for tech in ["mcp", "model context protocol", "context protocol"]):
        return "mcp"
    if any(tech in keywords for tech in ["framework", "sdk", "kit", "template"]):
        return "framework"
    if any(tech in keywords for tech in ["utility", "tool", "helper", "gateway", "proxy", "bridge"]):
        return "utility"
    if any(tech in keywords for tech in ["client", "chat", "interface"]):
        return "client"
    if any(tech in keywords for tech in ["tutorial", "guide", "example", "demo"]):
        return "tutorial"
    if any(tech in keywords for tech in ["community", "discord", "reddit"]):
        return "community"
    
    # Integration Categories
    if any(tech in keywords for tech in ["database", "sql", "nosql", "postgres", "mysql", "mongodb"]):
        return "database"
    if any(tech in keywords for tech in ["api", "rest", "graphql", "http"]):
        return "api"
    if any(tech in keywords for tech in ["file", "storage", "s3", "cloud"]):
        return "storage"
    if any(tech in keywords for tech in ["ai", "llm", "gpt", "claude", "model"]):
        return "ai"
    if any(tech in keywords for tech in ["chat", "messaging", "discord", "slack", "telegram"]):
        return "messaging"
    if any(tech in keywords for tech in ["search", "elastic", "lucene"]):
        return "search"
    
    return "general"


def extract_techstack(keywords: List[str], all_keywords: List[str], emojis: str = "") -> List[str]:
    """Extracts techstack from the keywords, using all available keywords and emojis."""
    tech_stack = []
    
    # Programming Languages
    if any(tech in keywords for tech in ["python", "py", "django", "flask", "fastapi"]) or '🐍' in emojis:
        tech_stack.append("python")
    if any(tech in keywords for tech in ["typescript", "ts", "javascript", "js", "node"]) or '📇' in emojis:
        tech_stack.append("typescript")
    if any(tech in keywords for tech in ["go", "golang"]) or '🏎️' in emojis:
        tech_stack.append("go")
    if any(tech in keywords for tech in ["rust"]) or '🦀' in emojis:
        tech_stack.append("rust")
    if any(tech in keywords for tech in ["java", "kotlin", "spring"]) or '☕' in emojis:
        tech_stack.append("java")
    if any(tech in keywords for tech in ["csharp", "dotnet", "net"]) or '#️⃣' in emojis:
        tech_stack.append("csharp")
    
    # Frameworks and Libraries
    if any(tech in keywords for tech in ["fastmcp", "fastapi"]):
        tech_stack.append("fastmcp")
    if any(tech in keywords for tech in ["langchain", "chain"]):
        tech_stack.append("langchain")
    if any(tech in keywords for tech in ["spring", "springboot"]):
        tech_stack.append("spring")
    if any(tech in keywords for tech in ["quarkus"]):
        tech_stack.append("quarkus")
    
    # Transport and Protocols
    if any(tech in keywords for tech in ["sse", "server sent events"]):
        tech_stack.append("sse")
    if any(tech in keywords for tech in ["websocket", "ws"]):
        tech_stack.append("websocket")
    if any(tech in keywords for tech in ["http", "rest", "api"]):
        tech_stack.append("http")
    
    # Deployment and Environment
    if any(tech in keywords for tech in ["cloud", "aws", "azure", "gcp"]) or '☁️' in emojis:
        tech_stack.append("cloud")
    if any(tech in keywords for tech in ["local", "desktop", "cli"]) or '🏠' in emojis:
        tech_stack.append("local")
    if any(tech in keywords for tech in ["docker", "container"]):
        tech_stack.append("docker")
    if any(tech in keywords for tech in ["embedded"]) or '📟' in emojis:
        tech_stack.append("embedded")
    
    # Operating Systems
    if '🍎' in emojis:
        tech_stack.append("macos")
    if '🪟' in emojis:
        tech_stack.append("windows")
    if '🐧' in emojis:
        tech_stack.append("linux")
    
    return tech_stack


def save_data_as_csv(filepath: Path, data: Dict[str, Any]) -> None:
    """Saves data to a CSV file.

    Args:
        filepath (str): The path to the CSV file.
        data (dict): The data to save.
    """
    # ensure parent directory exists
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    # Extract all repositories from the "all" key
    repos = data.get("all", [])
    
    if not repos:
        logging.warning("No data to save to CSV")
        return
        
    # Define fieldnames - match the format used in extract_mcp_servers.py
    fieldnames = ['name', 'description', 'html_url', 'stars', 'forks', 'keywords', 'category', 'techstack', 'emojis']
    
    # Convert sets to strings for CSV compatibility
    for repo in repos:
        if "keywords" in repo:
            repo["keywords"] = ",".join(repo["keywords"])
        if "techstack" in repo:
            repo["techstack"] = ",".join(repo["techstack"])
    
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(repos)
    
    logging.info(f"CSV results saved to: {filepath}")


def get_previous_day_file() -> Optional[Path]:
    """
    Get the path to the previous day's CSV file.
    
    Returns:
        Optional[Path]: Path to the previous day's CSV file or None if not found
    """
    yesterday = datetime.now() - timedelta(days=1)
    yesterday_str = yesterday.strftime('%Y%m%d')
    file_path = Path('data') / f'mcp_servers_{yesterday_str}.csv'
    
    if file_path.exists():
        return file_path
    return None


def read_previous_data(file_path: Path) -> Dict[str, RepoData]:
    """
    Read data from the previous day's CSV file.
    
    Args:
        file_path: Path to the CSV file
        
    Returns:
        Dict[str, RepoData]: Dictionary of repositories by name
    """
    repos = {}
    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Convert string fields back to lists
                if 'keywords' in row and row['keywords']:
                    row['keywords'] = row['keywords'].split(',')
                if 'techstack' in row and row['techstack']:
                    row['techstack'] = row['techstack'].split(',')
                repos[row['name']] = row
    except Exception as e:
        print(f"Error reading previous data: {e}")
    
    return repos


def merge_repos(old_repos: Dict[str, RepoData], new_repos: Dict[str, List[RepoData]]) -> Dict[str, RepoData]:
    """
    Merge old and new repository data, updating existing entries and adding new ones.
    
    Args:
        old_repos: Dictionary of old repositories by name
        new_repos: Dictionary of new repositories by keyword
        
    Returns:
        Dict[str, RepoData]: Merged dictionary of repositories by name
    """
    merged_repos = old_repos.copy()
    
    # Process all new repositories
    for keyword, repos in new_repos.items():
        for repo in repos:
            name = repo["name"]
            
            # Generate emojis
            repo["emojis"] = generate_emojis(repo)
            
            # Extract additional keywords
            additional_keywords = extract_keywords(repo["description"])
            repo["keywords"] = list(set(repo["keywords"] + additional_keywords))
            
            # Assign category
            repo["category"] = assign_category(repo["keywords"], repo["emojis"])
            
            # Extract tech stack
            repo["techstack"] = extract_techstack(repo["keywords"], KEYWORDS_ENV, repo["emojis"])
            
            # Update or add to merged repos
            if name in merged_repos:
                # Update existing repo
                old_repo = merged_repos[name]
                
                # Merge keywords
                old_repo["keywords"] = list(set(old_repo["keywords"] + repo["keywords"]))
                
                # Update stars and forks if new values are higher
                old_repo["stars"] = max(old_repo["stars"], repo["stars"])
                old_repo["forks"] = max(old_repo["forks"], repo["forks"])
                
                # Update emojis (combine)
                old_repo["emojis"] = "".join(set(old_repo["emojis"] + repo["emojis"]))
                
                # Update category if more specific
                if old_repo["category"] == "Other" and repo["category"] != "Other":
                    old_repo["category"] = repo["category"]
                
                # Merge tech stack
                old_repo["techstack"] = list(set(old_repo["techstack"] + repo["techstack"]))
                
                merged_repos[name] = old_repo
            else:
                # Add new repo
                merged_repos[name] = repo
    
    return merged_repos


def save_to_csv(repos: Dict[str, RepoData], output_dir: str = 'data') -> str:
    """
    Save repository data to a CSV file.
    
    Args:
        repos: Dictionary of repositories by name
        output_dir: Directory to save the CSV file
        
    Returns:
        Path to the saved CSV file
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate filename with current date
    date_str = datetime.now().strftime('%Y%m%d')
    output_file = os.path.join(output_dir, f'mcp_servers_{date_str}.csv')
    
    # Define fieldnames - match the format used in extract_mcp_servers.py
    fieldnames = ['name', 'description', 'html_url', 'stars', 'forks', 'keywords', 'category', 'techstack', 'emojis']
    
    # Write to CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for repo in repos.values():
            # Convert lists to comma-separated strings for CSV
            row = repo.copy()
            row['keywords'] = ', '.join(row['keywords'])
            row['techstack'] = ', '.join(row['techstack'])
            writer.writerow(row)
    
    return output_file


def main():
    # Parse keywords from environment variable
    keywords = [k.strip() for k in KEYWORDS_ENV.split(',') if k.strip()]
    
    # 1. Get previous day's data
    prev_file = get_previous_day_file()
    old_repos = {}
    if prev_file:
        print(f"Reading previous data from {prev_file}")
        old_repos = read_previous_data(prev_file)
    
    # 2. Search GitHub for new repositories
    print(f"Searching GitHub for {len(keywords)} keywords")
    new_repos = search_github_repos(keywords, GITHUB_TOKEN, MIN_STARS, MIN_FORKS)
    
    # 3. Merge old and new data
    print("Merging old and new data")
    merged_repos = merge_repos(old_repos, new_repos)
    
    # 4. Save to CSV
    output_file = save_to_csv(merged_repos)
    print(f"Total {len(merged_repos)} MCP servers saved to {output_file}")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    # Setup argument parser
    parser = argparse.ArgumentParser(
        description="Search and merge GitHub repository data"
    )
    args = parser.parse_args()

    # Load Configuration
    keywords_str = os.getenv("KEYWORDS_ENV")
    if keywords_str:
        keywords_to_search = [
            keyword.strip() for keyword in keywords_str.split(",") if keyword.strip()
        ]
    else:
        # Default keywords for MCP server repositories
        keywords_to_search = [
            "model context protocol server",
            "mcp server",
            "mcp framework",
            "mcp sdk",
            "mcp template",
            "mcp utility",
            "mcp gateway",
            "mcp proxy",
            "mcp client",
            "mcp tutorial",
            "mcp example",
            "mcp database",
            "mcp api",
            "mcp storage",
            "mcp ai",
            "mcp chat",
            "mcp search"
        ]
        logging.info("Using default MCP server keywords")

    github_token = os.getenv("GITHUB_TOKEN")
    try:
        min_stars_filter = int(os.getenv("MIN_STARS", 10))
        min_forks_filter = int(os.getenv("MIN_FORKS", 10))
    except ValueError as e:
        logging.error(f"Error parsing MIN_STARS or MIN_FORKS env variables: {e}")
        exit(1)
    
    # Use default output path since we're now using date-based CSV files
    output_file = Path("results/data.json")

    main()
