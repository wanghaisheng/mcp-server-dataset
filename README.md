# MCP Server Dataset Builder

A comprehensive tool for building and maintaining a dataset of Model Context Protocol (MCP) servers. This tool automatically collects, categorizes, and updates information about MCP servers from multiple sources.

## Overview

The MCP Server Dataset Builder is designed to:

1. Extract MCP server information from the [awesome-mcp-servers](https://github.com/punkpeye/awesome-mcp-servers) repository
2. Search GitHub for additional MCP server repositories
3. Merge and deduplicate data from both sources
4. Generate a daily CSV file with comprehensive information about each server

## Features

- **Dual Data Sources**: Combines data from curated lists and GitHub search
- **Automatic Categorization**: Assigns categories based on repository content
- **Tech Stack Detection**: Identifies programming languages and frameworks
- **Emoji Tagging**: Adds visual indicators for quick identification
- **Daily Updates**: Automatically runs to keep the dataset current
- **Data Persistence**: Maintains historical data while adding new entries

## Dataset Structure

The generated CSV files contain the following fields:

| Field | Description |
|-------|-------------|
| name | Repository name |
| description | Repository description |
| html_url | URL to the repository |
| stars | Number of GitHub stars |
| forks | Number of GitHub forks |
| keywords | Comma-separated list of keywords |
| category | Primary category (e.g., framework, utility, client) |
| techstack | Comma-separated list of technologies used |
| emojis | Visual indicators for quick identification |

## Usage

### Automatic Daily Updates

The dataset is automatically updated daily via GitHub Actions. No manual intervention is required.

### Manual Trigger

You can manually trigger the workflow from the GitHub Actions tab:

1. Go to the "Actions" tab in the repository
2. Select "Unified MCP Servers Extraction"
3. Click "Run workflow"
4. Optionally customize:
   - Keywords for GitHub search
   - Minimum stars and forks thresholds
   - Which extraction methods to run

### Local Development

To run the scripts locally:

```bash
# Install dependencies
pip install -r requirements.txt

# Run README extraction
python extract_mcp_servers.py

# Run GitHub search
python daily.py
```

## Environment Variables

The following environment variables can be used to customize the behavior:

| Variable | Description | Default |
|----------|-------------|---------|
| GITHUB_TOKEN | GitHub API token for authentication | - |
| KEYWORDS_ENV | Comma-separated list of search keywords | MCP-related keywords |
| MIN_STARS | Minimum number of stars for repositories | 10 |
| MIN_FORKS | Minimum number of forks for repositories | 5 |

## Data Sources

### 1. Awesome MCP Servers Repository

The tool extracts data from the [awesome-mcp-servers](https://github.com/punkpeye/awesome-mcp-servers) repository, which contains a curated list of MCP servers organized by category.

### 2. GitHub Search

The tool searches GitHub for repositories matching MCP-related keywords, ensuring comprehensive coverage of the ecosystem.

## Categorization System

Repositories are categorized based on their content and purpose:

- **Framework**: Core MCP server implementations
- **Utility**: Helper tools and utilities
- **Client**: Client libraries and applications
- **Tutorial**: Learning resources and examples
- **Database**: Database integrations
- **API**: API implementations
- **Storage**: Storage solutions
- **AI**: AI and LLM integrations
- **Chat**: Chat and messaging features
- **Search**: Search functionality

## Tech Stack Detection

The tool identifies the following technologies:

- **Languages**: Python, TypeScript, Go, Rust, Java, C#
- **Frameworks**: FastAPI, Langchain, Spring
- **Protocols**: SSE, WebSocket, HTTP
- **Deployment**: Cloud, Local, Docker
- **Platforms**: iOS, Windows, Linux

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.



