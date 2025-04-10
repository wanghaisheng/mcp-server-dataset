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
from datetime import datetime
from typing import List, Dict, Any, TypedDict
import base64

load_dotenv()

# Constants
GITHUB_API_BASE_URL = "https://api.github.com/search/repositories"
GITHUB_API_VERSION = "2022-11-28"


class RepoData(TypedDict):
    """Define the structure of a single repository's data"""

    name: str
    description: str
    html_url: str
    stars: int
    forks: int
    readme: str


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
                        
                        repo_data_for_keyword.append(
                            RepoData(
                                name=item["name"],
                                description=item["description"],
                                html_url=item["html_url"],
                                stars=item["stargazers_count"],
                                forks=item["forks_count"],
                                readme=readme_content
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


def assign_category(keywords: List[str]) -> str:
    """Categorizes item based on extracted keywords."""
    if not keywords:
        return "general"
    
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


def extract_techstack(keywords: List[str], all_keywords: List[str]) -> List[str]:
    """Extracts techstack from the keywords, using all available keywords."""
    tech_stack = []
    
    # Programming Languages
    if any(tech in keywords for tech in ["python", "py", "django", "flask", "fastapi"]):
        tech_stack.append("python")
    if any(tech in keywords for tech in ["typescript", "ts", "javascript", "js", "node"]):
        tech_stack.append("typescript")
    if any(tech in keywords for tech in ["go", "golang"]):
        tech_stack.append("go")
    if any(tech in keywords for tech in ["rust"]):
        tech_stack.append("rust")
    if any(tech in keywords for tech in ["java", "kotlin", "spring"]):
        tech_stack.append("java")
    if any(tech in keywords for tech in ["csharp", "dotnet", "net"]):
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
    if any(tech in keywords for tech in ["cloud", "aws", "azure", "gcp"]):
        tech_stack.append("cloud")
    if any(tech in keywords for tech in ["local", "desktop", "cli"]):
        tech_stack.append("local")
    if any(tech in keywords for tech in ["docker", "container"]):
        tech_stack.append("docker")
    
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
        
    # Get all possible fields from the data
    fieldnames = set()
    for repo in repos:
        fieldnames.update(repo.keys())
    
    # Convert sets to strings for CSV compatibility
    for repo in repos:
        if "keywords" in repo:
            repo["keywords"] = ",".join(repo["keywords"])
        if "techstack" in repo:
            repo["techstack"] = ",".join(repo["techstack"])
    
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=sorted(fieldnames))
        writer.writeheader()
        writer.writerows(repos)
    
    logging.info(f"CSV results saved to: {filepath}")


def merge_and_save_results(
    keywords_to_search: List[str],
    token: str,
    output_filepath: Path,
    min_stars: int = 0,
    min_forks: int = 0,
) -> None:
    """Searches, loads existing data, merges, and saves new data.

    Args:
       keywords (list): A list of keywords to search for.
       token (str, optional): A GitHub personal access token for higher rate limits. Defaults to None.
       output_filepath (str) : Path to save the results to
       min_stars (int, optional): Minimum number of stars a repo should have. Defaults to 0.
       min_forks (int, optional): Minimum number of forks a repo should have. Defaults to 0.
    """
    # 1. search github for keywords, with filter criteria
    new_results = search_github_repos(keywords_to_search, token, min_stars, min_forks)

    # 2. Load existing data (or initialize an empty dict)
    existing_data = load_existing_data(output_filepath)

    # 3.  Merge the data, make them unique and add keywords as properties
    merged_data = {"all": []}
    for keyword, new_repos in new_results.items():
        if not new_repos:
            logging.warning(f"No results for {keyword}. skipping...")
            continue  # Skip if there are no results
        for repo in new_repos:
            repo["keywords"] = extract_keywords(repo["description"])
            repo["category"] = assign_category(repo["keywords"])
            repo["techstack"] = extract_techstack(repo["keywords"], keywords_to_search)
            merged_data["all"].append(repo)

    for domain, existing_info in existing_data.items():
        if domain not in merged_data:
            merged_data[domain] = []
        if isinstance(existing_info, dict):
            for item in existing_info.get("description", []):
                keywords = extract_keywords(item)
                merged_data["all"].append(
                    {
                        "name": domain,
                        "description": item,
                        "keywords": keywords,
                        "category": assign_category(keywords),
                        "techstack": extract_techstack(keywords, keywords_to_search),
                        "domain_strength": existing_info.get("domain_strength"),
                        "est_mo_clicks": existing_info.get("est_mo_clicks", 0),
                        "google_description": existing_info.get("google_description"),
                    }
                )
    
    # 4. save to CSV file with date in filename
    date_str = datetime.now().strftime("%Y%m%d")
    csv_filepath = Path("data") / f"{date_str}.csv"
    save_data_as_csv(csv_filepath, merged_data)


def validate_config(min_stars: int, min_forks: int):
    if not isinstance(min_stars, int) or min_stars < 0:
        raise ValueError("min_stars must be a non-negative integer")
    if not isinstance(min_forks, int) or min_forks < 0:
        raise ValueError("min_forks must be a non-negative integer")


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

    validate_config(min_stars_filter, min_forks_filter)

    merge_and_save_results(
        keywords_to_search,
        github_token,
        output_file,
        min_stars_filter,
        min_forks_filter,
    )
