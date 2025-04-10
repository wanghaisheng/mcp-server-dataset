import re
import csv
import os
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path

# Constants
README_URL = "https://raw.githubusercontent.com/punkpeye/awesome-mcp-servers/refs/heads/main/README.md"

def fetch_readme_from_url() -> str:
    """
    Fetch README content from the GitHub URL.
    
    Returns:
        str: README content
    """
    try:
        response = requests.get(README_URL)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error fetching README from URL: {e}")
        # Fallback to local file if URL fetch fails
        return read_local_readme('mcp-server-README-example.md')

def read_local_readme(readme_path: str) -> str:
    """
    Read README content from local file.
    
    Args:
        readme_path: Path to the README file
        
    Returns:
        str: README content
    """
    try:
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading local README: {e}")
        return ""

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

def read_previous_data(file_path: Path) -> List[Dict[str, Any]]:
    """
    Read data from the previous day's CSV file.
    
    Args:
        file_path: Path to the CSV file
        
    Returns:
        List[Dict[str, Any]]: List of dictionaries containing MCP server information
    """
    servers = []
    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Convert string fields back to lists
                if 'keywords' in row and row['keywords']:
                    row['keywords'] = row['keywords'].split(',')
                if 'techstack' in row and row['techstack']:
                    row['techstack'] = row['techstack'].split(',')
                servers.append(row)
    except Exception as e:
        print(f"Error reading previous data: {e}")
    
    return servers

def extract_mcp_servers(readme_content: str) -> List[Dict[str, Any]]:
    """
    Extract MCP server information from the README content.
    
    Args:
        readme_content: README content
        
    Returns:
        List of dictionaries containing MCP server information
    """
    # Extract sections
    sections = re.split(r'##\s+', readme_content)[1:]  # Skip the first element (before first section)
    
    servers = []
    current_category = ""
    
    for section in sections:
        if not section.strip():
            continue
            
        # Extract section title
        title_match = re.match(r'^([^\n]+)', section)
        if not title_match:
            continue
            
        title = title_match.group(1).strip()
        
        # Skip non-server sections
        if title in ["What is MCP?", "Clients", "Tutorials", "Community", "Legend", "Frameworks", "Utilities", "Tips and Tricks"]:
            continue
            
        # Extract category from title
        category_match = re.match(r'^([^<]+)', title)
        if category_match:
            current_category = category_match.group(1).strip()
        
        # Extract server entries
        server_entries = re.findall(r'- \[([^\]]+)\]\(([^)]+)\)\s*(.*?)(?=\n-|\Z)', section, re.DOTALL)
        
        for name, url, description in server_entries:
            # Extract emojis from description
            emojis = re.findall(r'[^\w\s]', description)
            emojis_str = ''.join(emojis)
            
            # Clean description
            clean_description = re.sub(r'[^\w\s]', '', description).strip()
            
            # Extract tech stack from emojis
            tech_stack = []
            if '🐍' in emojis_str:
                tech_stack.append('Python')
            if '📇' in emojis_str:
                tech_stack.append('TypeScript')
            if '🏎️' in emojis_str:
                tech_stack.append('Go')
            if '🦀' in emojis_str:
                tech_stack.append('Rust')
            if '☕' in emojis_str:
                tech_stack.append('Java')
            if '#️⃣' in emojis_str:
                tech_stack.append('C#')
            if '🍎' in emojis_str:
                tech_stack.append('iOS')
            if '🪟' in emojis_str:
                tech_stack.append('Windows')
            if '🐧' in emojis_str:
                tech_stack.append('Linux')
            if '☁️' in emojis_str:
                tech_stack.append('Cloud')
            if '🏠' in emojis_str:
                tech_stack.append('Local')
            if '🎖️' in emojis_str:
                tech_stack.append('Official')
            
            # Extract keywords from description
            keywords = []
            if 'database' in description.lower():
                keywords.append('database')
            if 'api' in description.lower():
                keywords.append('api')
            if 'search' in description.lower():
                keywords.append('search')
            if 'monitoring' in description.lower():
                keywords.append('monitoring')
            if 'security' in description.lower():
                keywords.append('security')
            if 'file' in description.lower():
                keywords.append('file')
            if 'git' in description.lower():
                keywords.append('git')
            if 'ai' in description.lower() or 'llm' in description.lower():
                keywords.append('ai')
            
            server_info = {
                'name': name,
                'description': clean_description,
                'html_url': url,
                'stars': 0,  # Default values since we don't have this info from README
                'forks': 0,  # Default values since we don't have this info from README
                'category': current_category,
                'techstack': ', '.join(tech_stack),
                'keywords': ', '.join(keywords),
                'emojis': emojis_str
            }
            
            servers.append(server_info)
    
    return servers

def merge_servers(old_servers: List[Dict[str, Any]], new_servers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Merge old and new server data, updating existing entries and adding new ones.
    
    Args:
        old_servers: List of dictionaries containing old MCP server information
        new_servers: List of dictionaries containing new MCP server information
        
    Returns:
        List[Dict[str, Any]]: Merged list of dictionaries containing MCP server information
    """
    # Create a dictionary of old servers by name for easy lookup
    old_servers_dict = {server['name']: server for server in old_servers}
    
    # Update or add new servers
    for new_server in new_servers:
        name = new_server['name']
        if name in old_servers_dict:
            # Update existing server with new data
            old_servers_dict[name].update(new_server)
        else:
            # Add new server
            old_servers_dict[name] = new_server
    
    # Convert back to list
    return list(old_servers_dict.values())

def save_to_csv(servers: List[Dict[str, Any]], output_dir: str = 'data') -> str:
    """
    Save MCP server information to a CSV file.
    
    Args:
        servers: List of dictionaries containing MCP server information
        output_dir: Directory to save the CSV file
        
    Returns:
        Path to the saved CSV file
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate filename with current date
    date_str = datetime.now().strftime('%Y%m%d')
    output_file = os.path.join(output_dir, f'mcp_servers_{date_str}.csv')
    
    # Define fieldnames - match the format used in daily.py
    fieldnames = ['name', 'description', 'html_url', 'stars', 'forks', 'keywords', 'category', 'techstack', 'emojis']
    
    # Write to CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(servers)
    
    return output_file

def main():
    # 1. Get previous day's data
    prev_file = get_previous_day_file()
    old_servers = []
    if prev_file:
        print(f"Reading previous data from {prev_file}")
        old_servers = read_previous_data(prev_file)
    
    # 2. Fetch README content
    print("Fetching README content from URL")
    readme_content = fetch_readme_from_url()
    
    # 3. Extract new server data
    print("Extracting MCP server information")
    new_servers = extract_mcp_servers(readme_content)
    
    # 4. Merge old and new data
    print("Merging old and new data")
    merged_servers = merge_servers(old_servers, new_servers)
    
    # 5. Save to CSV
    output_file = save_to_csv(merged_servers)
    print(f"Extracted {len(new_servers)} new MCP servers, merged with {len(old_servers)} existing servers")
    print(f"Total {len(merged_servers)} MCP servers saved to {output_file}")

if __name__ == "__main__":
    main() 