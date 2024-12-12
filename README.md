# GitHub Newsletter Generator

A Python tool that automatically generates a newsletter summarizing the most important changes and improvements from Meilisearch's GitHub releases. The tool focuses on developer-relevant changes from the core search engine and SDKs.

## Features

- Fetches releases from Meilisearch's most active repositories
- Filters releases to focus on major and minor versions of the core engine
- Uses Claude AI to analyze release notes and identify key improvements
- Generates a well-formatted newsletter in Markdown
- Focuses on changes that matter to developers using Meilisearch

## Prerequisites

- Python 3.8+
- An Anthropic API key (for Claude)
- A GitHub personal access token with `repo` scope

## Installation

1. Clone the repository:

```bash
git clone https://github.com/meilisearch/github-newsletter-generator.git
cd github-newsletter-generator
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set up environment variables:

```bash
export ANTHROPIC_API_KEY=<your-anthropic-api-key>
export GITHUB_TOKEN=<your-github-token>
```

4. Run the script:

```bash
python github_newsletter_generator.py
```

The generated newsletter will be saved as `meilisearch_newsletter_2024.md`.

## How it Works

1. **Repository Selection**: 
   - Fetches Meilisearch's most active repositories
   - Focuses on the core engine and official SDKs

2. **Release Collection**:
   - Gathers releases from 2024
   - For meilisearch/meilisearch: only includes major and minor releases
   - For SDKs: includes all releases

3. **Analysis**:
   - Uses Claude AI to analyze release notes
   - Identifies important changes for developers
   - Focuses on technical improvements and features

4. **Newsletter Generation**:
   - Creates a structured Markdown document
   - Includes technical details and code examples
   - Highlights breaking changes and migration steps

## Output

The generated newsletter includes:
- Technical subject line
- Preview text highlighting key improvements
- Structured sections with features and changes
- Code examples where relevant
- Summary of analyzed repositories and releases

## Environment Variables

| Variable | Description |
|----------|-------------|
| `ANTHROPIC_API_KEY` | Your Anthropic API key for Claude |
| `GITHUB_TOKEN` | GitHub personal access token with repo access |

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.