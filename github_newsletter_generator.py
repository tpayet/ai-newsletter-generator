import os
from datetime import datetime
import requests
from anthropic import Anthropic
from typing import List, Dict
import json
from dotenv import load_dotenv

class NewsletterGenerator:
    def __init__(self):
        env_path = os.path.join(os.path.dirname(__file__), '.env')
        print(f"Loading .env from: {env_path}")
        load_dotenv(env_path)
        
        # Load Anthropic key
        self.anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        print(f"Raw API key from env: {self.anthropic_key}")
        if not self.anthropic_key or self.anthropic_key.startswith('your_') or not self.anthropic_key.startswith('sk-ant-'):
            raise ValueError("Please set a valid ANTHROPIC_API_KEY in your .env file")
        print(f"API key prefix: {self.anthropic_key[:15]}...")
        
        # Load GitHub token
        self.github_token = os.getenv('GITHUB_TOKEN')
        if not self.github_token:
            raise ValueError("Please set a valid GITHUB_TOKEN in your .env file")
        
        self.github_headers = {
            'Authorization': f'token {self.github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        self.anthropic_client = Anthropic(api_key=self.anthropic_key)
        
    def get_active_repositories(self, org: str, limit: int = 5) -> List[Dict]:
        """Fetch the most active repositories for an organization"""
        url = f'https://api.github.com/orgs/{org}/repos'
        repos = []
        
        try:
            response = requests.get(url, headers=self.github_headers)
            response.raise_for_status()
            
            all_repos = response.json()
            
            # First, try to get meilisearch-cloud directly
            cloud_repo_url = f'https://api.github.com/repos/{org}/meilisearch-cloud'
            try:
                cloud_response = requests.get(cloud_repo_url, headers=self.github_headers)
                cloud_response.raise_for_status()
                cloud_repo = cloud_response.json()
                repos.append(cloud_repo)
                print(f"Added meilisearch-cloud repository")
            except requests.exceptions.RequestException as e:
                print(f"Warning: Could not fetch meilisearch-cloud: {e}")
            
            # Sort remaining repositories by activity
            sorted_repos = sorted(
                all_repos,
                key=lambda x: x['stargazers_count'] + x['forks_count'] + x['watchers_count'],
                reverse=True
            )
            
            # Add other repositories up to the limit
            for repo in sorted_repos:
                if repo['name'] != 'meilisearch-cloud':  # Skip if already added
                    repos.append(repo)
                    if len(repos) >= limit:
                        break
            
            return repos
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching repositories: {e}")
            return []

    def get_releases(self, repo_full_name: str, year: int = 2024) -> List[Dict]:
        """Fetch all releases for a repository in the specified year"""
        url = f'https://api.github.com/repos/{repo_full_name}/releases'
        releases = []
        
        try:
            response = requests.get(url, headers=self.github_headers)
            response.raise_for_status()
            
            all_releases = response.json()
            
            for release in all_releases:
                if not release.get('published_at'):
                    continue
                    
                published_date = datetime.strptime(release['published_at'], '%Y-%m-%dT%H:%M:%SZ')
                if published_date.year != year:
                    continue
                    
                # For meilisearch/meilisearch, only include major and minor releases
                if repo_full_name == 'meilisearch/meilisearch':
                    tag = release['tag_name'].lstrip('v')
                    # Skip if it's a patch release (e.g., v1.2.3 -> skip, v1.2.0 -> include)
                    if tag.count('.') == 2 and not tag.endswith('.0'):
                        continue
                
                releases.append(release)
            
            return releases
                
        except requests.exceptions.RequestException as e:
            print(f"Error fetching releases for {repo_full_name}: {e}")
            return []

    def analyze_releases(self, releases: List[Dict]) -> str:
        """Use Claude to analyze releases and identify important changes"""
        simplified_releases = []
        for release in releases:
            simplified_release = {
                'name': release.get('name', ''),
                'tag_name': release.get('tag_name', ''),
                'published_at': release.get('published_at', ''),
                'body': release.get('body', '')[:2000],  # Limit release notes to 2000 characters
                'repository': release['url'].split('/repos/')[1].split('/releases')[0]
            }
            simplified_releases.append(simplified_release)
        
        # Take only the 10 most recent releases if there are more
        if len(simplified_releases) > 10:
            simplified_releases = simplified_releases[:10]
        
        releases_content = json.dumps(simplified_releases, indent=2)
        
        prompt = f"""You are a Product Marketing expert for Meilisearch.
        
        Context about Meilisearch:
        - Meilisearch is an open-source search engine (meilisearch/meilisearch repository)
        - The core product is used by developers to add search functionality to their applications
        - Focus on changes that affect developers using Meilisearch in their projects
        - Internal cloud platform changes (from meilisearch-cloud repository) should be ignored
        
        Please analyze these releases and identify the most significant improvements or changes 
        that would be valuable to highlight to developers using Meilisearch. Focus on:
        - New features in the core search engine
        - Performance improvements
        - API changes or additions
        - SDK updates that make integration easier
        - Breaking changes that developers need to know about
        
        Ignore:
        - Internal cloud platform changes
        - Administrative or operational updates
        - Changes that don't affect the developer experience
        
        Here are the releases to analyze:
        {releases_content}
        
        Please provide your analysis in a structured format with:
        1. A brief summary of each important change
        2. Why it matters to developers
        3. Order them by importance from a developer's perspective
        """
        
        try:
            response = self.anthropic_client.beta.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1000,
                temperature=0,
                system="You are a Product Marketing expert for Meilisearch, focused on communicating the value of our open-source search engine to developers.",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            print(f"Analysis response type: {type(response.content)}")
            return response.content.text if hasattr(response.content, 'text') else str(response.content)
            
        except Exception as e:
            print(f"Error analyzing releases with Claude: {e}")
            return ""

    def generate_newsletter(self, analysis: str) -> str:
        """Generate the final newsletter content using Claude"""
        prompt = f"""Based on this analysis of Meilisearch's 2024 releases, 
        please write an engaging newsletter for developers using Meilisearch in their projects.
        
        The newsletter should:
        1. Have an attention-grabbing introduction focused on developer benefits
        2. Highlight the most important improvements to the core search engine
        3. Include relevant technical details that developers need to know
        4. Explain any breaking changes and migration steps
        5. End with a call to action (e.g., try new features, upgrade version)

        Focus on:
        - Changes that affect developers using Meilisearch
        - Technical improvements and new capabilities
        - SDK updates and API changes
        
        Avoid mentioning:
        - Internal cloud platform changes
        - Administrative or operational updates
        - Changes that don't affect developers

        Format the response in Markdown with:
        - A clear technical subject line
        - Preview text highlighting key improvements
        - Proper headers (##) for each section
        - Code examples where relevant
        - Bullet points for features
        - Bold and italic text for emphasis
        
        Analysis:
        {analysis}
        """
        
        try:
            response = self.anthropic_client.beta.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1500,
                temperature=0.7,
                system="You are a Product Marketing expert for Meilisearch, skilled at communicating technical improvements to developers using our open-source search engine.",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            print(f"Newsletter response type: {type(response.content)}")
            return response.content.text if hasattr(response.content, 'text') else str(response.content)
            
        except Exception as e:
            print(f"Error generating newsletter with Claude: {e}")
            return ""

def main():
    print("\n=== Starting Newsletter Generation Process ===\n")
    generator = NewsletterGenerator()
    
    # Get most active repositories
    print("1. Fetching active Meilisearch repositories...")
    repos = generator.get_active_repositories('meilisearch')
    print(f"\nRepositories to analyze ({len(repos)}):")
    print("\nPriority repositories:")
    for repo in repos:
        if repo['name'] == 'meilisearch-cloud':
            print(f"- {repo['full_name']} (Cloud platform repository)")
        elif repo['name'] == 'meilisearch':
            print(f"- {repo['full_name']} (Core engine - major/minor releases only)")
        else:
            print(f"- {repo['full_name']} (Stars: {repo['stargazers_count']}, Forks: {repo['forks_count']})")
    
    # Collect all releases from 2024
    print("\n2. Collecting 2024 releases...")
    all_releases = []
    for repo in repos:
        releases = generator.get_releases(repo['full_name'])
        if releases:
            print(f"\nReleases from {repo['full_name']}:")
            for release in releases:
                published_date = datetime.strptime(release['published_at'], '%Y-%m-%dT%H:%M:%SZ')
                print(f"- {release['tag_name']} (Published: {published_date.strftime('%Y-%m-%d')})")
            all_releases.extend(releases)
        else:
            print(f"\nNo 2024 releases found for {repo['full_name']}")
    
    print(f"\nTotal releases collected: {len(all_releases)}")
    print("\nSummary by repository:")
    repo_counts = {}
    for release in all_releases:
        repo_name = release['url'].split('/repos/')[1].split('/releases')[0]
        repo_counts[repo_name] = repo_counts.get(repo_name, 0) + 1
    for repo, count in repo_counts.items():
        print(f"- {repo}: {count} releases")
    
    # Analyze releases
    print("\n3. Analyzing releases with Claude...")
    analysis = generator.analyze_releases(all_releases)
    print("\n4. Analysis completed")
    
    # Generate newsletter
    print("\n5. Generating newsletter content...")
    newsletter = generator.generate_newsletter(analysis)
    print("\n6. Newsletter generation completed")
    
    # Save the newsletter to a markdown file
    output_file = 'meilisearch_newsletter_2024.md'
    print(f"\n7. Saving newsletter to {output_file}")
    with open(output_file, 'w') as f:
        f.write(newsletter)
    print("\n=== Newsletter Generation Process Completed ===")

if __name__ == "__main__":
    main() 