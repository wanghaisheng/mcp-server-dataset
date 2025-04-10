import re
import csv
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

def extract_mcp_servers(readme_path: str) -> List[Dict[str, Any]]:
    """
    Extract MCP server information from the README file.
    
    Args:
        readme_path: Path to the README file
        
    Returns:
        List of dictionaries containing MCP server information
    """
    with open(readme_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract sections
    sections = re.split(r'##\s+', content)[1:]  # Skip the first element (before first section)
    
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
                'url': url,
                'description': clean_description,
                'category': current_category,
                'emojis': emojis_str,
                'tech_stack': ', '.join(tech_stack),
                'keywords': ', '.join(keywords)
            }
            
            servers.append(server_info)
    
    return servers

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
    
    # Define fieldnames
    fieldnames = ['name', 'url', 'description', 'category', 'emojis', 'tech_stack', 'keywords']
    
    # Write to CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(servers)
    
    return output_file

def main():
    readme_path = 'mcp-server-README-example.md'
    servers = extract_mcp_servers(readme_path)
    output_file = save_to_csv(servers)
    print(f"Extracted {len(servers)} MCP servers to {output_file}")

if __name__ == "__main__":
    main() 